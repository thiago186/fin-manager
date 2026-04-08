from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models.cash_flow_view import CashFlowGroup, CashFlowView
from apps.accounts.models.categories import Category
from apps.accounts.models.installment_plan import InstallmentPlan
from apps.accounts.models.transaction import Transaction


@pytest.mark.django_db
def test_report_accepts_installments_only_scope() -> None:
    """Report endpoint should filter to installment-linked transactions when requested."""
    user = User.objects.create_user(username="reportscopeuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Scoped View")

    category = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    group = CashFlowGroup.objects.create(cash_flow_view=view, name="Revenue", position=1)
    group.categories.add(category)

    year = timezone.now().year
    date = timezone.now().date().replace(year=year, month=1, day=1)

    plan = InstallmentPlan.objects.create(
        user=user,
        description="Laptop",
        total_amount=Decimal("100.00"),
        installment_amount=Decimal("50.00"),
        installments_count=2,
        first_due_date=date,
        transaction_type=Transaction.TransactionType.INCOME,
    )

    Transaction.objects.create(
        user=user,
        category=category,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=date,
        installments_total=2,
        installment_number=1,
        installment_plan=plan,
    )
    Transaction.objects.create(
        user=user,
        category=category,
        amount=Decimal("40.00"),
        transaction_type=Transaction.TransactionType.INCOME,
        occurred_at=date,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        f"/api/v1/finance/cash-flow-views/{view.id}/report/",
        {"year": year, "transaction_scope": "installments_only"},
    )

    assert response.status_code == 200
    assert Decimal(str(response.data["items"][0]["annual_total"])) == Decimal("100.00")


@pytest.mark.django_db
def test_report_rejects_invalid_transaction_scope() -> None:
    """Report endpoint should return 400 for invalid transaction_scope values."""
    user = User.objects.create_user(username="invalidscopeuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Invalid Scope View")

    client = APIClient()
    client.force_authenticate(user=user)

    year = timezone.now().year
    response = client.get(
        f"/api/v1/finance/cash-flow-views/{view.id}/report/",
        {"year": year, "transaction_scope": "invalid_scope"},
    )

    assert response.status_code == 400
    assert "transaction_scope" in response.data["error"]
