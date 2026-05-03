from datetime import date
from decimal import Decimal

import pytest
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.installment_plan import InstallmentPlan
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction
from apps.accounts.services.installment_service import InstallmentService
from apps.accounts.services.installment_update_service import InstallmentUpdateService


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def category(user: User) -> Category:
    return Category.objects.create(
        user=user, name="Expenses", transaction_type=Category.TransactionType.EXPENSE
    )


@pytest.fixture
def account(user: User) -> Account:
    return Account.objects.create(
        user=user, name="Checking", account_type=Account.AccountType.CHECKING
    )


@pytest.fixture
def credit_card(user: User) -> CreditCard:
    return CreditCard.objects.create(user=user, name="Visa")


@pytest.fixture
def plan_12x(user: User, category: Category, account: Account) -> InstallmentPlan:
    service = InstallmentService()
    plan, _ = service.create_plan_with_transactions(
        user=user,
        description="Test Plan",
        transaction_type=Transaction.TransactionType.EXPENSE,
        total_amount=Decimal("1200.00"),
        installment_amount=None,
        installments_count=12,
        first_due_date=date(2024, 1, 15),
        account=account,
        credit_card=None,
        category=category,
        subcategory=None,
    )
    return plan


@pytest.mark.django_db
def test_amount_change_updates_all_transactions(plan_12x: InstallmentPlan) -> None:
    """Changing amount on one transaction should update every sibling."""
    txn = plan_12x.transactions.get(installment_number=5)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"amount": Decimal("150.00")}
    )

    plan_12x.refresh_from_db()
    assert plan_12x.installment_amount == Decimal("150.00")
    assert plan_12x.total_amount == Decimal("1800.00")

    for t in plan_12x.transactions.all():
        assert t.amount == Decimal("150.00")


@pytest.mark.django_db
def test_increase_installments_total_creates_new_transactions(
    plan_12x: InstallmentPlan,
) -> None:
    """Increasing installments_total should create new transactions."""
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(plan_12x, txn, {"installments_total": 15})

    plan_12x.refresh_from_db()
    assert plan_12x.installments_count == 15
    assert plan_12x.transactions.count() == 15
    assert plan_12x.total_amount == Decimal("100.00") * 15

    last = plan_12x.transactions.get(installment_number=15)
    assert last.occurred_at == date(2025, 3, 15)


@pytest.mark.django_db
def test_decrease_installments_total_removes_excess(plan_12x: InstallmentPlan) -> None:
    """Decreasing installments_total should delete excess transactions."""
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(plan_12x, txn, {"installments_total": 8})

    plan_12x.refresh_from_db()
    assert plan_12x.installments_count == 8
    assert plan_12x.transactions.count() == 8
    assert plan_12x.total_amount == Decimal("100.00") * 8

    for t in plan_12x.transactions.all():
        assert t.installments_total == 8


@pytest.mark.django_db
def test_date_change_on_middle_transaction_shifts_subsequent(
    plan_12x: InstallmentPlan,
) -> None:
    """Changing occurred_at on a middle transaction shifts all subsequent ones."""
    txn = plan_12x.transactions.get(installment_number=5)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"occurred_at": date(2024, 7, 10)}
    )

    txn.refresh_from_db()
    assert txn.occurred_at == date(2024, 7, 10)

    txn6 = plan_12x.transactions.get(installment_number=6)
    assert txn6.occurred_at == date(2024, 8, 10)

    txn12 = plan_12x.transactions.get(installment_number=12)
    assert txn12.occurred_at == date(2025, 2, 10)

    txn4 = plan_12x.transactions.get(installment_number=4)
    assert txn4.occurred_at == date(2024, 4, 15)


@pytest.mark.django_db
def test_date_change_on_first_transaction_shifts_all(plan_12x: InstallmentPlan) -> None:
    """Changing occurred_at on transaction 1 shifts the entire plan."""
    txn = plan_12x.transactions.get(installment_number=1)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"occurred_at": date(2024, 2, 5)}
    )

    plan_12x.refresh_from_db()
    assert plan_12x.first_due_date == date(2024, 2, 5)

    for t in plan_12x.transactions.all():
        expected = date(2024, 2, 5) + relativedelta(months=t.installment_number - 1)
        assert t.occurred_at == expected


