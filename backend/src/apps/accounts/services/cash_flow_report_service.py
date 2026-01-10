from decimal import Decimal
from typing import Any

import structlog

from django.contrib.auth.models import User
from django.db.models import Case, DecimalField, F, Q, Sum, When
from django.db.models.functions import TruncMonth

from apps.accounts.models.cash_flow_view import (
    CashFlowGroup,
    CashFlowResult,
    CashFlowView,
)
from apps.accounts.models.categories import Category
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction

logger = structlog.stdlib.get_logger()


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
        logger.info(
            "Starting cash flow report generation",
            view_id=view.id,
            view_name=view.name,
            year=year,
            user_id=self.user.pk,
        )

        groups = view.groups.all().order_by("position")
        results = view.results.all().order_by("position")

        logger.debug(
            "Retrieved groups and results",
            view_id=view.id,
            groups_count=groups.count(),
            results_count=results.count(),
        )

        items = []
        group_totals: dict[int, dict[int, Decimal]] = {}

        for group in groups:
            logger.debug(
                "Processing group",
                view_id=view.id,
                group_id=group.id,
                group_name=group.name,
                group_position=group.position,
            )

            monthly_totals = self._calculate_group_monthly_totals(group, year)
            annual_total = sum(monthly_totals.values())
            group_totals[group.position] = monthly_totals

            categories_data = self._build_categories_with_subcategories(group, year)

            logger.debug(
                "Group totals calculated",
                view_id=view.id,
                group_id=group.id,
                group_name=group.name,
                annual_total=str(annual_total),
                categories_count=len(categories_data),
            )

            items.append(
                {
                    "type": "group",
                    "name": group.name,
                    "position": group.position,
                    "categories": categories_data,
                    "monthly_totals": {
                        str(month): str(total)
                        for month, total in monthly_totals.items()
                    },
                    "annual_total": str(annual_total),
                }
            )

        for result in results:
            logger.debug(
                "Processing result",
                view_id=view.id,
                result_id=result.id,
                result_name=result.name,
                result_position=result.position,
            )

            monthly_totals = self._calculate_result_monthly_totals(
                result, group_totals, year
            )
            annual_total = sum(monthly_totals.values())

            logger.debug(
                "Result totals calculated",
                view_id=view.id,
                result_id=result.id,
                result_name=result.name,
                annual_total=str(annual_total),
            )

            items.append(
                {
                    "type": "result",
                    "name": result.name,
                    "position": result.position,
                    "monthly_totals": {
                        str(month): str(total)
                        for month, total in monthly_totals.items()
                    },
                    "annual_total": str(annual_total),
                }
            )

        uncategorized_monthly_totals = self._calculate_uncategorized_transactions_monthly_totals(
            view, year
        )
        uncategorized_annual_total = sum(uncategorized_monthly_totals.values())

        if uncategorized_annual_total != Decimal("0.00"):
            logger.debug(
                "Adding uncategorized item to report",
                view_id=view.id,
                view_name=view.name,
                year=year,
                annual_total=str(uncategorized_annual_total),
            )

            items.append(
                {
                    "type": "uncategorized",
                    "name": "Uncategorized",
                    "monthly_totals": {
                        str(month): str(total)
                        for month, total in uncategorized_monthly_totals.items()
                    },
                    "annual_total": str(uncategorized_annual_total),
                }
            )

        logger.info(
            "Cash flow report generation completed",
            view_id=view.id,
            view_name=view.name,
            year=year,
            items_count=len(items),
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
            logger.warning(
                "Group has no categories, returning zero totals",
                group_id=group.id,
                group_name=group.name,
                year=year,
            )
            return {month: Decimal("0.00") for month in range(1, 13)}

        logger.debug(
            "Calculating group monthly totals",
            group_id=group.id,
            group_name=group.name,
            year=year,
            category_ids=category_ids,
            categories_count=len(category_ids),
        )

        transactions = Transaction.objects.filter(
            user=self.user,
            category_id__in=category_ids,
            occurred_at__year=year,
        )

        transactions_count = transactions.count()
        logger.debug(
            "Found transactions for group",
            group_id=group.id,
            group_name=group.name,
            year=year,
            transactions_count=transactions_count,
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

        monthly_totals: dict[int, Decimal] = {
            month: Decimal("0.00") for month in range(1, 13)
        }

        months_with_data = []
        for entry in monthly_data:
            month = entry["month"].month
            monthly_totals[month] = entry["total"]
            months_with_data.append(month)

        logger.debug(
            "Group monthly totals calculated",
            group_id=group.id,
            group_name=group.name,
            year=year,
            months_with_data=months_with_data,
            months_with_data_count=len(months_with_data),
        )

        return monthly_totals

    def _build_categories_with_subcategories(
        self, group: CashFlowGroup, year: int
    ) -> list[dict[str, Any]]:
        """Build categories with nested subcategories for a group.

        Args:
            group: The CashFlowGroup to build categories for.
            year: The year to calculate totals for.

        Returns:
            List of category dictionaries with nested subcategories.
        """
        categories_data = []
        group_categories = group.categories.all().order_by("name")

        for category in group_categories:
            logger.debug(
                "Processing category",
                group_id=group.id,
                category_id=category.id,
                category_name=category.name,
                year=year,
            )

            category_monthly_totals = self._calculate_category_monthly_totals(
                category, year
            )
            category_annual_total = sum(category_monthly_totals.values())

            subcategories_data = self._build_subcategories_for_category(category, year)

            categories_data.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "monthly_totals": {
                        str(month): str(total)
                        for month, total in category_monthly_totals.items()
                    },
                    "annual_total": str(category_annual_total),
                    "subcategories": subcategories_data,
                }
            )

        return categories_data

    def _build_subcategories_for_category(
        self, category: Category, year: int
    ) -> list[dict[str, Any]]:
        """Build subcategories list for a category, including uncategorized transactions.

        Args:
            category: The Category to build subcategories for.
            year: The year to calculate totals for.

        Returns:
            List of subcategory dictionaries, including an "Uncategorized" entry if needed.
        """
        subcategories_data = []

        category_subcategories = category.subcategories.filter(  # type: ignore[attr-defined]
            is_active=True, user=self.user
        ).order_by("name")

        for subcategory in category_subcategories:
            logger.debug(
                "Processing subcategory",
                category_id=category.id,
                subcategory_id=subcategory.id,
                subcategory_name=subcategory.name,
                year=year,
            )

            subcategory_monthly_totals = self._calculate_subcategory_monthly_totals(
                subcategory, year
            )
            subcategory_annual_total = sum(subcategory_monthly_totals.values())

            if subcategory_annual_total != Decimal("0.00"):
                subcategories_data.append(
                    {
                        "id": subcategory.id,
                        "name": subcategory.name,
                        "monthly_totals": {
                            str(month): str(total)
                            for month, total in subcategory_monthly_totals.items()
                        },
                        "annual_total": str(subcategory_annual_total),
                    }
                )

        uncategorized_totals = self._calculate_uncategorized_monthly_totals(
            category, year
        )
        uncategorized_annual_total = sum(uncategorized_totals.values())

        if uncategorized_annual_total != Decimal("0.00"):
            subcategories_data.append(
                {
                    "id": None,
                    "name": "Uncategorized",
                    "monthly_totals": {
                        str(month): str(total)
                        for month, total in uncategorized_totals.items()
                    },
                    "annual_total": str(uncategorized_annual_total),
                }
            )

        return subcategories_data

    def _calculate_category_monthly_totals(
        self, category: Category, year: int
    ) -> dict[int, Decimal]:
        """Calculate monthly totals for a category.

        Args:
            category: The Category to calculate totals for.
            year: The year to calculate totals for.

        Returns:
            Dictionary mapping month number (1-12) to total amount for that month.
        """
        logger.debug(
            "Calculating category monthly totals",
            category_id=category.id,
            category_name=category.name,
            year=year,
        )

        transactions = Transaction.objects.filter(
            user=self.user,
            category=category,
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

        monthly_totals: dict[int, Decimal] = {
            month: Decimal("0.00") for month in range(1, 13)
        }

        for entry in monthly_data:
            month = entry["month"].month
            monthly_totals[month] = entry["total"]

        return monthly_totals

    def _calculate_subcategory_monthly_totals(
        self, subcategory: Subcategory, year: int
    ) -> dict[int, Decimal]:
        """Calculate monthly totals for a subcategory.

        Args:
            subcategory: The Subcategory to calculate totals for.
            year: The year to calculate totals for.

        Returns:
            Dictionary mapping month number (1-12) to total amount for that month.
        """
        logger.debug(
            "Calculating subcategory monthly totals",
            subcategory_id=subcategory.id,
            subcategory_name=subcategory.name,
            category_id=subcategory.category.id,
            year=year,
        )

        transactions = Transaction.objects.filter(
            user=self.user,
            subcategory=subcategory,
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

        monthly_totals: dict[int, Decimal] = {
            month: Decimal("0.00") for month in range(1, 13)
        }

        for entry in monthly_data:
            month = entry["month"].month
            monthly_totals[month] = entry["total"]

        return monthly_totals

    def _calculate_uncategorized_monthly_totals(
        self, category: Category, year: int
    ) -> dict[int, Decimal]:
        """Calculate monthly totals for transactions without subcategories in a category.

        Args:
            category: The Category to calculate uncategorized totals for.
            year: The year to calculate totals for.

        Returns:
            Dictionary mapping month number (1-12) to total amount for that month.
        """
        logger.debug(
            "Calculating uncategorized monthly totals",
            category_id=category.id,
            category_name=category.name,
            year=year,
        )

        transactions = Transaction.objects.filter(
            user=self.user,
            category=category,
            subcategory__isnull=True,
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

        monthly_totals: dict[int, Decimal] = {
            month: Decimal("0.00") for month in range(1, 13)
        }

        for entry in monthly_data:
            month = entry["month"].month
            monthly_totals[month] = entry["total"]

        return monthly_totals

    def _calculate_uncategorized_transactions_monthly_totals(
        self, view: CashFlowView, year: int
    ) -> dict[int, Decimal]:
        """Calculate monthly totals for uncategorized transactions.

        Includes transactions with no category and transactions with categories
        not included in any group of the cash flow view.

        Args:
            view: The CashFlowView to calculate uncategorized totals for.
            year: The year to calculate totals for.

        Returns:
            Dictionary mapping month number (1-12) to total amount for that month.
        """
        groups = view.groups.all()
        group_category_ids = set()
        for group in groups:
            category_ids = list(group.categories.values_list("id", flat=True))
            group_category_ids.update(category_ids)

        logger.debug(
            "Calculating uncategorized transactions monthly totals",
            view_id=view.id,
            view_name=view.name,
            year=year,
            group_category_ids=list(group_category_ids),
            group_category_count=len(group_category_ids),
        )

        if group_category_ids:
            transactions = Transaction.objects.filter(
                user=self.user,
                occurred_at__year=year,
            ).filter(
                Q(category__isnull=True) | ~Q(category_id__in=group_category_ids)
            )
        else:
            transactions = Transaction.objects.filter(
                user=self.user,
                occurred_at__year=year,
            )

        transactions_with_category = transactions.filter(category__isnull=False)
        transactions_without_category = transactions.filter(category__isnull=True)

        monthly_totals: dict[int, Decimal] = {
            month: Decimal("0.00") for month in range(1, 13)
        }

        if transactions_with_category.exists():
            monthly_data_with_category = (
                transactions_with_category.annotate(month=TruncMonth("occurred_at"))
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

            for entry in monthly_data_with_category:
                month = entry["month"].month
                monthly_totals[month] += entry["total"]

        if transactions_without_category.exists():
            monthly_data_without_category = (
                transactions_without_category.annotate(month=TruncMonth("occurred_at"))
                .values("month")
                .annotate(
                    total=Sum(
                        Case(
                            When(
                                transaction_type=Transaction.TransactionType.INCOME,
                                then="amount",
                            ),
                            When(
                                transaction_type=Transaction.TransactionType.EXPENSE,
                                then=-1 * F("amount"),
                            ),
                            default=Decimal("0.00"),
                            output_field=DecimalField(max_digits=12, decimal_places=2),
                        )
                    )
                )
                .order_by("month")
            )

            for entry in monthly_data_without_category:
                month = entry["month"].month
                monthly_totals[month] += entry["total"]

        months_with_data = [
            month for month, total in monthly_totals.items() if total != Decimal("0.00")
        ]
        logger.debug(
            "Uncategorized transactions monthly totals calculated",
            view_id=view.id,
            view_name=view.name,
            year=year,
            months_with_data=months_with_data,
            months_with_data_count=len(months_with_data),
        )

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
        logger.debug(
            "Calculating result monthly totals",
            result_id=result.id,
            result_name=result.name,
            result_position=result.position,
            year=year,
            available_group_positions=list(group_totals.keys()),
        )

        monthly_totals: dict[int, Decimal] = {
            month: Decimal("0.00") for month in range(1, 13)
        }

        included_groups = []
        for group_position, group_monthly_totals in group_totals.items():
            if group_position < result.position:
                included_groups.append(group_position)
                for month in range(1, 13):
                    monthly_totals[month] += group_monthly_totals.get(
                        month, Decimal("0.00")
                    )

        logger.debug(
            "Result monthly totals calculated",
            result_id=result.id,
            result_name=result.name,
            result_position=result.position,
            included_group_positions=included_groups,
            included_groups_count=len(included_groups),
        )

        return monthly_totals
