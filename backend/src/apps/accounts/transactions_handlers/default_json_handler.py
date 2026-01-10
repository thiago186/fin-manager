import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import User

from apps.accounts.interfaces.json_handler import BaseJsonHandler
from apps.accounts.models.transaction import Transaction


class DefaultJsonHandler(BaseJsonHandler):
    """Handler for parsing transactions from standard JSON files."""

    # Date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
    ]

    def can_handle_file(self, json_file_path: str) -> bool:
        """Check if this handler can handle the JSON file.

        Reads the file and checks if it contains a valid JSON array with
        at least one transaction object that has required fields (name, date, total).
        This is the fallback handler, so it should return True if it can read
        the file and find the required structure.

        Args:
            json_file_path: Path to the JSON file to check.

        Returns:
            True if this handler can handle the JSON format, False otherwise.
            Returns False if the file cannot be read or doesn't have required structure.
        """
        try:
            with open(json_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                return False

            if len(data) == 0:
                return False

            # Check if first item has required fields
            first_item = data[0]
            if not isinstance(first_item, dict):
                return False

            required_fields = ["name", "date", "total"]
            has_required_fields = all(field in first_item for field in required_fields)

            return has_required_fields
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            return False
        except Exception:
            return False

    def parse_transactions_from_file(
        self, filename: str, user: User
    ) -> list[Transaction]:
        """Parse transactions from JSON file.

        Args:
            filename: Path to the JSON file containing transaction data.
            user: The user who owns these transactions.

        Returns:
            List of Transaction objects parsed from the JSON file.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            ValueError: If required fields are missing or invalid.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{filename}' not found.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file '{filename}': {e}")

        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of transactions.")

        transactions = []

        for idx, item in enumerate(data, start=1):
            try:
                transaction = self._parse_transaction_item(item, user, idx)
                if transaction:
                    transactions.append(transaction)
            except ValueError as e:
                print(f"Warning: Skipping transaction {idx}: {e}")
                continue

        return transactions

    def _parse_transaction_item(
        self, item: dict[str, Any], user: User, item_num: int
    ) -> Transaction | None:
        """Parse a single transaction item from the JSON data.

        Args:
            item: Dictionary containing transaction data.
            user: The user who owns this transaction.
            item_num: Item number for error reporting.

        Returns:
            Transaction object or None if the transaction should be skipped.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Validate required fields
        required_fields = ["name", "date", "total"]
        for field in required_fields:
            if field not in item:
                raise ValueError(
                    f"Transaction {item_num}: Missing required field: {field}"
                )

        # Parse date
        date_value = str(item["date"]).strip()
        occurred_at = self._parse_date(date_value, item_num)
        if not occurred_at:
            raise ValueError(
                f"Transaction {item_num}: Invalid date format: {date_value}. "
                f"Expected format: YYYY-MM-DD"
            )

        # Parse amount
        try:
            amount = Decimal(str(item["total"]))
        except (ValueError, TypeError):
            raise ValueError(f"Transaction {item_num}: Invalid amount: {item['total']}")

        # Determine transaction type from amount sign
        if amount < 0:
            transaction_type = Transaction.TransactionType.INCOME
            amount = abs(amount)
        else:
            transaction_type = Transaction.TransactionType.EXPENSE

        # Parse installments
        installments_total = item.get("total_installments", 1)
        installment_number = item.get("current_installment", 1)

        if not isinstance(installments_total, int) or installments_total < 1:
            installments_total = 1
        if not isinstance(installment_number, int) or installment_number < 1:
            installment_number = 1
        if installment_number > installments_total:
            raise ValueError(
                f"Transaction {item_num}: current_installment ({installment_number}) "
                f"cannot be greater than total_installments ({installments_total})"
            )

        # Get description
        description = str(item["name"]).strip() or ""

        # Create transaction object (without saving)
        transaction = Transaction(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            occurred_at=occurred_at,
            installments_total=installments_total,
            installment_number=installment_number,
        )

        # Store optional identifiers for later matching (will be set by service)
        transaction._json_account_identifier = (
            item.get("account") or item.get("account_id") or item.get("account_name")
        )  # type: ignore
        transaction._json_credit_card_identifier = (
            item.get("credit_card")
            or item.get("credit_card_id")
            or item.get("credit_card_name")
        )  # type: ignore
        transaction._json_category_name = item.get("category") or item.get(
            "category_name"
        )  # type: ignore
        transaction._json_subcategory_name = item.get("subcategory") or item.get(
            "subcategory_name"
        )  # type: ignore
        tags_value = item.get("tags") or item.get("tag")
        transaction._json_tags_value = tags_value if tags_value else None  # type: ignore

        return transaction

    def _parse_date(self, date_str: str, item_num: int) -> Any | None:
        """Parse date string using multiple format attempts.

        Args:
            date_str: Date string to parse.
            item_num: Item number for error reporting.

        Returns:
            Date object if successful, None otherwise.
        """
        date_str = date_str.strip()
        for date_format in self.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, date_format).date()
            except ValueError:
                continue
        return None
