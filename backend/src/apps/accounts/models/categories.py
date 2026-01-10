from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models

if TYPE_CHECKING:
    from apps.accounts.models.subcategory import Subcategory


class Category(models.Model):
    """
    Represents a top-level category for classifying income and expenses.

    Categories can have subcategories (via the Subcategory model), allowing for
    hierarchical organization. For example, a "Transportation" category can have
    subcategories like "Fuel", "Maintenance", etc.
    """

    class TransactionType(models.TextChoices):
        """Transaction type choices for categorizing income vs expenses."""

        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
        help_text="The owner of this category",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the category (e.g., 'Transportation', 'Food', 'Salary')",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        help_text="Type of transactions this category is used for",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the category",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the category was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the category was last updated",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the category is active and can be used for transactions",
    )

    # Type hints
    id: int
    subcategories: models.Manager["Subcategory"]

    class Meta:
        """Meta options for the Category model."""

        db_table = "categories"
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["transaction_type"]),
        ]
        unique_together = [
            ["user", "name", "transaction_type"],
        ]

    def __str__(self) -> str:
        """String representation of the category."""
        return self.name

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"Category(id={self.id}, name='{self.name}', user_id={self.user.pk}, transaction_type='{self.transaction_type}')"

    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level category (always True for Category model)."""
        return True
