from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.accounts.models.cash_flow_view import (
    CashFlowGroup,
    CashFlowResult,
    CashFlowView,
)
from apps.accounts.models.categories import Category
from apps.accounts.models.subcategory import Subcategory
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

    group2 = CashFlowGroup.objects.create(cash_flow_view=view, name="Costs", position=2)
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

    group2 = CashFlowGroup.objects.create(cash_flow_view=view, name="Costs", position=2)
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


@pytest.mark.django_db
def test_report_with_subcategories() -> None:
    """Test generating a report with categories that have subcategories."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    category = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    subcategory1 = Subcategory.objects.create(
        user=user, name="Product Sales", category=category
    )
    subcategory2 = Subcategory.objects.create(
        user=user, name="Service Sales", category=category
    )

    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group.categories.add(category)

    year = timezone.now().year
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=subcategory1,
        amount=Decimal("1000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=subcategory2,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )

    service = CashFlowReportService(user=user)
    report = service.generate_report(view, year)

    assert len(report["items"]) == 1
    group_item = report["items"][0]
    assert group_item["type"] == "group"
    assert len(group_item["categories"]) == 1

    category_data = group_item["categories"][0]
    assert category_data["id"] == category.id
    assert category_data["name"] == "Sales"
    assert Decimal(category_data["annual_total"]) == Decimal("1500.00")
    assert len(category_data["subcategories"]) == 2

    subcat1_data = next(
        sc for sc in category_data["subcategories"] if sc["id"] == subcategory1.id
    )
    assert subcat1_data["name"] == "Product Sales"
    assert Decimal(subcat1_data["annual_total"]) == Decimal("1000.00")

    subcat2_data = next(
        sc for sc in category_data["subcategories"] if sc["id"] == subcategory2.id
    )
    assert subcat2_data["name"] == "Service Sales"
    assert Decimal(subcat2_data["annual_total"]) == Decimal("500.00")


@pytest.mark.django_db
def test_report_with_uncategorized_transactions() -> None:
    """Test generating a report with transactions without subcategories."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    category = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )

    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group.categories.add(category)

    year = timezone.now().year
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=None,
        amount=Decimal("1000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )

    service = CashFlowReportService(user=user)
    report = service.generate_report(view, year)

    category_data = report["items"][0]["categories"][0]
    assert Decimal(category_data["annual_total"]) == Decimal("1000.00")
    assert len(category_data["subcategories"]) == 1

    uncategorized = category_data["subcategories"][0]
    assert uncategorized["id"] is None
    assert uncategorized["name"] == "Uncategorized"
    assert Decimal(uncategorized["annual_total"]) == Decimal("1000.00")


@pytest.mark.django_db
def test_report_with_mixed_subcategorized_and_uncategorized() -> None:
    """Test report with both subcategorized and uncategorized transactions."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    category = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    subcategory = Subcategory.objects.create(
        user=user, name="Product Sales", category=category
    )

    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group.categories.add(category)

    year = timezone.now().year
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=subcategory,
        amount=Decimal("1000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=None,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )

    service = CashFlowReportService(user=user)
    report = service.generate_report(view, year)

    category_data = report["items"][0]["categories"][0]
    assert Decimal(category_data["annual_total"]) == Decimal("1500.00")
    assert len(category_data["subcategories"]) == 2

    subcat_data = next(
        sc for sc in category_data["subcategories"] if sc["id"] == subcategory.id
    )
    assert Decimal(subcat_data["annual_total"]) == Decimal("1000.00")

    uncategorized = next(
        sc for sc in category_data["subcategories"] if sc["id"] is None
    )
    assert Decimal(uncategorized["annual_total"]) == Decimal("500.00")

    total_subcategories = sum(
        Decimal(sc["annual_total"]) for sc in category_data["subcategories"]
    )
    assert total_subcategories == Decimal(category_data["annual_total"])


@pytest.mark.django_db
def test_report_category_totals_equal_subcategory_sum() -> None:
    """Test that category totals equal the sum of all subcategory totals."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")

    category = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    subcategory1 = Subcategory.objects.create(
        user=user, name="Product Sales", category=category
    )
    subcategory2 = Subcategory.objects.create(
        user=user, name="Service Sales", category=category
    )

    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group.categories.add(category)

    year = timezone.now().year
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=subcategory1,
        amount=Decimal("1000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=subcategory2,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )
    Transaction.objects.create(
        user=user,
        category=category,
        subcategory=None,
        amount=Decimal("300.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=timezone.now().date().replace(year=year, month=1, day=1),
    )

    service = CashFlowReportService(user=user)
    report = service.generate_report(view, year)

    category_data = report["items"][0]["categories"][0]
    category_total = Decimal(category_data["annual_total"])

    subcategory_sum = sum(
        Decimal(sc["annual_total"]) for sc in category_data["subcategories"]
    )

    assert category_total == subcategory_sum
    assert category_total == Decimal("1800.00")
