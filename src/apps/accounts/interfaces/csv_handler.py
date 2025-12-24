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
    def can_handle_file(self, csv_file_path: str) -> bool:
        """Check if this handler can handle the CSV file.

        Each handler is responsible for reading the file and determining if it
        can handle the format. This allows handlers to use their own detection
        strategies (e.g., reading specific lines, checking metadata, etc.).

        Args:
            csv_file_path: Path to the CSV file to check.

        Returns:
            True if this handler can handle the CSV format, False otherwise.
            Should return False (not raise) if the file cannot be read or
            doesn't match the expected format.
        """
        raise NotImplementedError("Subclasses must implement can_handle_file method")
