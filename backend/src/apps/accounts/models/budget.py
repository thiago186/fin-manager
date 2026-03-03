from django.contrib.auth.models import User
from django.db import models

from apps.accounts.models.categories import Category


class Budget(models.Model):
    """
    Represents a monthly budget limit for a specific category.

    Each user can set one budget per category, defining a monthly
    spending or income target.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="budgets",
        help_text="The owner of this budget",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budgets",
        help_text="The category this budget applies to",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monthly budget limit amount",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this budget is currently active",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the budget was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the budget was last updated",
    )

    # Type hints
    id: int

    class Meta:
        db_table = "budgets"
        ordering = ["category__name"]
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        unique_together = [["user", "category"]]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.category.name} - {self.amount}"

    def __repr__(self) -> str:
        return f"Budget(id={self.id}, category='{self.category.name}', amount={self.amount}, user_id={self.user.pk})"
