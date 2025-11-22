from abc import ABC, abstractmethod

from apps.accounts.models import Transaction


class BaseCreditCardBillHandler:
    """Base class for credit card bill handlers."""

    @abstractmethod
    def parse_transactions_from_file(self, filename: str) -> list[Transaction]:
        """Parse transactions from billing file."""
