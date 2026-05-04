from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction
from apps.accounts.models.transaction_tag import Tag
from apps.accounts.services.transaction_processor import TransactionProcessor


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def account(user: User) -> Account:
    return Account.objects.create(
        user=user, name="Checking", account_type=Account.AccountType.CHECKING
    )


@pytest.fixture
def credit_card(user: User) -> CreditCard:
    return CreditCard.objects.create(user=user, name="Visa")


@pytest.fixture
def category_expense(user: User) -> Category:
    return Category.objects.create(
        user=user, name="Food", transaction_type=Category.TransactionType.EXPENSE
    )


@pytest.fixture
def imported_report_account(user: User, account: Account) -> ImportedReport:
    return ImportedReport.objects.create(
        user=user,
        account=account,
        file_name="report_account.csv",
        file_path="/tmp/report_account.csv",
    )


@pytest.fixture
def imported_report_credit_card(user: User, credit_card: CreditCard) -> ImportedReport:
    return ImportedReport.objects.create(
        user=user,
        credit_card=credit_card,
        file_name="report_card.csv",
        file_path="/tmp/report_card.csv",
    )


def _make_transaction(user: User, **kwargs: object) -> Transaction:
    defaults: dict[str, object] = {
        "user": user,
        "transaction_type": Transaction.TransactionType.EXPENSE,
        "amount": Decimal("100.00"),
        "occurred_at": date(2024, 1, 1),
    }
    defaults.update(kwargs)
    return Transaction(**defaults)


# ---- Happy Path ----

@pytest.mark.django_db
def test_process_transaction_with_imported_report_account(
    user: User, imported_report_account: ImportedReport, account: Account
) -> None:
    """Transaction inherits account from ImportedReport and saves successfully."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    assert result["error_count"] == 0
    saved = Transaction.objects.get(user=user)
    assert saved.account == account
    assert saved.credit_card is None
    assert saved.origin == "report_account.csv"


@pytest.mark.django_db
def test_process_transaction_with_imported_report_credit_card(
    user: User, imported_report_credit_card: ImportedReport, credit_card: CreditCard
) -> None:
    """Transaction inherits credit_card from ImportedReport and saves successfully."""
    processor = TransactionProcessor(
        user=user, imported_report=imported_report_credit_card
    )
    txn = _make_transaction(user=user)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    saved = Transaction.objects.get(user=user)
    assert saved.credit_card == credit_card
    assert saved.account is None
    assert saved.origin == "report_card.csv"


@pytest.mark.django_db
def test_match_existing_category(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """Existing category is matched by name (case-insensitive) and transaction type."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user, transaction_type=Transaction.TransactionType.EXPENSE)
    txn._csv_category_name = category_expense.name.upper()  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    assert Transaction.objects.first().category == category_expense


@pytest.mark.django_db
def test_create_new_category_when_not_found(
    user: User, imported_report_account: ImportedReport
) -> None:
    """New category is created automatically when name does not exist."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user, transaction_type=Transaction.TransactionType.INCOME)
    txn._csv_category_name = "Salary"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    category = Category.objects.get(user=user, name="Salary")
    assert category.transaction_type == Category.TransactionType.INCOME
    assert Transaction.objects.first().category == category


@pytest.mark.django_db
def test_match_existing_subcategory(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """Existing subcategory is matched when it belongs to the specified category."""
    sub = Subcategory.objects.create(user=user, name="Groceries", category=category_expense)
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_category_name = category_expense.name  # type: ignore[attr-defined]
    txn._csv_subcategory_name = sub.name  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    saved = Transaction.objects.first()
    assert saved.subcategory == sub


@pytest.mark.django_db
def test_create_new_subcategory_when_not_found(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """New subcategory is created when it does not exist under the specified category."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_category_name = category_expense.name  # type: ignore[attr-defined]
    txn._csv_subcategory_name = "New Sub"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    sub = Subcategory.objects.get(user=user, name="New Sub", category=category_expense)
    assert Transaction.objects.first().subcategory == sub


