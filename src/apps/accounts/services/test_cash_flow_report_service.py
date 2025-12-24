from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.accounts.models.cash_flow_view import CashFlowGroup, CashFlowResult, CashFlowView
from apps.accounts.models.categories import Category
from apps.accounts.models.transaction import Transaction
from apps.accounts.services.cash_flow_report_service import CashFlowReportService


@pytest.mark.django_db
def test_generate_report_with_groups() -> None:
    """Test generating a report with groups only."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    category1 = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    category2 = Category.objects.create(
        user=user, name="Rent", transaction_type=Category.TransactionType.EXPENSE
    )

    group1 = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group1.categories.add(category1)

    group2 = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Costs", position=2
    )
    group2.categories.add(category2)

    Transaction.objects.create(
        user=user,
        category=category1,
        amount=Decimal("1000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(month=1, day=1),
    )
    Transaction.objects.create(
        user=user,
        category=category2,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=timezone.now().date().replace(month=1, day=1),
    )

    service = CashFlowReportService(user=user)
    year = timezone.now().year
    report = service.generate_report(view, year)

    assert report["view_id"] == view.id
    assert report["view_name"] == "Test View"
    assert report["year"] == year
    assert len(report["items"]) == 2
    assert report["items"][0]["type"] == "group"
    assert report["items"][0]["name"] == "Revenue"
    assert report["items"][1]["type"] == "group"
    assert report["items"][1]["name"] == "Costs"


@pytest.mark.django_db
def test_generate_report_with_results() -> None:
    """Test generating a report with groups and results."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    category1 = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    category2 = Category.objects.create(
        user=user, name="Rent", transaction_type=Category.TransactionType.EXPENSE
    )

    group1 = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group1.categories.add(category1)

    group2 = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Costs", position=2
    )
    group2.categories.add(category2)

    result = CashFlowResult.objects.create(
        cash_flow_view=view, name="Net Result", position=3
    )

    Transaction.objects.create(
        user=user,
        category=category1,
        amount=Decimal("1000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(month=1, day=1),
    )
    Transaction.objects.create(
        user=user,
        category=category2,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=timezone.now().date().replace(month=1, day=1),
    )

    service = CashFlowReportService(user=user)
    year = timezone.now().year
    report = service.generate_report(view, year)

    assert len(report["items"]) == 3
    assert report["items"][2]["type"] == "result"
    assert report["items"][2]["name"] == "Net Result"


@pytest.mark.django_db
def test_report_empty_group() -> None:
    """Test generating a report with a group that has no categories."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Empty Group", position=1
    )

    service = CashFlowReportService(user=user)
    year = timezone.now().year
    report = service.generate_report(view, year)

    assert len(report["items"]) == 1
    assert report["items"][0]["name"] == "Empty Group"
    assert all(
        Decimal(total) == Decimal("0.00")
        for total in report["items"][0]["monthly_totals"].values()
    )

