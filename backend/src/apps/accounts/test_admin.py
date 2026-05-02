import datetime
from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.http import HttpRequest

from apps.accounts.admin import TransactionAdmin
from apps.accounts.models import Account, Transaction


pytestmark = pytest.mark.django_db


def test_recalculate_hash_action() -> None:
    """Test that recalculate_hash admin action updates transaction hashes."""
    user = User.objects.create_user(username="testuser", password="testpass")
    account = Account.objects.create(
        user=user,
        name="Test Account",
        account_type=Account.AccountType.CHECKING,
        current_balance=Decimal("100.00"),
    )
    transaction = Transaction.objects.create(
        user=user,
        account=account,
        transaction_type=Transaction.TransactionType.EXPENSE,
        amount=Decimal("50.00"),
        description="Test",
        occurred_at=datetime.date(2024, 1, 1),
    )
    expected_hash = transaction.hash

    # Corrupt the hash directly in the database to bypass model save()
    Transaction.objects.filter(pk=transaction.pk).update(hash="wrong_hash")
    transaction.refresh_from_db()
    assert transaction.hash == "wrong_hash"

    admin_instance = TransactionAdmin(Transaction, AdminSite())
    admin_instance.message_user = lambda *args, **kwargs: None  # type: ignore[method-assign]

    request = HttpRequest()
    request.user = user
    queryset = Transaction.objects.filter(pk=transaction.pk)

    admin_instance.recalculate_hash(request, queryset)

    transaction.refresh_from_db()
    assert transaction.hash == expected_hash
