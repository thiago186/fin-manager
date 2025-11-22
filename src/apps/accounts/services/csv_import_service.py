import os
import tempfile
from typing import Any

from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction as db_transaction

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.transaction import Transaction
from apps.accounts.models.transaction_tag import Tag
from apps.accounts.services.csv_import_factory import CSVImportFactory


class CSVImportService:
    """Service for importing transactions from CSV files."""

    def __init__(self, user: User):
        """Initialize the CSV import service.

        Args:
            user: The user who owns the transactions to be imported.
        """
        self.user = user

    def import_transactions(self, csv_file: UploadedFile) -> dict[str, Any]:
        """Import transactions from CSV file.

        Args:
            csv_file: Uploaded CSV file.

        Returns:
            Dictionary with import results:
            {
                "success_count": int,
                "error_count": int,
                "errors": list[str]
            }
        """
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".csv"
        ) as temp_file:
            for chunk in csv_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            handler = CSVImportFactory.create_handler(temp_file_path)

            transactions = handler.parse_transactions_from_file(
                temp_file_path, self.user
            )

            return self._process_transactions(transactions)
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def _process_transactions(self, transactions: list[Transaction]) -> dict[str, Any]:
        """Process and save transactions with matching logic.

        All transactions are processed in a single database transaction.
        If any transaction fails validation or saving, the entire import is rolled back.
        All errors are collected and returned so the user can fix them at once.

        Args:
            transactions: List of parsed Transaction objects.

        Returns:
            Dictionary with import results.
        """
        errors: list[str] = []
        processed_transactions: list[Transaction] = []

        # First pass: Process all transactions and collect errors
        for idx, transaction in enumerate(transactions, start=1):
            try:
                # Match account if identifier provided
                if (
                    hasattr(transaction, "_csv_account_identifier")
                    and transaction._csv_account_identifier
                ):  # type: ignore
                    account = self._match_account(transaction._csv_account_identifier)  # type: ignore
                    if account:
                        transaction.account = account

                # Match credit card if identifier provided
                if (
                    hasattr(transaction, "_csv_credit_card_identifier")
                    and transaction._csv_credit_card_identifier
                ):  # type: ignore
                    credit_card = self._match_credit_card(
                        transaction._csv_credit_card_identifier
                    )  # type: ignore
                    if credit_card:
                        transaction.credit_card = credit_card

                # Match category if name provided
                if (
                    hasattr(transaction, "_csv_category_name")
                    and transaction._csv_category_name
                ):  # type: ignore
                    category = self._match_category_by_name(
                        transaction._csv_category_name,  # type: ignore
                        transaction.transaction_type,
                        None,
                    )
                    if category:
                        transaction.category = category

                # Match subcategory if name provided
                if (
                    hasattr(transaction, "_csv_subcategory_name")
                    and transaction._csv_subcategory_name
                ):  # type: ignore
                    parent_category = transaction.category
                    if not parent_category:
                        errors.append(
                            f"Transaction {idx}: Cannot set subcategory without category"
                        )
                    else:
                        subcategory = self._match_category_by_name(
                            transaction._csv_subcategory_name,  # type: ignore
                            transaction.transaction_type,
                            parent_category,
                        )
                        if subcategory:
                            transaction.subcategory = subcategory

                # Validate transaction (but don't save yet)
                transaction.full_clean()

                # Store tags for later assignment
                tags_to_set: list[Tag] = []
                if (
                    hasattr(transaction, "_csv_tags_value")
                    and transaction._csv_tags_value
                ):  # type: ignore
                    tags_to_set = self._match_tags(transaction._csv_tags_value)  # type: ignore
                    transaction._tags_to_set = tags_to_set  # type: ignore

                processed_transactions.append(transaction)
            except Exception as e:
                errors.append(f"Transaction {idx}: {str(e)}")

        # If there are any errors, return them without saving anything
        if errors:
            return {
                "success_count": 0,
                "error_count": len(errors),
                "errors": errors,
            }

        # If no errors, save all transactions in a single atomic transaction
        try:
            with db_transaction.atomic():
                for transaction_obj in processed_transactions:
                    transaction_obj.save()

                    # Set tags after saving (many-to-many relationships require saved object)
                    if hasattr(transaction_obj, "_tags_to_set"):  # type: ignore
                        tags_to_set = transaction_obj._tags_to_set  # type: ignore
                        transaction_obj.tags.set(tags_to_set)

            return {
                "success_count": len(processed_transactions),
                "error_count": 0,
                "errors": [],
            }
        except Exception as e:
            # If any transaction fails during save, the entire transaction is rolled back
            return {
                "success_count": 0,
                "error_count": len(processed_transactions),
                "errors": [f"Failed to save transactions: {str(e)}"],
            }

    def _match_category_by_name(
        self, name: str, transaction_type: str, parent: Category | None
    ) -> Category:
        """Match or create category by name.

        Args:
            name: Category name.
            transaction_type: Transaction type (INCOME/EXPENSE).
            parent: Parent category if this is a subcategory.

        Returns:
            Category instance (existing or newly created).
        """
        # Normalize transaction type for category
        category_transaction_type = (
            "income"
            if transaction_type == Transaction.TransactionType.INCOME
            else "expense"
        )

        # Try to find existing category
        category = Category.objects.filter(
            user=self.user,
            name__iexact=name,
            parent=parent,
            transaction_type=category_transaction_type,
        ).first()

        if category:
            return category

        # Create new category if not found
        category = Category.objects.create(
            user=self.user,
            name=name,
            parent=parent,
            transaction_type=category_transaction_type,
        )

        return category

    def _match_account(self, identifier: str) -> Account | None:
        """Match account by name or ID.

        Args:
            identifier: Account name or ID string.

        Returns:
            Account instance if found, None otherwise.
        """
        # Try to match by ID first
        try:
            account_id = int(identifier)
            account = Account.objects.filter(user=self.user, id=account_id).first()
            if account:
                return account
        except ValueError:
            pass

        # Try to match by name
        account = Account.objects.filter(
            user=self.user, name__iexact=identifier
        ).first()
        return account

    def _match_credit_card(self, identifier: str) -> CreditCard | None:
        """Match credit card by name or ID.

        Args:
            identifier: Credit card name or ID string.

        Returns:
            CreditCard instance if found, None otherwise.
        """
        # Try to match by ID first
        try:
            credit_card_id = int(identifier)
            credit_card = CreditCard.objects.filter(
                user=self.user, id=credit_card_id
            ).first()
            if credit_card:
                return credit_card
        except ValueError:
            pass

        # Try to match by name
        credit_card = CreditCard.objects.filter(
            user=self.user, name__iexact=identifier
        ).first()
        return credit_card

    def _match_tags(self, tag_names: str) -> list[Tag]:
        """Match tags by name (create if not exists).

        Args:
            tag_names: Comma-separated tag names.

        Returns:
            List of Tag instances.
        """
        tags: list[Tag] = []
        tag_name_list = [name.strip() for name in tag_names.split(",") if name.strip()]

        for tag_name in tag_name_list:
            # Try to find existing tag
            tag = Tag.objects.filter(user=self.user, name__iexact=tag_name).first()

            if not tag:
                # Create new tag if not found
                tag = Tag.objects.create(user=self.user, name=tag_name)

            tags.append(tag)

        return tags
