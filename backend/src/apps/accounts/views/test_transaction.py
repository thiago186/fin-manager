from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models.transaction import Transaction


@pytest.mark.django_db
def test_duplicates_endpoint_returns_duplicate_transactions() -> None:
    """Duplicates endpoint should return transactions that share the same hash."""
    user = User.objects.create_user(username="duplicatesuser", password="testpass")
    date = timezone.now().date()

    t1 = Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )
    t2 = Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )
    Transaction.objects.create(
        user=user,
        amount=Decimal("50.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Tea",
        occurred_at=date,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/finance/transactions/duplicates/")

    assert response.status_code == 200
    results = response.data["results"]
    result_ids = {t["id"] for t in results}
    assert result_ids == {t1.id, t2.id}


@pytest.mark.django_db
def test_duplicates_endpoint_excludes_other_users_transactions() -> None:
    """Duplicates endpoint should not include transactions from other users."""
    user1 = User.objects.create_user(username="user1", password="testpass")
    user2 = User.objects.create_user(username="user2", password="testpass")
    date = timezone.now().date()

    t1 = Transaction.objects.create(
        user=user1,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )
    t2 = Transaction.objects.create(
        user=user1,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )
    Transaction.objects.create(
        user=user2,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )
    Transaction.objects.create(
        user=user2,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )

    client = APIClient()
    client.force_authenticate(user=user1)

    response = client.get("/api/v1/finance/transactions/duplicates/")

    assert response.status_code == 200
    results = response.data["results"]
    assert len(results) == 2
    result_ids = {t["id"] for t in results}
    assert result_ids == {t1.id, t2.id}


@pytest.mark.django_db
def test_duplicates_endpoint_returns_empty_when_no_duplicates() -> None:
    """Duplicates endpoint should return empty results when there are no duplicates."""
    user = User.objects.create_user(username="nodupesuser", password="testpass")
    date = timezone.now().date()

    Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/finance/transactions/duplicates/")

    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.mark.django_db
def test_duplicates_endpoint_excludes_ignored_transactions() -> None:
    """Duplicates endpoint should exclude transactions marked with ignore_duplicates=True."""
    user = User.objects.create_user(username="ignoredupesuser", password="testpass")
    date = timezone.now().date()

    Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
        ignore_duplicates=True,
    )
    Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
        ignore_duplicates=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/finance/transactions/duplicates/")

    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.mark.django_db
def test_bulk_update_can_set_ignore_duplicates() -> None:
    """Bulk update endpoint should allow setting ignore_duplicates on transactions."""
    user = User.objects.create_user(username="bulkignoreuser", password="testpass")
    date = timezone.now().date()

    t1 = Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )
    t2 = Transaction.objects.create(
        user=user,
        amount=Decimal("100.00"),
        transaction_type=Transaction.TransactionType.EXPENSE,
        description="Coffee",
        occurred_at=date,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        "/api/v1/finance/transactions/bulk-update/",
        {
            "transactions": [
                {"id": t1.id, "ignore_duplicates": True},
                {"id": t2.id, "ignore_duplicates": True},
            ]
        },
        format="json",
    )

    assert response.status_code == 200, response.data

    t1.refresh_from_db()
    t2.refresh_from_db()
    assert t1.ignore_duplicates is True
    assert t2.ignore_duplicates is True
