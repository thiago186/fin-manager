from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from typing import Any
import uuid
import hashlib
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.subcategory import Subcategory
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
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    subcategory = models.ForeignKey(
        Subcategory,
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

    # AI classification flag
    need_review = models.BooleanField(
        default=False,
        help_text="Whether this transaction needs review after AI classification",
    )

    origin = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="Source of transaction creation (e.g., 'manual', report filename)",
    )

    hash = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
        help_text="MD5 hash of amount, description, and occurred_at for duplicate detection",
    )

    # Type hints
    id: int

    class Meta:
        """Meta options for Transaction model."""

        indexes = [
            models.Index(fields=["user", "transaction_type"], name="txn_user_type_idx"),
            models.Index(fields=["user", "account"], name="txn_user_account_idx"),
            models.Index(fields=["user", "credit_card"], name="txn_user_card_idx"),
            models.Index(fields=["user", "category"], name="txn_user_category_idx"),
            models.Index(fields=["user", "occurred_at"], name="txn_user_date_idx"),
            models.Index(fields=["user", "need_review"], name="txn_user_review_idx"),
        ]
        ordering = ["-occurred_at"]

    def clean(self) -> None:
        """Validate the transaction data."""
        super().clean()

        if self.account and self.credit_card:
            raise ValidationError(
                "A transaction cannot be associated with both an account and a credit card. "
                "Please choose either an account or a credit card."
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

    def _calculate_hash(self) -> str:
        """Calculate MD5 hash from amount, description, and occurred_at.

        Returns:
            MD5 hash as hexadecimal string (32 characters).
        """
        amount_str = str(self.amount)
        description_str = self.description or ""
        occurred_at_str = self.occurred_at.isoformat() if self.occurred_at else ""

        hash_input = f"{amount_str}|{description_str}|{occurred_at_str}"
        return hashlib.md5(hash_input.encode("utf-8")).hexdigest()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure clean() is called and hash is calculated."""
        self.full_clean()
        self.hash = self._calculate_hash()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.transaction_type} - {self.amount} on {self.occurred_at}"
