from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from django.contrib.auth.models import User

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.models.transaction import Transaction


class BancoInterBankStatementCsvHandler(BaseCSVHandler):
    """Handler for parsing transactions from Banco Inter bank statement CSV files."""

    # Expected headers for Banco Inter bank statement CSV format
    EXPECTED_HEADERS = ["data lançamento", "descrição", "valor", "saldo"]

    def can_handle_file(self, csv_file_path: str) -> bool:
        """Check if this handler can handle the CSV file.

        Reads the file with skiprows=5 (to skip metadata lines) and semicolon
        delimiter, then checks if headers match the expected Banco Inter bank
        statement format.

        Args:
            csv_file_path: Path to the CSV file to check.

        Returns:
            True if this handler can handle the CSV format, False otherwise.
            Returns False if the file cannot be read or doesn't match the format.
        """
        try:
            # Read CSV file skipping the first 5 metadata lines
            # Using skiprows=5 to skip lines 0-4 (0-indexed), so header is at row 5
            df = pd.read_csv(
                csv_file_path,
                encoding="utf-8-sig",
                sep=";",
                skiprows=5,
                nrows=0,  # Only read headers, not data
                skipinitialspace=True,
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
        """Parse transactions from Banco Inter bank statement CSV file.

        The CSV file has metadata lines at the top (lines 1-5) that need to be skipped.
        The header row is at line 6, and data rows start at line 7.

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
            # Read CSV file skipping the first 5 metadata lines
            # Using skiprows=5 to skip lines 0-4 (0-indexed), so header is at row 5
            df = pd.read_csv(
                filename,
                encoding="utf-8-sig",
                sep=";",
                skiprows=5,
                skipinitialspace=True,
            )

            if df.empty:
                return []

            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()

            transactions = []
            for row_idx, (_, row) in enumerate(df.iterrows(), start=0):
                # Row number for error reporting (accounting for skipped rows + header)
                row_num = row_idx + 7
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
        date_str = row.get("data lançamento", "").strip()
        if not date_str:
            raise ValueError(f"Row {row_num}: Missing required field: data lançamento")

        occurred_at = self._parse_date(date_str, row_num)
        if not occurred_at:
            raise ValueError(f"Row {row_num}: Invalid date format: {date_str}")

        valor_str = row.get("valor", "").strip()
        if not valor_str:
            raise ValueError(f"Row {row_num}: Missing required field: valor")

        amount = self._parse_amount(valor_str, row_num)

        # In bank statements: negative values are expenses (money going out),
        # positive values are income (money coming in)
        if amount < 0:
            transaction_type = Transaction.TransactionType.EXPENSE
            amount = abs(amount)
        else:
            transaction_type = Transaction.TransactionType.INCOME

        description = row.get("descrição", "").strip() or ""

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
        - "1,00" (positive)
        - "-5,00" (negative)
        - "5.000,00" (with thousands separator)
        - "-10.000,00" (negative with thousands separator)

        Args:
            valor_str: Amount string to parse.
            row_num: Row number for error reporting.

        Returns:
            Decimal amount (negative if prefixed with minus sign).

        Raises:
            ValueError: If amount format is invalid.
        """
        valor_str = valor_str.strip()

        is_negative = valor_str.startswith("-")
        if is_negative:
            valor_str = valor_str[1:].strip()

        # Remove thousands separator (dot) and replace decimal separator (comma) with dot
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
