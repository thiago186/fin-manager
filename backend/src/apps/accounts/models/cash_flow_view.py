from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models.categories import Category

class CashFlowView(models.Model):
    """
    Represents a user-configurable cash flow view configuration.

    Users can create multiple named views, each containing groups of categories
    and result lines that calculate cumulative totals.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cash_flow_views",
        help_text="The owner of this cash flow view",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the cash flow view (e.g., 'Monthly P&L', 'Annual Summary')",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the view was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the view was last updated",
    )

    # Type hints
    id: int
    groups: models.Manager["CashFlowGroup"]
    results: models.Manager["CashFlowResult"]

    class Meta:
        """Meta options for the CashFlowView model."""

        db_table = "cash_flow_views"
        ordering = ["name"]
        verbose_name = "Cash Flow View"
        verbose_name_plural = "Cash Flow Views"
        indexes = [
            models.Index(fields=["user", "name"]),
        ]
        unique_together = [
            ["user", "name"],
        ]

    def __str__(self) -> str:
        """String representation of the cash flow view."""
        return self.name

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"CashFlowView(id={self.id}, name='{self.name}', user_id={self.user.pk})"


class CashFlowGroup(models.Model):
    """
    Represents a group of categories within a cash flow view.

    Groups contain one or more categories and display a subtotal for those categories.
    Examples: "Revenue", "Operating Costs", "Taxes".
    """

    cash_flow_view = models.ForeignKey(
        CashFlowView,
        on_delete=models.CASCADE,
        related_name="groups",
        help_text="The cash flow view this group belongs to",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the group (e.g., 'Revenue', 'Operating Costs')",
    )
    position = models.PositiveIntegerField(
        help_text="Position of this group within the view (used for ordering and result calculations)",
    )
    categories: models.ManyToManyField = models.ManyToManyField(  # type: ignore[assignment]
        Category,
        related_name="cash_flow_groups",
        blank=True,
        help_text="Categories included in this group",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the group was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the group was last updated",
    )

    # Type hints
    id: int
    cash_flow_view_id: int

    class Meta:
        """Meta options for the CashFlowGroup model."""

        db_table = "cash_flow_groups"
        ordering = ["position"]
        verbose_name = "Cash Flow Group"
        verbose_name_plural = "Cash Flow Groups"
        indexes = [
            models.Index(fields=["cash_flow_view", "position"]),
        ]

    def clean(self) -> None:
        """Validate the group data."""
        super().clean()
        if self.cash_flow_view_id:
            view = self.cash_flow_view
            groups = CashFlowGroup.objects.filter(
                cash_flow_view=view, position=self.position
            )
            if self.pk:
                groups = groups.exclude(pk=self.pk)
            if groups.exists():
                raise ValidationError(
                    f"Position {self.position} is already taken by another group in this view."
                )
            results = CashFlowResult.objects.filter(
                cash_flow_view=view, position=self.position
            )
            if results.exists():
                raise ValidationError(
                    f"Position {self.position} is already taken by a result in this view."
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """String representation of the cash flow group."""
        return f"{self.cash_flow_view.name} - {self.name}"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"CashFlowGroup(id={self.id}, name='{self.name}', view_id={self.cash_flow_view_id}, position={self.position})"


class CashFlowResult(models.Model):
    """
    Represents a result line within a cash flow view.

    Result lines calculate cumulative totals of all groups above them (based on position).
    Examples: "Gross Margin", "Net Result".
    """

    cash_flow_view = models.ForeignKey(
        CashFlowView,
        on_delete=models.CASCADE,
        related_name="results",
        help_text="The cash flow view this result belongs to",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the result line (e.g., 'Gross Margin', 'Net Result')",
    )
    position = models.PositiveIntegerField(
        help_text="Position of this result within the view (used for ordering and calculation)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the result was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the result was last updated",
    )

    # Type hints
    id: int
    cash_flow_view_id: int

    class Meta:
        """Meta options for the CashFlowResult model."""

        db_table = "cash_flow_results"
        ordering = ["position"]
        verbose_name = "Cash Flow Result"
        verbose_name_plural = "Cash Flow Results"
        indexes = [
            models.Index(fields=["cash_flow_view", "position"]),
        ]

    def clean(self) -> None:
        """Validate the result data."""
        super().clean()
        if self.cash_flow_view_id:
            view = self.cash_flow_view
            groups = CashFlowGroup.objects.filter(
                cash_flow_view=view, position=self.position
            )
            results = CashFlowResult.objects.filter(
                cash_flow_view=view, position=self.position
            )
            if self.pk:
                results = results.exclude(pk=self.pk)
            if groups.exists() or results.exists():
                raise ValidationError(
                    f"Position {self.position} is already taken by another group or result in this view."
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure clean() is called."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """String representation of the cash flow result."""
        return f"{self.cash_flow_view.name} - {self.name}"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return f"CashFlowResult(id={self.id}, name='{self.name}', view_id={self.cash_flow_view_id}, position={self.position})"
