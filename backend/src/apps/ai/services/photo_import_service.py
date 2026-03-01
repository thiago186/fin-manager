"""Service for extracting transactions from photos using a vision-capable LLM."""

import base64
import json
import mimetypes
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import structlog
from django.conf import settings
from django.contrib.auth.models import User
from jinja2 import Environment, FileSystemLoader
from openrouter import OpenRouter

from apps.accounts.models.transaction import Transaction
from apps.accounts.services.file_storage_service import get_file_storage_service

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class PhotoImportService:
    """Extracts transaction data from photos via a vision-capable LLM."""

    def __init__(self, user: User) -> None:
        self.user = user
        self.storage_service = get_file_storage_service()

        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must be set in settings")

        self.api_key = api_key
        self.model = getattr(settings, "OPENROUTER_VISION_MODEL", "openai/gpt-5-mini")

    def extract_transactions(
        self,
        photo_paths: list[str],
        positive_as_expense: bool = True,
    ) -> list[Transaction]:
        """Extract transactions from stored photo files.

        Args:
            photo_paths: List of storage paths returned by FileStorageService.
            positive_as_expense: If True, positive amounts are expenses; if False, income.

        Returns:
            List of unsaved Transaction objects ready for TransactionProcessor.
        """
        image_contents = self._load_images(photo_paths)
        prompt = self._build_prompt(positive_as_expense=positive_as_expense)
        llm_response = self._call_vision_llm(image_contents, prompt)
        transactions = self._parse_response(llm_response)
        return transactions

    def _load_images(self, photo_paths: list[str]) -> list[dict]:
        """Load and base64-encode images from storage.

        Returns:
            List of dicts with 'mime_type' and 'base64_data' keys.
        """
        images = []
        for storage_path in photo_paths:
            file_path = self.storage_service.get_file_path(storage_path)
            abs_path = Path(file_path)

            if not abs_path.exists():
                logger.warning("Photo file not found", path=file_path)
                continue

            mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
            with open(abs_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")

            images.append({"mime_type": mime_type, "base64_data": data})
            logger.info(
                "Loaded image for LLM",
                path=storage_path,
                mime_type=mime_type,
                size_kb=len(data) * 3 // 4 // 1024,
            )

        return images

    def _build_prompt(self, positive_as_expense: bool = True) -> str:
        """Render the extraction prompt from the Jinja2 template."""
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template("photo_transaction_extraction_prompt.jinja2")
        logger.info(
            "Building prompt",
            positive_as_expense=positive_as_expense,
        )
        return template.render(positive_as_expense=positive_as_expense)

    def _call_vision_llm(self, images: list[dict], system_prompt: str) -> str:
        """Send images to the vision LLM and get the response.

        Args:
            images: List of base64-encoded image dicts.
            system_prompt: The system prompt for extraction.

        Returns:
            Raw string response from the LLM.
        """
        # Build multimodal user message content
        user_content: list[dict] = []
        for img in images:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img['mime_type']};base64,{img['base64_data']}"
                    },
                }
            )

        user_content.append(
            {
                "type": "text",
                "text": "Extract all transactions from the images above.",
            }
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        logger.info(
            "Calling vision LLM",
            model=self.model,
            image_count=len(images),
        )

        with OpenRouter(api_key=self.api_key) as client:
            response = client.chat.send(
                model=self.model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout_ms=60 * 1000,
            )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from vision LLM")

        result = str(content)
        logger.info(
            "Vision LLM response received",
            model=self.model,
            response_length=len(result),
        )
        return result

    def _parse_response(self, llm_response: str) -> list[Transaction]:
        """Parse the LLM JSON response into Transaction objects.

        Args:
            llm_response: Raw JSON string from the LLM.

        Returns:
            List of unsaved Transaction objects.
        """
        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON", error=str(e))
            raise ValueError(f"LLM returned invalid JSON: {e}")

        raw_transactions = data.get("transactions", [])
        if not raw_transactions:
            logger.warning("LLM returned no transactions")
            return []

        transactions = []
        for i, raw in enumerate(raw_transactions):
            try:
                transaction = self._build_transaction(raw, i)
                transactions.append(transaction)
            except Exception as e:
                logger.warning(
                    "Failed to parse transaction from LLM response",
                    index=i,
                    raw=raw,
                    error=str(e),
                )
                continue

        logger.info(
            "Parsed transactions from LLM response",
            total_raw=len(raw_transactions),
            parsed=len(transactions),
        )
        return transactions

    def _build_transaction(self, raw: dict, index: int) -> Transaction:
        """Build a single Transaction object from raw LLM data."""
        # Parse date
        date_str = raw.get("date", "")
        try:
            occurred_at = date.fromisoformat(date_str)
        except (ValueError, TypeError):
            raise ValueError(f"Transaction {index}: invalid date '{date_str}'")

        # Parse amount
        try:
            amount = Decimal(str(raw.get("amount", 0)))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (InvalidOperation, TypeError):
            raise ValueError(
                f"Transaction {index}: invalid amount '{raw.get('amount')}'"
            )

        # Parse transaction type
        transaction_type = raw.get("transaction_type", "").upper()
        valid_types = {
            Transaction.TransactionType.INCOME,
            Transaction.TransactionType.EXPENSE,
        }
        if transaction_type not in valid_types:
            raise ValueError(
                f"Transaction {index}: invalid type '{transaction_type}'"
            )

        description = str(raw.get("description", "")).strip()
        if not description:
            description = f"Photo import transaction #{index + 1}"

        return Transaction(
            user=self.user,
            amount=amount,
            description=description,
            occurred_at=occurred_at,
            transaction_type=transaction_type,
        )
