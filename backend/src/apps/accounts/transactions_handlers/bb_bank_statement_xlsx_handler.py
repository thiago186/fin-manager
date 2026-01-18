from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from django.contrib.auth.models import User

from apps.accounts.interfaces.xlsx_handler import BaseXlsxHandler
from apps.accounts.models.transaction import Transaction


class BBBankStatementXlsxHandler(BaseXlsxHandler):
    """Handler for parsing transactions from Banco do Brasil bank statement XLSX files."""

    # Expected headers for Banco do Brasil bank statement XLSX format
    EXPECTED_HEADERS = ["data", "lançamento", "detalhes", "n° documento", "valor", "tipo lançamento"]

    # Rows to ignore (balance rows)
    IGNORE_PATTERNS = ["saldo", "saldo do dia"]

    def can_handle_file(self, xlsx_file_path: str) -> bool:
        """Check if this handler can handle the XLSX file.

        Reads the file and checks if headers match the expected Banco do Brasil bank
        statement format.

        Args:
            xlsx_file_path: Path to the XLSX file to check.

        Returns:
            True if this handler can handle the XLSX format, False otherwise.
            Returns False if the file cannot be read or doesn't match the format.
        """
        try:
            # Read XLSX file (only headers)
            df = pd.read_excel(
                xlsx_file_path,
                engine="openpyxl",
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
            ImportError,  # openpyxl not installed
        ):
            return False
        except Exception:
            # Any other error means we can't handle this file
            return False

    def parse_transactions_from_file(
        self, filename: str, user: User
    ) -> list[Transaction]:
        """Parse transactions from Banco do Brasil bank statement XLSX file.

        Args:
            filename: Path to the XLSX file containing transaction data.
            user: The user who owns these transactions.

        Returns:
            List of Transaction objects parsed from the XLSX file.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            ValueError: If required fields are missing or invalid.
        """
        try:
            # Read XLSX file
            df = pd.read_excel(
                filename,
                engine="openpyxl",
            )

            if df.empty:
                return []

            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()

            transactions = []
            for row_idx, (_, row) in enumerate(df.iterrows(), start=0):
                # Row number for error reporting (accounting for header)
                row_num = row_idx + 2  # +1 for 0-indexed, +1 for header row
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
        except ImportError as e:
            raise ValueError(
                f"Error reading XLSX file '{filename}': openpyxl library is required. "
                f"Install it with: pip install openpyxl"
            ) from e
        except Exception as e:
            raise ValueError(f"Error reading XLSX file '{filename}': {e}")

    def _parse_transaction_row(
        self, row: dict[str, str], user: User, row_num: int
    ) -> Transaction | None:
        """Parse a single transaction row from the XLSX data.

        Args:
            row: Dictionary containing transaction data from XLSX row.
            user: The user who owns this transaction.
            row_num: Row number for error reporting.

        Returns:
            Transaction object or None if the transaction should be skipped.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Check if this is a balance row that should be ignored
        lancamento = row.get("lançamento", "").strip().lower()
        if any(pattern in lancamento for pattern in self.IGNORE_PATTERNS):
            return None

        date_str = row.get("data", "")
        if not date_str or (isinstance(date_str, str) and not date_str.strip()):
            raise ValueError(f"Row {row_num}: Missing required field: data")

        occurred_at = self._parse_date(date_str, row_num)
        if not occurred_at:
            raise ValueError(f"Row {row_num}: Invalid date format: {date_str}")

        valor_str = row.get("valor", "").strip()
        if not valor_str:
            raise ValueError(f"Row {row_num}: Missing required field: valor")

        amount = self._parse_amount(valor_str, row_num)

        # Determine transaction type from "Tipo Lançamento" column or amount sign
        tipo_lancamento = row.get("tipo lançamento", "").strip().lower()
        
        if tipo_lancamento == "entrada":
            transaction_type = Transaction.TransactionType.INCOME
            amount = abs(amount)
        elif tipo_lancamento == "saída":
            transaction_type = Transaction.TransactionType.EXPENSE
            amount = abs(amount)
        else:
            # Fallback to amount sign if tipo lançamento is not available
            # In bank statements: negative values are expenses (money going out),
            # positive values are income (money coming in)
            if amount < 0:
                transaction_type = Transaction.TransactionType.EXPENSE
                amount = abs(amount)
            else:
                transaction_type = Transaction.TransactionType.INCOME

        # Build description from "Lançamento" and "Detalhes"
        lancamento_desc = row.get("lançamento", "").strip()
        detalhes = row.get("detalhes", "").strip()
        
        if detalhes:
            description = f"{lancamento_desc} - {detalhes}"
        else:
            description = lancamento_desc or ""

        transaction = Transaction(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            occurred_at=occurred_at,
        )

        return transaction

    def _parse_date(self, date_str: Any, row_num: int) -> Any | None:
        """Parse date string in DD/MM/YYYY format.

        Handles pandas datetime objects, date objects, and string formats.

        Args:
            date_str: Date string, datetime object, or date object to parse.
            row_num: Row number for error reporting.

        Returns:
            Date object if successful, None otherwise.
        """
        try:
            # Handle pandas datetime objects
            if hasattr(date_str, 'date') and callable(getattr(date_str, 'date', None)):
                return date_str.date()
            # Handle date objects directly
            if hasattr(date_str, 'year') and hasattr(date_str, 'month') and hasattr(date_str, 'day'):
                return date_str
            
            # Handle string formats
            date_str = str(date_str).strip()
            
            # Skip invalid dates
            if date_str == "00/00/0000" or date_str == "00/00/00" or date_str == "nan" or date_str == "":
                return None
            
            # Try DD/MM/YYYY format first
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                pass
            
            # Try DD/MM/YY format
            try:
                return datetime.strptime(date_str, "%d/%m/%y").date()
            except ValueError:
                pass
            
            # Try ISO format
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            except ValueError:
                pass
            
            return None
        except Exception:
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
        # Handle numeric types from pandas
        if isinstance(valor_str, (int, float)):
            return Decimal(str(valor_str))
        
        valor_str = str(valor_str).strip()

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
