from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from typing import Any
import uuid
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.transaction_tag import Tag


class Transaction(models.Model):
    """Represents a transaction in the system.

    A transaction is a record of a financial event, such as a purchase, sale, or transfer of money.
    It can be an income, an expense, or a transfer between accounts.
    """

    class TransactionType(models.TextChoices):
        """Transaction type choices."""

        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"
        TRANSFER = "TRANSFER", "Transfer"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="The user who owns this transaction",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        help_text="The type of transaction",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)
    occurred_at = models.DateField()
    charge_at_card = models.DateField(null=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_transactions",
    )
    tags: models.ManyToManyField = models.ManyToManyField(
        Tag,
        related_name="transactions",
        blank=True,
        help_text="The tags for this transaction",
    )

    installments_total = models.PositiveIntegerField(default=1)
    installment_number = models.PositiveIntegerField(default=1)
    installment_group_id = models.CharField(max_length=36, null=True, blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The date and time the transaction was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="The date and time the transaction was last updated"
    )

    def clean(self) -> None:
        """Validate the transaction data."""
        super().clean()

        if self.account and self.credit_card:
            raise ValidationError(
                "A transaction cannot be associated with both an account and a credit card. "
                "Please choose either an account or a credit card."
            )

        if self.credit_card and not self.charge_at_card:
            raise ValidationError(
                "When a transaction is associated with a credit card, the 'charge_at_card' field must be filled."
            )

        if self.installments_total > 1 or self.installment_number > 1:
            if self.installments_total <= 0:
                raise ValidationError("installments_total must be greater than 0.")

            if self.installment_number <= 0:
                raise ValidationError("installment_number must be greater than 0.")

            if self.installment_number > self.installments_total:
                raise ValidationError(
                    f"installment_number ({self.installment_number}) cannot be greater than "
                    f"installments_total ({self.installments_total})."
                )

            if not self.installment_group_id:
                self.installment_group_id = str(uuid.uuid4())

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.transaction_type} - {self.amount} on {self.occurred_at}"
