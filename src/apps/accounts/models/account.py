from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models

class Account(models.Model):
    """
    Represents a user's bank account where money can be deposited or withdrawn immediately.

    Examples include checking accounts, savings accounts, and digital wallets.
    The account has a balance that is directly affected by debit/credit transactions.
    """

    class AccountType(models.TextChoices):
        """Account type choices."""

        CHECKING = "checking", "Checking Account"

    class Currency(models.TextChoices):
        """Currency choices."""

        BRL = "BRL", "Brazilian Real"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="accounts",
        help_text="The owner of this account",
    )
    name = models.CharField(
        max_length=100,
        help_text="Descriptive name for the account (e.g., 'Checking Account Bank X')",
    )
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current balance of the account. Updated automatically when transactions are created/edited/deleted.",
    )
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CHECKING,
        help_text="Type of account (checking, savings, investment, etc.)",
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.BRL,
        help_text="Currency of the account",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Date and time when the account was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Date and time when the account was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the account is active and can be used for transactions",
    )

    class Meta:
        """Meta options for the Account model."""

        db_table = "accounts"
        ordering = ["-created_at"]
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["account_type"]),
        ]

    def __str__(self) -> str:
        """String representation of the account."""
        return f"{self.name} - {self.user.username}"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"Account(id={self.pk}, name='{self.name}', user_id={self.user.pk}, balance={self.current_balance})"

    @property
    def formatted_balance(self) -> str:
        """Return the current balance formatted as currency string."""
        return f"{self.currency} {self.current_balance:,.2f}"

    def update_balance(self, amount: Decimal) -> None:
        """
        Update the account balance by adding the specified amount.

        Args:
            amount: The amount to add to the current balance (can be negative for withdrawals)
        """
        self.current_balance += amount
        self.save(update_fields=["current_balance", "updated_at"])

    def can_withdraw(self, amount: Decimal) -> bool:
        """
        Check if the account has sufficient funds for a withdrawal.

        Args:
            amount: The amount to withdraw

        Returns:
            True if the account has sufficient funds, False otherwise
        """
        return self.current_balance >= amount
