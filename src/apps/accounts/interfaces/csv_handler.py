from abc import ABC, abstractmethod

from django.contrib.auth.models import User

from apps.accounts.models.transaction import Transaction


class BaseCSVHandler(ABC):
    """Base class for CSV transaction handlers."""

    @abstractmethod
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
        pass

    @abstractmethod
    def can_handle_file(self, csv_headers: list[str]) -> bool:
        """Check if this handler can handle the CSV file based on its headers.

        Args:
            csv_headers: List of CSV column headers (normalized to lowercase).

        Returns:
            True if this handler can handle the CSV format, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement can_handle_file method")
