import csv
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import User

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.models.transaction import Transaction


class DefaultCSVHandler(BaseCSVHandler):
    """Handler for parsing transactions from standard CSV files."""

    # Column mapping: CSV column names -> Transaction field names
    DATE_COLUMNS = ["date", "occurred_at", "transaction_date", "occurred_date"]
    AMOUNT_COLUMNS = ["amount", "value", "total"]
    DESCRIPTION_COLUMNS = ["description", "name", "memo", "note"]
    TRANSACTION_TYPE_COLUMNS = ["transaction_type", "type"]
    ACCOUNT_COLUMNS = ["account", "account_id", "account_name"]
    CREDIT_CARD_COLUMNS = ["credit_card", "credit_card_id", "credit_card_name"]
    CATEGORY_COLUMNS = ["category", "category_name"]
    SUBCATEGORY_COLUMNS = ["subcategory", "subcategory_name"]
    TAGS_COLUMNS = ["tags", "tag"]
    INSTALLMENTS_TOTAL_COLUMNS = ["installments_total", "total_installments"]
    INSTALLMENT_NUMBER_COLUMNS = ["installment_number", "current_installment"]

    # Date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
    ]

    def can_handle_file(self, csv_file_path: str) -> bool:
        """Check if this handler can handle the CSV file.

        Reads the file with standard CSV reading and checks if it contains at
        least one date column and one amount column (required fields). This is
        the fallback handler, so it should return True if it can read the file
        and find the required columns.

        Args:
            csv_file_path: Path to the CSV file to check.

        Returns:
            True if this handler can handle the CSV format, False otherwise.
            Returns False if the file cannot be read or doesn't have required columns.
        """
        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                # Get headers from the reader
                headers = reader.fieldnames

                if not headers:
                    return False

                # Normalize headers (case-insensitive, strip whitespace)
                normalized_headers = [h.strip().lower() if h else "" for h in headers]

                # Check for at least one date column and one amount column (required fields)
                has_date = any(col in normalized_headers for col in self.DATE_COLUMNS)
                has_amount = any(
                    col in normalized_headers for col in self.AMOUNT_COLUMNS
                )

                return has_date and has_amount
        except (FileNotFoundError, UnicodeDecodeError, csv.Error):
            return False
        except Exception:
            # Any other error means we can't handle this file
            return False

    def parse_transactions_from_file(
        self, filename: str, user: User
    ) -> list[Transaction]:
        """Parse transactions from CSV file.

        Args:
            filename: Path to the CSV file containing transaction data.
            user: The user who owns these transactions.

        Returns:
            List of Transaction objects parsed from the CSV file.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            ValueError: If required fields are missing or invalid.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                transactions = []

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 (header is row 1)
                    try:
                        transaction = self._parse_transaction_row(row, user, row_num)
                        if transaction:
                            transactions.append(transaction)
                    except ValueError as e:
                        # Log the error but continue processing other transactions
                        print(f"Warning: Skipping row {row_num}: {e}")
                        continue

                return transactions
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{filename}' not found.")
        except Exception as e:
            raise ValueError(f"Error reading CSV file '{filename}': {e}")

    def _parse_transaction_row(
        self, row: dict[str, str], user: User, row_num: int
    ) -> Transaction | None:
        """Parse a single transaction row from the CSV data.

        Args:
            row: Dictionary containing transaction data from CSV row.
            user: The user who owns this transaction.
            row_num: Row number for error reporting.

        Returns:
            Transaction object or None if the transaction should be skipped.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Normalize column names (case-insensitive, strip whitespace)
        normalized_row = {k.strip().lower(): v for k, v in row.items() if v}

        # Find and parse date
        date_value = self._find_column_value(normalized_row, self.DATE_COLUMNS)
        if not date_value:
            raise ValueError(f"Row {row_num}: Missing required field: date")

        occurred_at = self._parse_date(date_value, row_num)
        if not occurred_at:
            raise ValueError(f"Row {row_num}: Invalid date format: {date_value}")

        # Find and parse amount
        amount_value = self._find_column_value(normalized_row, self.AMOUNT_COLUMNS)
        if not amount_value:
            raise ValueError(f"Row {row_num}: Missing required field: amount")

        try:
            amount = Decimal(str(amount_value))
        except (ValueError, TypeError):
            raise ValueError(f"Row {row_num}: Invalid amount: {amount_value}")

        # Find transaction type
        transaction_type_value = self._find_column_value(
            normalized_row, self.TRANSACTION_TYPE_COLUMNS
        )
        if not transaction_type_value:
            # Infer from amount sign if not provided
            if amount < 0:
                transaction_type = Transaction.TransactionType.INCOME
                amount = abs(amount)
            else:
                transaction_type = Transaction.TransactionType.EXPENSE
        else:
            transaction_type = self._parse_transaction_type(
                transaction_type_value, row_num
            )

        # Find description
        description = (
            self._find_column_value(normalized_row, self.DESCRIPTION_COLUMNS) or ""
        )

        # Find optional fields
        account_identifier = self._find_column_value(
            normalized_row, self.ACCOUNT_COLUMNS
        )
        credit_card_identifier = self._find_column_value(
            normalized_row, self.CREDIT_CARD_COLUMNS
        )
        category_name = self._find_column_value(normalized_row, self.CATEGORY_COLUMNS)
        subcategory_name = self._find_column_value(
            normalized_row, self.SUBCATEGORY_COLUMNS
        )
        tags_value = self._find_column_value(normalized_row, self.TAGS_COLUMNS)
        installments_total_value = self._find_column_value(
            normalized_row, self.INSTALLMENTS_TOTAL_COLUMNS
        )
        installment_number_value = self._find_column_value(
            normalized_row, self.INSTALLMENT_NUMBER_COLUMNS
        )

        # Parse installments
        installments_total = 1
        installment_number = 1
        if installments_total_value:
            try:
                installments_total = int(installments_total_value)
                if installments_total < 1:
                    installments_total = 1
            except (ValueError, TypeError):
                pass

        if installment_number_value:
            try:
                installment_number = int(installment_number_value)
                if installment_number < 1:
                    installment_number = 1
            except (ValueError, TypeError):
                pass

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

        # Store identifiers for later matching (will be set by service)
        transaction._csv_account_identifier = account_identifier  # type: ignore
        transaction._csv_credit_card_identifier = credit_card_identifier  # type: ignore
        transaction._csv_category_name = category_name  # type: ignore
        transaction._csv_subcategory_name = subcategory_name  # type: ignore
        transaction._csv_tags_value = tags_value  # type: ignore

        return transaction

    def _find_column_value(
        self, row: dict[str, str], column_names: list[str]
    ) -> str | None:
        """Find a value in the row by checking multiple possible column names.

        Args:
            row: Normalized row dictionary (lowercase keys).
            column_names: List of possible column names to check.

        Returns:
            The value if found, None otherwise.
        """
        for col_name in column_names:
            if col_name.lower() in row:
                value = row[col_name.lower()].strip()
                if value:
                    return value
        return None

    def _parse_date(self, date_str: str, row_num: int) -> Any | None:
        """Parse date string using multiple format attempts.

        Args:
            date_str: Date string to parse.
            row_num: Row number for error reporting.

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

    def _parse_transaction_type(
        self, type_str: str, row_num: int
    ) -> Transaction.TransactionType:
        """Parse transaction type string.

        Args:
            type_str: Transaction type string.
            row_num: Row number for error reporting.

        Returns:
            Transaction type value.

        Raises:
            ValueError: If transaction type is invalid.
        """
        type_str = type_str.strip().upper()
        valid_types = {
            "INCOME": Transaction.TransactionType.INCOME,
            "EXPENSE": Transaction.TransactionType.EXPENSE,
            "TRANSFER": Transaction.TransactionType.TRANSFER,
        }

        if type_str in valid_types:
            return valid_types[type_str]

        # Try alternative names
        if type_str in ["I", "IN", "INCOME"]:
            return Transaction.TransactionType.INCOME
        if type_str in ["E", "EX", "EXPENSE", "EXP"]:
            return Transaction.TransactionType.EXPENSE
        if type_str in ["T", "TR", "TRANSFER", "TRANS"]:
            return Transaction.TransactionType.TRANSFER

        raise ValueError(f"Row {row_num}: Invalid transaction type: {type_str}")
