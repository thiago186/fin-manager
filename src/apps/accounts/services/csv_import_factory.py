import csv
from typing import Type

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.transactions_handlers.default_csv_handler import DefaultCSVHandler


class CSVImportFactory:
    """Factory for creating appropriate CSV handlers based on file format detection."""

    # Registry of format handlers
    _handlers: list[Type[BaseCSVHandler]] = [DefaultCSVHandler]

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
        # Read headers to detect format
        headers = cls._read_csv_headers(csv_file_path)

        # Try each handler to see if it can handle this format
        for handler_class in cls._handlers:
            handler_instance = handler_class()
            if handler_instance.can_handle_file(headers):
                return handler_instance

        # Default to DefaultCSVHandler if no specific match
        return DefaultCSVHandler()

    @classmethod
    def _read_csv_headers(cls, csv_file_path: str) -> list[str]:
        """Read CSV headers from file.

        Args:
            csv_file_path: Path to the CSV file.

        Returns:
            List of header column names (normalized to lowercase).

        Raises:
            ValueError: If file cannot be read or is not a valid CSV.
        """
        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                headers = next(reader, None)
                if not headers:
                    raise ValueError("CSV file is empty or has no headers")
                return [h.strip().lower() for h in headers]
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{csv_file_path}' not found.")
        except Exception as e:
            raise ValueError(f"Error reading CSV file '{csv_file_path}': {e}")