@pytest.mark.django_db
def test_date_change_on_last_transaction_only_affects_itself(
    plan_12x: InstallmentPlan,
) -> None:
    """Changing occurred_at on the last transaction only affects that one."""
    txn = plan_12x.transactions.get(installment_number=12)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"occurred_at": date(2025, 5, 20)}
    )

    txn.refresh_from_db()
    assert txn.occurred_at == date(2025, 5, 20)

    txn11 = plan_12x.transactions.get(installment_number=11)
    assert txn11.occurred_at == date(2024, 11, 15)


@pytest.mark.django_db
def test_simultaneous_amount_and_count_increase(
    plan_12x: InstallmentPlan,
) -> None:
    """New transactions should receive the new amount when both fields change."""
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"amount": Decimal("200.00"), "installments_total": 15}
    )

    plan_12x.refresh_from_db()
    assert plan_12x.installments_count == 15
    assert plan_12x.total_amount == Decimal("200.00") * 15

    for t in plan_12x.transactions.all():
        assert t.amount == Decimal("200.00")


@pytest.mark.django_db
def test_category_change_cascades_to_all(plan_12x: InstallmentPlan, user: User) -> None:
    """Changing category on one transaction should update every sibling."""
    new_cat = Category.objects.create(
        user=user, name="New Cat", transaction_type=Category.TransactionType.EXPENSE
    )
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(plan_12x, txn, {"category": new_cat})

    plan_12x.refresh_from_db()
    assert plan_12x.category == new_cat

    for t in plan_12x.transactions.all():
        assert t.category == new_cat


@pytest.mark.django_db
def test_account_change_cascades_to_all(
    plan_12x: InstallmentPlan, user: User, account: Account
) -> None:
    """Changing account on one transaction should update every sibling."""
    new_account = Account.objects.create(
        user=user, name="Savings", account_type=Account.AccountType.CHECKING
    )
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"account": new_account}
    )

    plan_12x.refresh_from_db()
    assert plan_12x.account == new_account

    for t in plan_12x.transactions.all():
        assert t.account == new_account


@pytest.mark.django_db
def test_credit_card_change_cascades_to_all(
    plan_12x: InstallmentPlan, user: User, credit_card: CreditCard
) -> None:
    """Changing credit_card on one transaction should update every sibling."""
    new_card = CreditCard.objects.create(user=user, name="Mastercard")
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"credit_card": new_card}
    )

    plan_12x.refresh_from_db()
    assert plan_12x.credit_card == new_card

    for t in plan_12x.transactions.all():
        assert t.credit_card == new_card


@pytest.mark.django_db
def test_transaction_type_change_cascades_to_all(plan_12x: InstallmentPlan) -> None:
    """Changing transaction_type on one transaction should update every sibling."""
    txn = plan_12x.transactions.get(installment_number=3)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(
        plan_12x, txn, {"transaction_type": Transaction.TransactionType.INCOME}
    )

    plan_12x.refresh_from_db()
    assert plan_12x.transaction_type == Transaction.TransactionType.INCOME

    for t in plan_12x.transactions.all():
        assert t.transaction_type == Transaction.TransactionType.INCOME


@pytest.mark.django_db
def test_description_change_does_not_cascade(plan_12x: InstallmentPlan) -> None:
    """Changing description should not affect siblings."""
    txn = plan_12x.transactions.get(installment_number=5)
    original_descriptions = {
        t.id: t.description for t in plan_12x.transactions.exclude(id=txn.id)
    }

    txn.description = "Unique description"
    txn.save()

    for t in plan_12x.transactions.exclude(id=txn.id):
        assert t.description == original_descriptions[t.id]


@pytest.mark.django_db
def test_decrease_to_one_installment(plan_12x: InstallmentPlan) -> None:
    """Decreasing to 1 installment leaves a single transaction."""
    txn = plan_12x.transactions.get(installment_number=1)
    service = InstallmentUpdateService()

    service.update_plan_from_transaction(plan_12x, txn, {"installments_total": 1})

    plan_12x.refresh_from_db()
    assert plan_12x.installments_count == 1
    assert plan_12x.transactions.count() == 1
    assert plan_12x.total_amount == Decimal("100.00")

    remaining = plan_12x.transactions.first()
    assert remaining.installment_number == 1
    assert remaining.installments_total == 1
