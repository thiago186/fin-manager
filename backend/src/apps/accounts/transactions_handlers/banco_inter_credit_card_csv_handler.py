from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from django.contrib.auth.models import User

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.models.transaction import Transaction


class BancoInterCreditCardCsvHandler(BaseCSVHandler):
    """Handler for parsing transactions from Banco Inter credit card CSV files."""

    # Expected headers for Banco Inter CSV format
    EXPECTED_HEADERS = ["data", "lançamento", "categoria", "tipo", "valor"]

    def can_handle_file(self, csv_file_path: str) -> bool:
        """Check if this handler can handle the CSV file.

        Reads the file with standard pandas CSV reading (no skiprows, comma
        delimiter) and checks if headers match the expected Banco Inter credit
        card CSV format.

        Args:
            csv_file_path: Path to the CSV file to check.

        Returns:
            True if this handler can handle the CSV format, False otherwise.
            Returns False if the file cannot be read or doesn't match the format.
        """
        try:
            # Read CSV file with standard settings
            df = pd.read_csv(
                csv_file_path,
                encoding="utf-8-sig",
                nrows=0,  # Only read headers, not data
            )

            if df.columns.empty:
                return False

            # Normalize column names
            headers = [str(col).strip().lower() for col in df.columns]

            # Check if all expected headers are present
            return all(header in headers for header in self.EXPECTED_HEADERS)
        except (
            FileNotFoundError,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
            ValueError,
        ):
            return False
        except Exception:
            # Any other error means we can't handle this file
            return False

    def parse_transactions_from_file(
        self, filename: str, user: User
    ) -> list[Transaction]:
        """Parse transactions from Banco Inter CSV file.

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
            df = pd.read_csv(filename, encoding="utf-8-sig")

            if df.empty:
                return []

            df.columns = df.columns.str.strip().str.lower()

            transactions = []
            for row_idx, (_, row) in enumerate(df.iterrows(), start=0):
                row_num = row_idx + 2
                try:
                    row_dict: dict[str, str] = {
                        str(k): str(v) if pd.notna(v) else "" for k, v in row.items()
                    }

                    transaction = self._parse_transaction_row(row_dict, user, row_num)
                    if transaction:
                        transactions.append(transaction)
                except ValueError as e:
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
        date_str = row.get("data", "").strip()
        if not date_str:
            raise ValueError(f"Row {row_num}: Missing required field: data")

        occurred_at = self._parse_date(date_str, row_num)
        if not occurred_at:
            raise ValueError(f"Row {row_num}: Invalid date format: {date_str}")

        valor_str = row.get("valor", "").strip()
        if not valor_str:
            raise ValueError(f"Row {row_num}: Missing required field: valor")

        amount = self._parse_amount(valor_str, row_num)

        if amount < 0:
            transaction_type = Transaction.TransactionType.INCOME
            amount = abs(amount)
        else:
            transaction_type = Transaction.TransactionType.EXPENSE

        description = row.get("lançamento", "").strip() or ""

        transaction = Transaction(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            occurred_at=occurred_at,
        )

        return transaction

    def _parse_date(self, date_str: str, row_num: int) -> Any | None:
        """Parse date string in DD/MM/YYYY format.

        Args:
            date_str: Date string to parse.
            row_num: Row number for error reporting.

        Returns:
            Date object if successful, None otherwise.
        """
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except ValueError:
            return None

    def _parse_amount(self, valor_str: str, row_num: int) -> Decimal:
        """Parse amount string in Brazilian Real format.

        Handles formats like:
        - "R$ 384,72" (positive)
        - "-R$ 13,94" (negative)
        - "R$ 1.468,78" (with thousands separator)

        Args:
            valor_str: Amount string to parse.
            row_num: Row number for error reporting.

        Returns:
            Decimal amount (negative if prefixed with minus sign).

        Raises:
            ValueError: If amount format is invalid.
        """
        valor_str = valor_str.replace("R$", "").strip()

        is_negative = valor_str.startswith("-")
        if is_negative:
            valor_str = valor_str[1:].strip()

        valor_str = valor_str.replace(".", "").replace(",", ".")

        try:
            amount = Decimal(valor_str)
            if is_negative:
                amount = -amount
            return amount
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Row {row_num}: Invalid amount format: {valor_str}"
            ) from e
