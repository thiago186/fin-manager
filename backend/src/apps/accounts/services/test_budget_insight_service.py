from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.accounts.models.budget import Budget
from apps.accounts.models.categories import Category
from apps.accounts.models.transaction import Transaction
from apps.accounts.services.budget_insight_service import BudgetInsightService


@pytest.fixture
def user() -> User:
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def expense_category(user: User) -> Category:
    """Create an expense category."""
    return Category.objects.create(
        user=user, name="Food", transaction_type=Category.TransactionType.EXPENSE
    )


@pytest.fixture
def income_category(user: User) -> Category:
    """Create an income category."""
    return Category.objects.create(
        user=user, name="Salary", transaction_type=Category.TransactionType.INCOME
    )


@pytest.fixture
def today() -> date:
    """Return today's date."""
    return timezone.now().date()


@pytest.mark.django_db
def test_no_budgets_returns_empty_list(user: User) -> None:
    """When user has no budgets, insights should be empty."""
    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert insights == []


@pytest.mark.django_db
def test_budget_below_80_percent_not_included(
    user: User, expense_category: Category, today: date
) -> None:
    """Budgets with spending below 80% should not appear in insights."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert insights == []


@pytest.mark.django_db
def test_budget_below_80_percent_included_with_threshold_zero(
    user: User, expense_category: Category, today: date
) -> None:
    """Budgets with spending below 80% should appear when threshold is 0."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights(threshold_percentage=0)
    assert len(insights) == 1
    assert insights[0]["status"] == "safe"
    assert insights[0]["percentage"] == 50.0


@pytest.mark.django_db
def test_budget_at_exactly_80_percent_returns_warning(
    user: User, expense_category: Category, today: date
) -> None:
    """Budget at exactly 80% should appear with warning status."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("800.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert len(insights) == 1
    assert insights[0]["status"] == "warning"
    assert insights[0]["percentage"] == 80.0
    assert insights[0]["spent_amount"] == Decimal("800.00")
    assert insights[0]["remaining_amount"] == Decimal("200.00")


@pytest.mark.django_db
def test_budget_at_90_percent_returns_critical(
    user: User, expense_category: Category, today: date
) -> None:
    """Budget at 90% should appear with critical status."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("900.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert len(insights) == 1
    assert insights[0]["status"] == "critical"
    assert insights[0]["percentage"] == 90.0


@pytest.mark.django_db
def test_budget_over_100_percent_returns_over_budget(
    user: User, expense_category: Category, today: date
) -> None:
    """Budget over 100% should appear with over-budget status."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("1100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert len(insights) == 1
    assert insights[0]["status"] == "over-budget"
    assert insights[0]["percentage"] == 110.0
    assert insights[0]["remaining_amount"] == Decimal("-100.00")


@pytest.mark.django_db
def test_income_budget_is_ignored(
    user: User, income_category: Category, today: date
) -> None:
    """Income budgets should not be included in expense insights."""
    Budget.objects.create(user=user, category=income_category, amount=Decimal("5000.00"))
    Transaction.objects.create(
        user=user,
        category=income_category,
        amount=Decimal("5000.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert insights == []


@pytest.mark.django_db
def test_inactive_budget_is_ignored(
    user: User, expense_category: Category, today: date
) -> None:
    """Inactive budgets should not be included in insights."""
    Budget.objects.create(
        user=user, category=expense_category, amount=Decimal("1000.00"), is_active=False
    )
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("900.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert insights == []


@pytest.mark.django_db
def test_previous_month_transactions_ignored(
    user: User, expense_category: Category, today: date
) -> None:
    """Transactions from previous months should not count toward current month spending."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("900.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today.replace(month=today.month - 1 or 12),
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert insights == []


@pytest.mark.django_db
def test_multiple_budgets_sorted_by_percentage(
    user: User, today: date
) -> None:
    """Multiple budgets should be sorted by percentage descending."""
    cat1 = Category.objects.create(
        user=user, name="Food", transaction_type=Category.TransactionType.EXPENSE
    )
    cat2 = Category.objects.create(
        user=user, name="Transport", transaction_type=Category.TransactionType.EXPENSE
    )

    Budget.objects.create(user=user, category=cat1, amount=Decimal("1000.00"))
    Budget.objects.create(user=user, category=cat2, amount=Decimal("500.00"))

    Transaction.objects.create(
        user=user,
        category=cat1,
        amount=Decimal("850.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )
    Transaction.objects.create(
        user=user,
        category=cat2,
        amount=Decimal("500.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert len(insights) == 2
    assert insights[0]["category"]["name"] == "Transport"
    assert insights[0]["percentage"] == 100.0
    assert insights[1]["category"]["name"] == "Food"
    assert insights[1]["percentage"] == 85.0


@pytest.mark.django_db
def test_budget_with_no_transactions_returns_empty(
    user: User, expense_category: Category
) -> None:
    """A budget with zero transactions should not appear in insights."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert insights == []


@pytest.mark.django_db
def test_multiple_transactions_same_category_are_summed(
    user: User, expense_category: Category, today: date
) -> None:
    """Multiple transactions in the same category should be summed."""
    Budget.objects.create(user=user, category=expense_category, amount=Decimal("1000.00"))
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("400.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )
    Transaction.objects.create(
        user=user,
        category=expense_category,
        amount=Decimal("400.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        occurred_at=today,
    )

    service = BudgetInsightService(user=user)
    insights = service.get_insights()
    assert len(insights) == 1
    assert insights[0]["spent_amount"] == Decimal("800.00")
    assert insights[0]["percentage"] == 80.0
