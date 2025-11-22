import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from apps.accounts.interfaces.credit_card_bill_handler import BaseCreditCardBillHandler
from apps.accounts.models import Transaction


class JSONCreditCardHandler(BaseCreditCardBillHandler):
    """Handler for parsing credit card transactions from JSON files."""

    def parse_transactions_from_file(self, filename: str) -> list[Transaction]:
        """Parse transactions from JSON billing file.

        Args:
            filename: Path to the JSON file containing transaction data.

        Returns:
            List of Transaction objects parsed from the JSON file.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            json.JSONDecodeError: If the JSON file is malformed.
            ValueError: If required fields are missing or invalid.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{filename}' not found.")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON format in file '{filename}': {e}", e.doc, e.pos
            )

        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of transactions.")

        transactions = []

        for item in data:
            try:
                transaction = self._parse_transaction_item(item)
                if transaction:
                    transactions.append(transaction)
            except ValueError as e:
                # Log the error but continue processing other transactions
                print(f"Warning: Skipping invalid transaction: {e}")
                continue

        return transactions

    def _parse_transaction_item(self, item: dict[str, Any]) -> Transaction | None:
        """Parse a single transaction item from the JSON data.

        Args:
            item: Dictionary containing transaction data.

        Returns:
            Transaction object or None if the transaction should be skipped.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Validate required fields
        required_fields = ["name", "date", "total"]
        for field in required_fields:
            if field not in item:
                raise ValueError(f"Missing required field: {field}")

        # Parse date
        try:
            transaction_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                f"Invalid date format: {item['date']}. Expected format: YYYY-MM-DD"
            )

        # Parse amount
        try:
            amount = Decimal(str(item["total"]))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount: {item['total']}")

        if amount < 0:
            transaction_type = Transaction.TransactionType.INCOME
            amount = abs(amount)
        else:
            transaction_type = Transaction.TransactionType.EXPENSE

        current_installment = item.get("current_installment", 1)
        total_installments = item.get("total_installments", 1)

        if not isinstance(current_installment, int) or current_installment < 1:
            raise ValueError(f"Invalid current_installment: {current_installment}")
        if not isinstance(total_installments, int) or total_installments < 1:
            raise ValueError(f"Invalid total_installments: {total_installments}")
        if current_installment > total_installments:
            raise ValueError(
                f"current_installment ({current_installment}) cannot be greater than "
                f"total_installments ({total_installments})"
            )

        transaction = Transaction(
            transaction_type=transaction_type,
            amount=amount,
            description=item["name"],
            occurred_at=transaction_date,
            charge_at_card=transaction_date,
            installments_total=total_installments,
            installment_number=current_installment,
        )

        return transaction
