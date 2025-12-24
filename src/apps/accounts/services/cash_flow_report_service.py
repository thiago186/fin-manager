from decimal import Decimal
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Case, DecimalField, F, Sum, When
from django.db.models.functions import TruncMonth

from apps.accounts.models.cash_flow_view import CashFlowGroup, CashFlowResult, CashFlowView
from apps.accounts.models.categories import Category
from apps.accounts.models.transaction import Transaction


class CashFlowReportService:
    """Service for generating cash flow reports from views."""

    def __init__(self, user: User):
        """Initialize the cash flow report service.

        Args:
            user: The user who owns the cash flow view.
        """
        self.user = user

    def generate_report(self, view: CashFlowView, year: int) -> dict[str, Any]:
        """Generate a cash flow report for a given view and year.

        Args:
            view: The CashFlowView to generate the report for.
            year: The year to generate the report for.

        Returns:
            Dictionary containing the report data with monthly totals for each group and result.
        """
        groups = view.groups.all().order_by("position")
        results = view.results.all().order_by("position")

        items = []
        group_totals: dict[int, dict[int, Decimal]] = {}

        for group in groups:
            monthly_totals = self._calculate_group_monthly_totals(group, year)
            annual_total = sum(monthly_totals.values())
            group_totals[group.position] = monthly_totals

            categories = [
                {"id": cat.id, "name": cat.name} for cat in group.categories.all()
            ]

            items.append(
                {
                    "type": "group",
                    "name": group.name,
                    "position": group.position,
                    "categories": categories,
                    "monthly_totals": {
                        str(month): str(total) for month, total in monthly_totals.items()
                    },
                    "annual_total": str(annual_total),
                }
            )

        for result in results:
            monthly_totals = self._calculate_result_monthly_totals(
                result, group_totals, year
            )
            annual_total = sum(monthly_totals.values())

            items.append(
                {
                    "type": "result",
                    "name": result.name,
                    "position": result.position,
                    "monthly_totals": {
                        str(month): str(total) for month, total in monthly_totals.items()
                    },
                    "annual_total": str(annual_total),
                }
            )

        return {
            "view_id": view.id,
            "view_name": view.name,
            "year": year,
            "items": items,
        }

    def _calculate_group_monthly_totals(
        self, group: CashFlowGroup, year: int
    ) -> dict[int, Decimal]:
        """Calculate monthly totals for a group.

        Args:
            group: The CashFlowGroup to calculate totals for.
            year: The year to calculate totals for.

        Returns:
            Dictionary mapping month number (1-12) to total amount for that month.
        """
        category_ids = list(group.categories.values_list("id", flat=True))
        if not category_ids:
            return {month: Decimal("0.00") for month in range(1, 13)}

        transactions = Transaction.objects.filter(
            user=self.user,
            category_id__in=category_ids,
            occurred_at__year=year,
        )

        monthly_data = (
            transactions.annotate(month=TruncMonth("occurred_at"))
            .values("month")
            .annotate(
                total=Sum(
                    Case(
                        When(
                            category__transaction_type=Category.TransactionType.INCOME,
                            then="amount",
                        ),
                        When(
                            category__transaction_type=Category.TransactionType.EXPENSE,
                            then=-1 * F("amount"),
                        ),
                        default=Decimal("0.00"),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                )
            )
            .order_by("month")
        )

        monthly_totals: dict[int, Decimal] = {month: Decimal("0.00") for month in range(1, 13)}

        for entry in monthly_data:
            month = entry["month"].month
            monthly_totals[month] = entry["total"]

        return monthly_totals

    def _calculate_result_monthly_totals(
        self,
        result: CashFlowResult,
        group_totals: dict[int, dict[int, Decimal]],
        year: int,
    ) -> dict[int, Decimal]:
        """Calculate monthly totals for a result line.

        Results sum all groups with position < result.position.

        Args:
            result: The CashFlowResult to calculate totals for.
            group_totals: Dictionary mapping group positions to their monthly totals.
            year: The year (unused but kept for consistency).

        Returns:
            Dictionary mapping month number (1-12) to total amount for that month.
        """
        monthly_totals: dict[int, Decimal] = {month: Decimal("0.00") for month in range(1, 13)}

        for group_position, group_monthly_totals in group_totals.items():
            if group_position < result.position:
                for month in range(1, 13):
                    monthly_totals[month] += group_monthly_totals.get(
                        month, Decimal("0.00")
                    )

        return monthly_totals

