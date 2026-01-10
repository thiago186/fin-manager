from django.contrib.auth.models import User
from django.db import models

from apps.accounts.models.categories import Category


class Subcategory(models.Model):
    """
    Represents a subcategory for classifying income and expenses.

    Subcategories belong to a parent Category and inherit the transaction_type
    from their parent category. For example, a "Transportation" category can have
    subcategories like "Fuel", "Maintenance", etc.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subcategories",
        help_text="The owner of this subcategory",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the subcategory (e.g., 'Fuel', 'Maintenance', 'Groceries')",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
        help_text="The parent category this subcategory belongs to",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the subcategory",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the subcategory was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the subcategory was last updated",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the subcategory is active and can be used for transactions",
    )

    # Type hints
    id: int

    class Meta:
        """Meta options for the Subcategory model."""

        db_table = "subcategories"
        ordering = ["name"]
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["category"]),
        ]
        unique_together = [
            ["user", "name", "category"],
        ]

    def __str__(self) -> str:
        """String representation of the subcategory."""
        return f"{self.category.name} > {self.name}"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"Subcategory(id={self.id}, name='{self.name}', user_id={self.user.pk}, category_id={self.category.pk})"

    @property
    def transaction_type(self) -> str:
        """Get the transaction type from the parent category."""
        return self.category.transaction_type

