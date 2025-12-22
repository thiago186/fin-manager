import structlog
from typing import Type

import pandas as pd

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.transactions_handlers.banco_inter_csv_handler import (
    BancoInterCsvHandler,
)
from apps.accounts.transactions_handlers.default_csv_handler import DefaultCSVHandler

logger = structlog.stdlib.get_logger()


class CSVImportFactory:
    """Factory for creating appropriate CSV handlers based on file format detection."""

    # Registry of format handlers (order matters - more specific handlers first)
    _handlers: list[Type[BaseCSVHandler]] = [
        BancoInterCsvHandler,
        DefaultCSVHandler,
    ]

    @classmethod
    def create_handler(cls, csv_file_path: str) -> BaseCSVHandler:
        """Create appropriate CSV handler based on format detection.

        Args:
            csv_file_path: Path to the CSV file.

        Returns:
            Appropriate CSV handler instance.

        Raises:
            ValueError: If no suitable handler can be determined.
        """
        headers = cls._read_csv_headers(csv_file_path)

        for handler_class in cls._handlers:
            handler_instance = handler_class()
            if handler_instance.can_handle_file(headers):
                logger.debug(f"Using handler: {handler_class.__name__}")
                return handler_instance
            else:
                logger.debug(
                    f"Handler {handler_class.__name__} cannot handle file",
                    headers=headers,
                )

        return DefaultCSVHandler()

    @classmethod
    def _read_csv_headers(cls, csv_file_path: str) -> list[str]:
        """Read CSV headers from file using pandas.

        Pandas automatically handles BOM, encoding, and CSV parsing.

        Args:
            csv_file_path: Path to the CSV file.

        Returns:
            List of header column names (normalized to lowercase).

        Raises:
            ValueError: If file cannot be read or is not a valid CSV.
        """
        try:
            # Read only the first row to get headers
            # utf-8-sig automatically handles BOM
            df = pd.read_csv(
                csv_file_path,
                encoding="utf-8-sig",
                nrows=0,  # Only read headers, not data
            )
            if df.empty or df.columns.empty:
                raise ValueError("CSV file is empty or has no headers")
            # Normalize headers: strip whitespace and convert to lowercase
            return [str(col).strip().lower() for col in df.columns]
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{csv_file_path}' not found.")
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except Exception as e:
            raise ValueError(f"Error reading CSV file '{csv_file_path}': {e}")
