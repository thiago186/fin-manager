from typing import Any

from django.contrib.auth.models import User
from django.db import models


class CreditCard(models.Model):
    """
    Represents a user's credit card.
    """

    id: int

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="credit_cards",
        help_text="The owner of this credit card",
    )
    name = models.CharField(
        max_length=100,
        help_text="Descriptive name for the credit card (e.g., 'Nubank Credit Card')",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Date and time when the credit card was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Date and time when the credit card was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the credit card is active and can be used for transactions",
    )

    class Meta:
        """Meta options for the CreditCard model."""

        db_table = "credit_cards"
        ordering = ["-created_at"]
        verbose_name = "Credit Card"
        verbose_name_plural = "Credit Cards"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        """String representation of the credit card."""
        return f"{self.name} - {self.user.username}"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"CreditCard(id={self.pk}, name='{self.name}', user_id={self.user.pk})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to validate fields before saving."""
        self.clean()
        super().save(*args, **kwargs)
