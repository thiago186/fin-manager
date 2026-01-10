"""Service for AI-powered transaction classification."""

import json
from pathlib import Path
from typing import Any

import structlog
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from jinja2 import Environment, FileSystemLoader

from apps.accounts.models.categories import Category
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction
from apps.ai.interfaces.ai_classifier import AIClassifierInterface
from apps.ai.models import AIClassifierInstruction
from apps.ai.services.openrouter_classifier import OpenRouterClassifier

logger = structlog.get_logger(__name__)


class AIClassificationService:
    """Service for classifying transactions using AI."""

    def __init__(
        self, user: User, classifier: AIClassifierInterface | None = None
    ) -> None:
        """Initialize the AI classification service.

        Args:
            user: The user whose transactions will be classified
            classifier: Optional AI classifier instance. If not provided, uses OpenRouterClassifier
        """
        self.user = user
        self.classifier = classifier or OpenRouterClassifier()

        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
        )

    def classify_transactions(
        self, transaction_type: str | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """Classify uncategorized transactions for the user.

        Args:
            transaction_type: Optional filter by transaction type (INCOME, EXPENSE, TRANSFER).
                If None, classifies expenses first, then incomes separately.
            limit: Maximum number of transactions to classify in one batch per transaction type

        Returns:
            Dictionary with classification summary:
            {
                "classified_count": int,
                "failed_count": int,
                "total_processed": int,
                "errors": list[str]
            }
        """
        logger.info(
            "Starting transaction classification",
            user_id=self.user.id,
            transaction_type=transaction_type,
            limit=limit,
        )

        # If transaction_type is provided, classify only that type
        if transaction_type:
            return self._classify_transactions_by_type(transaction_type, limit)

        # If no transaction_type provided, classify expenses first, then incomes
        expense_result = self._classify_transactions_by_type("EXPENSE", limit)
        income_result = self._classify_transactions_by_type("INCOME", limit)

        # Aggregate results
        return {
            "classified_count": expense_result["classified_count"]
            + income_result["classified_count"],
            "failed_count": expense_result["failed_count"]
            + income_result["failed_count"],
            "total_processed": expense_result["total_processed"]
            + income_result["total_processed"],
            "errors": expense_result["errors"] + income_result["errors"],
        }

    def _classify_transactions_by_type(
        self, transaction_type: str, limit: int
    ) -> dict[str, Any]:
        """Classify uncategorized transactions for a specific transaction type.

        Args:
            transaction_type: Transaction type to classify (INCOME, EXPENSE, TRANSFER)
            limit: Maximum number of transactions to classify in one batch

        Returns:
            Dictionary with classification summary
        """
        # Get user instructions
        user_instructions = self._get_user_instructions()

        # Get uncategorized transactions
        uncategorized_transactions = self._get_uncategorized_transactions(
            transaction_type, limit
        )

        if not uncategorized_transactions:
            logger.info(
                "No uncategorized transactions found",
                user_id=self.user.id,
                transaction_type=transaction_type,
            )
            return {
                "classified_count": 0,
                "failed_count": 0,
                "total_processed": 0,
                "errors": [],
            }

        # Get categorized examples
        examples = self._get_categorized_examples(transaction_type)

        # Get categories and subcategories
        categories = self._get_categories(transaction_type)

        # Build prompt
        user_prompt = self._build_prompt(
            user_instructions, categories, examples, uncategorized_transactions
        )

        # Build messages with system and user prompts
        messages = [
            {
                "role": "system",
                "content": "You are a financial transaction classifier. Always respond with valid JSON only.",
            },
            {"role": "user", "content": user_prompt},
        ]

        # Call AI classifier
        try:
            ai_response = self.classifier.classify(messages)
            logger.debug(
                "AI response",
                ai_response=ai_response,
                transactions_count=len(uncategorized_transactions),
                transaction_type=transaction_type,
            )
            logger.debug(f"Prompt: \n{user_prompt}")
            classifications = self._parse_ai_response(ai_response)
        except Exception as e:
            logger.exception(
                "AI classification failed",
                user_id=self.user.id,
                transaction_type=transaction_type,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "classified_count": 0,
                "failed_count": len(uncategorized_transactions),
                "total_processed": len(uncategorized_transactions),
                "errors": [
                    f"AI classification failed for {transaction_type}: {str(e)}"
                ],
            }

        return self._update_transactions(classifications, uncategorized_transactions)

    def classify_specific_transactions(
        self, transactions: list[Transaction]
    ) -> dict[str, Any]:
        """Classify a specific list of transactions.

        Args:
            transactions: List of Transaction instances to classify

        Returns:
            Dictionary with classification summary:
            {
                "classified_count": int,
                "failed_count": int,
                "total_processed": int,
                "errors": list[str]
            }
        """
        if not transactions:
            return {
                "classified_count": 0,
                "failed_count": 0,
                "total_processed": 0,
                "errors": [],
            }

        # Filter to only transactions belonging to this user
        user_transactions = [t for t in transactions if t.user_id == self.user.id]
        if not user_transactions:
            return {
                "classified_count": 0,
                "failed_count": 0,
                "total_processed": 0,
                "errors": ["No transactions belong to this user"],
            }

        logger.info(
            "Starting classification for specific transactions",
            user_id=self.user.id,
            transaction_count=len(user_transactions),
        )

        # Get user instructions
        user_instructions = self._get_user_instructions()

        # Determine transaction type from transactions (use first one if mixed)
        transaction_type = (
            user_transactions[0].transaction_type if user_transactions else None
        )

        # Get categorized examples
        examples = self._get_categorized_examples(transaction_type)

        # Get categories and subcategories
        categories = self._get_categories(transaction_type)

        # Build prompt
        user_prompt = self._build_prompt(
            user_instructions, categories, examples, user_transactions
        )

        # Build messages with system and user prompts
        messages = [
            {
                "role": "system",
                "content": "You are a financial transaction classifier. Always respond with valid JSON only.",
            },
            {"role": "user", "content": user_prompt},
        ]

        # Call AI classifier
        try:
            ai_response = self.classifier.classify(messages)
            classifications = self._parse_ai_response(ai_response)
        except Exception as e:
            logger.exception(
                "AI classification failed",
                user_id=self.user.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "classified_count": 0,
                "failed_count": len(user_transactions),
                "total_processed": len(user_transactions),
                "errors": [f"AI classification failed: {str(e)}"],
            }

        # Update transactions
        return self._update_transactions(classifications, user_transactions)

    def _get_user_instructions(self) -> str:
        """Get user-specific classification instructions.

        Returns:
            User instructions as a string, or default instructions if none exist
        """
        instruction = AIClassifierInstruction.objects.filter(user=self.user).first()
        if instruction:
            return instruction.instructions

        return (
            "Classify transactions based on their description and amount. "
            "Use your best judgment to match transactions to the most appropriate subcategory. "
            "Consider common patterns and context when classifying."
        )

    def _get_uncategorized_transactions(
        self, transaction_type: str | None, limit: int
    ) -> list[Transaction]:
        """Get uncategorized transactions for the user.

        Args:
            transaction_type: Optional filter by transaction type
            limit: Maximum number of transactions to return

        Returns:
            List of uncategorized transactions
        """
        queryset = Transaction.objects.filter(
            user=self.user, subcategory__isnull=True
        ).select_related("account", "credit_card")

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        return list(queryset[:limit])

    def _get_categorized_examples(
        self, transaction_type: str | None, limit: int = 10
    ) -> list[Transaction]:
        """Get categorized transaction examples for the user.

        Args:
            transaction_type: Optional filter by transaction type
            limit: Maximum number of examples to return

        Returns:
            List of categorized transactions to use as examples
        """
        queryset = (
            Transaction.objects.filter(user=self.user, subcategory__isnull=False)
            .select_related("subcategory", "subcategory__category")
            .order_by("-occurred_at")
        )

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        return list(queryset[:limit])

    def _get_categories(self, transaction_type: str | None) -> list[Category]:
        """Get categories and subcategories for the user.

        Args:
            transaction_type: Optional filter by transaction type

        Returns:
            List of categories with their subcategories
        """
        queryset = Category.objects.filter(
            user=self.user, is_active=True
        ).prefetch_related("subcategories")

        if transaction_type:
            # Map Transaction.TransactionType to Category.TransactionType
            category_type_map = {
                "INCOME": "income",
                "EXPENSE": "expense",
                "TRANSFER": "expense",
            }
            mapped_type = category_type_map.get(transaction_type)
            if mapped_type:
                queryset = queryset.filter(transaction_type=mapped_type)

        return list(queryset)

    def _build_prompt(
        self,
        user_instructions: str,
        categories: list[Category],
        examples: list[Transaction],
        transactions: list[Transaction],
    ) -> str:
        """Build the classification prompt using Jinja2 template.

        Args:
            user_instructions: User-specific classification instructions
            categories: List of categories with subcategories
            examples: List of example transactions
            transactions: List of transactions to classify

        Returns:
            Rendered prompt string
        """
        template = self.jinja_env.get_template(
            "transaction_classification_prompt.jinja2"
        )

        # Filter categories to only include those with active subcategories
        categories_with_subcategories = [
            cat
            for cat in categories
            if cat.subcategories.filter(is_active=True).exists()
        ]

        return template.render(
            user_instructions=user_instructions,
            categories=categories_with_subcategories,
            examples=examples,
            transactions=transactions,
        )

    def _parse_ai_response(self, response: str) -> list[dict[str, Any]]:
        """Parse the AI response JSON into classification data.

        Args:
            response: JSON string response from AI

        Returns:
            List of classification dictionaries with transaction_id and subcategory_id

        Raises:
            ValueError: If response cannot be parsed or is invalid
        """
        try:
            data = json.loads(response)
            if "classifications" not in data:
                raise ValueError("Response missing 'classifications' key")

            classifications = data["classifications"]
            if not isinstance(classifications, list):
                raise ValueError("'classifications' must be a list")

            return classifications

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}") from e

    def _update_transactions(
        self,
        classifications: list[dict[str, Any]],
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        """Update transactions with AI classifications.

        Args:
            classifications: List of classification dictionaries
            transactions: List of transactions that were sent for classification

        Returns:
            Dictionary with update summary
        """
        transaction_map = {t.id: t for t in transactions}
        classified_count = 0
        failed_count = 0
        errors: list[str] = []

        with db_transaction.atomic():
            for classification in classifications:
                transaction_id = classification.get("transaction_id")
                subcategory_id = classification.get("subcategory_id")

                if not transaction_id or not subcategory_id:
                    failed_count += 1
                    errors.append(
                        "Invalid classification: missing transaction_id or subcategory_id"
                    )
                    continue

                transaction = transaction_map.get(transaction_id)
                if not transaction:
                    failed_count += 1
                    errors.append(f"Transaction {transaction_id} not found in batch")
                    continue

                try:
                    subcategory = Subcategory.objects.get(
                        id=subcategory_id,
                        user=self.user,
                        is_active=True,
                    )

                    # Validate subcategory matches transaction type
                    if transaction.transaction_type == "INCOME":
                        if subcategory.transaction_type != "income":
                            raise ValueError(
                                f"Subcategory {subcategory_id} is not for income transactions"
                            )
                    elif transaction.transaction_type == "EXPENSE":
                        if subcategory.transaction_type != "expense":
                            raise ValueError(
                                f"Subcategory {subcategory_id} is not for expense transactions"
                            )

                    transaction.subcategory = subcategory
                    transaction.category = subcategory.category
                    transaction.need_review = True
                    transaction.save()

                    classified_count += 1

                except Subcategory.DoesNotExist:
                    failed_count += 1
                    errors.append(
                        f"Subcategory {subcategory_id} not found or not active for user"
                    )
                except ValueError as e:
                    failed_count += 1
                    errors.append(str(e))
                except Exception as e:
                    failed_count += 1
                    errors.append(
                        f"Error updating transaction {transaction_id}: {str(e)}"
                    )

        logger.info(
            "Transaction classification completed",
            user_id=self.user.id,
            classified_count=classified_count,
            failed_count=failed_count,
            total_processed=len(transactions),
        )

        return {
            "classified_count": classified_count,
            "failed_count": failed_count,
            "total_processed": len(transactions),
            "errors": errors[:10],  # Limit errors to first 10
        }
