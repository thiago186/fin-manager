from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction


class InstallmentPlan(models.Model):
    """Groups a set of installment transactions created together.

    Tracks all transactions belonging to a purchase split into installments,
    allowing the full set to be retrieved and managed as a unit.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="installment_plans",
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    installments_count = models.PositiveIntegerField()
    first_due_date = models.DateField()
    transaction_type = models.CharField(
        max_length=10,
        choices=Transaction.TransactionType.choices,
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installment_plans",
    )
    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installment_plans",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installment_plans",
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installment_plans",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Type hints
    id: int

    class Meta:
        """Meta options for InstallmentPlan model."""

        db_table = "installment_plans"
        indexes = [
            models.Index(fields=["user"], name="plan_user_idx"),
            models.Index(fields=["user", "first_due_date"], name="plan_user_date_idx"),
        ]
        ordering = ["-created_at"]

    def clean(self) -> None:
        """Validate that account and credit card are mutually exclusive."""
        super().clean()
        if self.account and self.credit_card:
            raise ValidationError(
                "An installment plan cannot be associated with both an account and a credit card."
            )

    def __str__(self) -> str:
        return f"{self.description or 'Plan'} - {self.installments_count}x {self.installment_amount}"
