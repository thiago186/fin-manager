from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from django.contrib.auth.models import User
from django.db.models import QuerySet, Sum
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from apps.accounts.models.budget import Budget
from apps.accounts.models.transaction import Transaction

logger = structlog.stdlib.get_logger()


class BudgetInsightService:
    """Service for generating budget insights for the current month."""

    STATUS_SAFE = "safe"
    STATUS_WARNING = "warning"
    STATUS_CRITICAL = "critical"
    STATUS_OVER_BUDGET = "over-budget"

    def __init__(self, user: User):
        """Initialize the budget insight service.

        Args:
            user: The user who owns the budgets and transactions.
        """
        self.user = user

    def get_insights(self, threshold_percentage: int = 80) -> list[dict[str, Any]]:
        """Generate budget insights for the current month.

        Args:
            threshold_percentage: Minimum percentage spent to include in results.
                Defaults to 80. Use 0 to include all budgets.

        Returns:
            List of dictionaries containing budget insight data for categories
            that have spent at least the threshold percentage of their budget.
        """
        month_start, month_end = self._get_current_month_bounds()
        logger.info(
            "Generating budget insights",
            user_id=self.user.pk,
            month_start=month_start,
            month_end=month_end,
        )

        budgets = self._get_active_expense_budgets()
        if not budgets:
            logger.debug("No active expense budgets found", user_id=self.user.pk)
            return []

        spent_by_category = self._get_spent_by_category(month_start, month_end)

        insights = []
        for budget in budgets:
            spent = spent_by_category.get(budget.category_id, Decimal("0.00"))
            percentage = self._calculate_percentage(spent, budget.amount)

            if percentage < threshold_percentage:
                continue

            status = self._determine_status(percentage)
            remaining = budget.amount - spent

            insights.append(
                {
                    "category": {
                        "id": budget.category_id,
                        "name": budget.category.name,
                        "transaction_type": budget.category.transaction_type,
                    },
                    "budget_amount": budget.amount,
                    "spent_amount": spent,
                    "percentage": percentage,
                    "status": status,
                    "remaining_amount": remaining,
                }
            )

        insights.sort(key=lambda x: x["percentage"], reverse=True)

        logger.info(
            "Budget insights generated",
            user_id=self.user.pk,
            insights_count=len(insights),
        )
        return insights

    def _get_current_month_bounds(self) -> tuple[date, date]:
        """Calculate the start and end dates of the current month.

        Returns:
            Tuple of (first_day, last_day) for the current month.
        """
        today = timezone.now().date()
        first_day = today.replace(day=1)
        last_day = first_day + relativedelta(months=1) - relativedelta(days=1)
        return first_day, last_day

    def _get_active_expense_budgets(self) -> QuerySet[Budget]:
        """Retrieve active expense budgets for the user.

        Returns:
            QuerySet of Budget objects with related categories.
        """
        return (
            Budget.objects.filter(
                user=self.user,
                is_active=True,
                category__transaction_type="expense",
            )
            .select_related("category")
            .order_by("category__name")
        )

    def _get_spent_by_category(
        self, month_start: date, month_end: date
    ) -> dict[int, Decimal]:
        """Aggregate current month's expenses per category.

        Args:
            month_start: First day of the current month.
            month_end: Last day of the current month.

        Returns:
            Dictionary mapping category_id to total spent amount.
        """
        results = (
            Transaction.objects.filter(
                user=self.user,
                transaction_type=Transaction.TransactionType.EXPENSE,
                occurred_at__gte=month_start,
                occurred_at__lte=month_end,
                category__isnull=False,
            )
            .values("category")
            .annotate(spent=Sum("amount"))
        )

        return {row["category"]: row["spent"] or Decimal("0.00") for row in results}

    def _calculate_percentage(self, spent: Decimal, budget_amount: Decimal) -> float:
        """Calculate the percentage of budget spent.

        Args:
            spent: Amount spent in the category.
            budget_amount: Budget limit for the category.

        Returns:
            Percentage spent as a float.
        """
        if budget_amount == 0:
            return 0.0
        return float((spent / budget_amount) * 100)

    def _determine_status(self, percentage: float) -> str:
        """Determine the budget status based on percentage spent.

        Args:
            percentage: Percentage of budget spent.

        Returns:
            Status string: 'safe', 'warning', 'critical', or 'over-budget'.
        """
        if percentage >= 100:
            return self.STATUS_OVER_BUDGET
        if percentage >= 90:
            return self.STATUS_CRITICAL
        if percentage >= 80:
            return self.STATUS_WARNING
        return self.STATUS_SAFE