@pytest.mark.django_db
def test_match_tags_from_string(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Tags matched from a comma-separated string; new tags are created."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_tags_value = "urgent, work"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    saved = Transaction.objects.first()
    tag_names = {t.name for t in saved.tags.all()}
    assert tag_names == {"urgent", "work"}


@pytest.mark.django_db
def test_match_tags_from_list(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Tags matched from a list of strings."""
    existing_tag = Tag.objects.create(user=user, name="existing")
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._json_tags_value = ["existing", "new-tag"]  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    saved = Transaction.objects.first()
    tag_names = {t.name for t in saved.tags.all()}
    assert tag_names == {"existing", "new-tag"}


@pytest.mark.django_db
def test_empty_tags_string_ignored(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Empty tag string does not attach any tags."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_tags_value = ""  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    assert Transaction.objects.first().tags.count() == 0


@pytest.mark.django_db
def test_process_multiple_transactions(
    user: User, imported_report_account: ImportedReport, account: Account
) -> None:
    """Multiple transactions are saved in a single batch."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txns = [
        _make_transaction(user=user, amount=Decimal("10.00")),
        _make_transaction(user=user, amount=Decimal("20.00")),
    ]

    result = processor.process_transactions(txns)

    assert result["success_count"] == 2
    assert Transaction.objects.count() == 2


# ---- Edge Cases ----

@pytest.mark.django_db
def test_transaction_without_account_or_credit_card_is_rejected(user: User) -> None:
    """Transaction without metadata and without ImportedReport is rejected."""
    processor = TransactionProcessor(user=user)
    txn = _make_transaction(user=user)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert "must have either an account or a credit card" in result["errors"][0]
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_subcategory_without_category_is_error(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Subcategory metadata without a matched category produces an error."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_subcategory_name = "Orphan Sub"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert "Cannot set subcategory without category" in result["errors"][0]
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_account_and_credit_card_simultaneously_is_error(user: User) -> None:
    """A transaction cannot have both account and credit_card set."""
    processor = TransactionProcessor(user=user)
    txn = _make_transaction(user=user)
    txn.account = Account.objects.create(
        user=user, name="A", account_type=Account.AccountType.CHECKING
    )
    txn.credit_card = CreditCard.objects.create(user=user, name="C")

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_imported_report_with_both_account_and_credit_card_is_error(
    user: User, account: Account, credit_card: CreditCard
) -> None:
    """ImportedReport with both account and credit_card causes validation error."""
    report = ImportedReport.objects.create(
        user=user,
        account=account,
        credit_card=credit_card,
        file_name="both.csv",
        file_path="/tmp/both.csv",
    )
    processor = TransactionProcessor(user=user, imported_report=report)
    txn = _make_transaction(user=user)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_validation_error_in_batch_rolls_back_all(
    user: User, imported_report_account: ImportedReport
) -> None:
    """If one transaction fails validation, none are saved."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    valid_txn = _make_transaction(user=user)
    invalid_txn = _make_transaction(user=user)
    invalid_txn.account = Account.objects.create(
        user=user, name="A", account_type=Account.AccountType.CHECKING
    )
    invalid_txn.credit_card = CreditCard.objects.create(user=user, name="C")

    result = processor.process_transactions([valid_txn, invalid_txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_invalid_installments_produces_error(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Transaction with invalid installment data fails validation."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user, installments_total=2, installment_number=5)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert "cannot be greater than" in result["errors"][0]


@pytest.mark.django_db
def test_category_mapped_correctly_for_income(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Category transaction type is mapped correctly for INCOME transactions."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user, transaction_type=Transaction.TransactionType.INCOME)
    txn._csv_category_name = "Bonus"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    category = Category.objects.get(user=user, name="Bonus")
    assert category.transaction_type == Category.TransactionType.INCOME


@pytest.mark.django_db
def test_subcategory_in_different_category_is_error(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """Subcategory that already exists under a DIFFERENT category raises an error."""
    other_category = Category.objects.create(
        user=user, name="Other", transaction_type=Category.TransactionType.EXPENSE
    )
    Subcategory.objects.create(user=user, name="Groceries", category=other_category)

    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_category_name = category_expense.name  # type: ignore[attr-defined]
    txn._csv_subcategory_name = "Groceries"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert "already exists under category 'Other'" in result["errors"][0]
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_subcategory_not_found_anywhere_is_created(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """Subcategory that does not exist anywhere is created under the specified category."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_category_name = category_expense.name  # type: ignore[attr-defined]
    txn._csv_subcategory_name = "Brand New"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    sub = Subcategory.objects.get(user=user, name="Brand New", category=category_expense)
    assert Transaction.objects.first().subcategory == sub


@pytest.mark.django_db
def test_subcategory_reused_when_exists_in_same_category(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """Subcategory existing in the specified category is reused (case-insensitive)."""
    sub = Subcategory.objects.create(user=user, name="Groceries", category=category_expense)
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_category_name = category_expense.name  # type: ignore[attr-defined]
    txn._csv_subcategory_name = "GROCERIES"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    assert Subcategory.objects.filter(user=user, name__iexact="Groceries").count() == 1
    assert Transaction.objects.first().subcategory == sub


@pytest.mark.django_db
def test_new_category_and_new_subcategory_created_together(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Both category and subcategory are created when neither exists."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_category_name = "NewCat"  # type: ignore[attr-defined]
    txn._csv_subcategory_name = "NewSub"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    category = Category.objects.get(user=user, name="NewCat")
    sub = Subcategory.objects.get(user=user, name="NewSub", category=category)
    saved = Transaction.objects.first()
    assert saved.category == category
    assert saved.subcategory == sub


@pytest.mark.django_db
def test_subcategory_specified_but_category_missing_is_error(
    user: User, imported_report_account: ImportedReport
) -> None:
    """Subcategory metadata without category metadata raises an error."""
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._csv_subcategory_name = "Orphan"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 0
    assert result["error_count"] == 1
    assert "Cannot set subcategory without category" in result["errors"][0]


@pytest.mark.django_db
def test_transaction_with_pre_set_account_without_imported_report(
    user: User, account: Account
) -> None:
    """Transaction already having an account set passes validation and saves with empty origin."""
    processor = TransactionProcessor(user=user)
    txn = _make_transaction(user=user, account=account)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    assert result["error_count"] == 0
    saved = Transaction.objects.first()
    assert saved.account == account
    assert saved.origin == ""


@pytest.mark.django_db
def test_transaction_with_pre_set_credit_card_without_imported_report(
    user: User, credit_card: CreditCard
) -> None:
    """Transaction already having a credit_card set passes validation and saves with empty origin."""
    processor = TransactionProcessor(user=user)
    txn = _make_transaction(user=user, credit_card=credit_card)

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    assert result["error_count"] == 0
    saved = Transaction.objects.first()
    assert saved.credit_card == credit_card
    assert saved.origin == ""


@pytest.mark.django_db
def test_xlsx_metadata_prefix_is_supported(
    user: User, imported_report_account: ImportedReport, category_expense: Category
) -> None:
    """_xlsx_ prefixed metadata is extracted and processed correctly."""
    sub = Subcategory.objects.create(user=user, name="XlsxSub", category=category_expense)
    processor = TransactionProcessor(user=user, imported_report=imported_report_account)
    txn = _make_transaction(user=user)
    txn._xlsx_category_name = category_expense.name  # type: ignore[attr-defined]
    txn._xlsx_subcategory_name = sub.name  # type: ignore[attr-defined]
    txn._xlsx_tags_value = "xlsx-tag"  # type: ignore[attr-defined]

    result = processor.process_transactions([txn])

    assert result["success_count"] == 1
    saved = Transaction.objects.first()
    assert saved.category == category_expense
    assert saved.subcategory == sub
    assert saved.tags.filter(name="xlsx-tag").exists()
