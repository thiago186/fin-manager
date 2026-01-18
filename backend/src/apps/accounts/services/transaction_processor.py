from typing import Any

import structlog
from django.contrib.auth.models import User
from django.db import transaction as db_transaction

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction
from apps.accounts.models.transaction_tag import Tag

logger = structlog.stdlib.get_logger()


class TransactionProcessor:
    """Centralized service for processing and saving transactions.

    This service handles all transaction processing logic including:
    - Matching accounts, credit cards, categories, subcategories, and tags
    - Validating transactions
    - Saving transactions in database transactions
    - Error handling

    It is format-agnostic and works with transactions from CSV, JSON, or XLSX files.
    """

    def __init__(self, user: User, imported_report: ImportedReport | None = None):
        """Initialize the transaction processor.

        Args:
            user: The user who owns the transactions to be processed.
            imported_report: Optional ImportedReport instance with account/credit_card association.
        """
        self.user = user
        self.imported_report = imported_report

    def process_transactions(
        self,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        """Process and save transactions with matching logic.

        All transactions are processed in a single database transaction.
        If any transaction fails validation or saving, the entire import is rolled back.
        All errors are collected and returned so the user can fix them at once.

        Args:
            transactions: List of parsed Transaction objects.

        Returns:
            Dictionary with import results:
            {
                "success_count": int,
                "error_count": int,
                "errors": list[str]
            }
        """
        errors: list[str] = []
        processed_transactions: list[Transaction] = []

        # First pass: Process all transactions and collect errors
        total_transactions = len(transactions)
        logger.info(
            "Processing transactions",
            total_count=total_transactions,
            user_id=self.user.id,  # type: ignore
        )

        # Get account/credit_card from imported_report if provided
        report_account = self.imported_report.account if self.imported_report else None
        report_credit_card = (
            self.imported_report.credit_card if self.imported_report else None
        )

        if report_account:
            logger.info(
                "Using account from import report",
                account_id=report_account.id,  # type: ignore
                account_name=report_account.name,
            )
        if report_credit_card:
            logger.info(
                "Using credit card from import report",
                credit_card_id=report_credit_card.id,  # type: ignore
                credit_card_name=report_credit_card.name,
            )

        for idx, transaction in enumerate(transactions, start=1):
            try:
                if idx % 10 == 0 or idx == total_transactions:
                    logger.debug(
                        "Processing transaction",
                        transaction_index=idx,
                        total_count=total_transactions,
                    )

                # Extract metadata from transaction (format-agnostic)
                metadata = self._extract_metadata(transaction)

                # Match account if identifier provided in file
                if metadata["account_identifier"]:
                    account = self._match_account(metadata["account_identifier"])
                    if account:
                        transaction.account = account
                        logger.debug(
                            "Matched account from file",
                            transaction_index=idx,
                            account_id=account.id,  # type: ignore
                            account_name=account.name,
                        )
                # Otherwise, use account from import report if provided
                elif report_account:
                    transaction.account = report_account
                    logger.debug(
                        "Using account from import report",
                        transaction_index=idx,
                        account_id=report_account.id,  # type: ignore
                        account_name=report_account.name,
                    )

                # Match credit card if identifier provided in file
                if metadata["credit_card_identifier"]:
                    credit_card = self._match_credit_card(
                        metadata["credit_card_identifier"]
                    )
                    if credit_card:
                        transaction.credit_card = credit_card
                        logger.debug(
                            "Matched credit card from file",
                            transaction_index=idx,
                            credit_card_id=credit_card.id,  # type: ignore
                            credit_card_name=credit_card.name,
                        )
                # Otherwise, use credit card from import report if provided
                elif report_credit_card:
                    transaction.credit_card = report_credit_card
                    logger.debug(
                        "Using credit card from import report",
                        transaction_index=idx,
                        credit_card_id=report_credit_card.id,  # type: ignore
                        credit_card_name=report_credit_card.name,
                    )

                # Match category if name provided
                if metadata["category_name"]:
                    # Convert Transaction.TransactionType to Category.TransactionType
                    transaction_type_str = transaction.transaction_type.lower()
                    category_transaction_type = (
                        Category.TransactionType.INCOME
                        if transaction_type_str == "income"
                        else Category.TransactionType.EXPENSE
                    )
                    category = self._match_category_by_name(
                        metadata["category_name"],
                        category_transaction_type,
                    )
                    if category:
                        transaction.category = category
                        logger.debug(
                            "Matched category",
                            transaction_index=idx,
                            category_id=category.id,  # type: ignore
                            category_name=category.name,
                        )

                # Match subcategory if name provided
                if metadata["subcategory_name"]:
                    parent_category = transaction.category
                    if not parent_category:
                        error_msg = (
                            f"Transaction {idx}: Cannot set subcategory without category"
                        )
                        errors.append(error_msg)
                        logger.warning(
                            "Cannot set subcategory without category",
                            transaction_index=idx,
                        )
                    else:
                        subcategory = self._match_subcategory_by_name(
                            metadata["subcategory_name"],
                            parent_category,
                        )
                        if subcategory:
                            transaction.subcategory = subcategory  # type: ignore
                            logger.debug(
                                "Matched subcategory",
                                transaction_index=idx,
                                subcategory_id=subcategory.id,
                                subcategory_name=subcategory.name,
                            )

                # Validate transaction (but don't save yet)
                transaction.full_clean()

                # Store tags for later assignment
                if metadata["tags_value"]:
                    tags_to_set = self._match_tags(metadata["tags_value"])
                    transaction._tags_to_set = tags_to_set  # type: ignore
                    if tags_to_set:
                        logger.debug(
                            "Matched tags",
                            transaction_index=idx,
                            tag_count=len(tags_to_set),
                        )

                processed_transactions.append(transaction)
            except Exception as e:
                error_msg = f"Transaction {idx}: {str(e)}"
                errors.append(error_msg)
                logger.warning(
                    "Transaction processing error",
                    transaction_index=idx,
                    error=str(e),
                    transaction_type=transaction.transaction_type
                    if hasattr(transaction, "transaction_type")
                    else None,
                    amount=transaction.amount
                    if hasattr(transaction, "amount")
                    else None,
                )

        # If there are any errors, return them without saving anything
        if errors:
            logger.warning(
                "Transaction processing completed with validation errors",
                error_count=len(errors),
                processed_count=len(processed_transactions),
            )
            return {
                "success_count": 0,
                "error_count": len(errors),
                "errors": errors,
            }

        # If no errors, save all transactions in a single atomic transaction
        try:
            logger.info(
                "Saving transactions to database",
                transaction_count=len(processed_transactions),
            )

            with db_transaction.atomic():
                for transaction_obj in processed_transactions:
                    # Set origin from imported_report if available
                    if self.imported_report:
                        transaction_obj.origin = self.imported_report.file_name
                    else:
                        transaction_obj.origin = ""
                    transaction_obj.save()

                    # Set tags after saving (many-to-many relationships require saved object)
                    if hasattr(transaction_obj, "_tags_to_set"):  # type: ignore
                        tags_to_set = transaction_obj._tags_to_set  # type: ignore
                        transaction_obj.tags.set(tags_to_set)

            logger.info(
                "Successfully saved all transactions",
                success_count=len(processed_transactions),
            )

            return {
                "success_count": len(processed_transactions),
                "error_count": 0,
                "errors": [],
            }
        except Exception as e:
            # If any transaction fails during save, the entire transaction is rolled back
            logger.error(
                "Failed to save transactions",
                error=str(e),
                transaction_count=len(processed_transactions),
            )
            return {
                "success_count": 0,
                "error_count": len(processed_transactions),
                "errors": [f"Failed to save transactions: {str(e)}"],
            }

    def _extract_metadata(self, transaction: Transaction) -> dict[str, Any]:
        """Extract metadata from transaction in a format-agnostic way.

        Checks for attributes with any format prefix (_csv_*, _json_*, _xlsx_*)
        and returns a dictionary with normalized metadata.

        Args:
            transaction: Transaction object that may have format-specific attributes.

        Returns:
            Dictionary with extracted metadata:
            {
                "account_identifier": str | None,
                "credit_card_identifier": str | None,
                "category_name": str | None,
                "subcategory_name": str | None,
                "tags_value": str | list[str] | None
            }
        """
        metadata: dict[str, Any] = {
            "account_identifier": None,
            "credit_card_identifier": None,
            "category_name": None,
            "subcategory_name": None,
            "tags_value": None,
        }

        # Check for account identifier with any format prefix
        for prefix in ["_csv_", "_json_", "_xlsx_"]:
            attr_name = f"{prefix}account_identifier"
            if hasattr(transaction, attr_name):
                value = getattr(transaction, attr_name, None)
                if value:
                    metadata["account_identifier"] = value
                    break

        # Check for credit card identifier with any format prefix
        for prefix in ["_csv_", "_json_", "_xlsx_"]:
            attr_name = f"{prefix}credit_card_identifier"
            if hasattr(transaction, attr_name):
                value = getattr(transaction, attr_name, None)
                if value:
                    metadata["credit_card_identifier"] = value
                    break

        # Check for category name with any format prefix
        for prefix in ["_csv_", "_json_", "_xlsx_"]:
            attr_name = f"{prefix}category_name"
            if hasattr(transaction, attr_name):
                value = getattr(transaction, attr_name, None)
                if value:
                    metadata["category_name"] = value
                    break

        # Check for subcategory name with any format prefix
        for prefix in ["_csv_", "_json_", "_xlsx_"]:
            attr_name = f"{prefix}subcategory_name"
            if hasattr(transaction, attr_name):
                value = getattr(transaction, attr_name, None)
                if value:
                    metadata["subcategory_name"] = value
                    break

        # Check for tags value with any format prefix
        for prefix in ["_csv_", "_json_", "_xlsx_"]:
            attr_name = f"{prefix}tags_value"
            if hasattr(transaction, attr_name):
                value = getattr(transaction, attr_name, None)
                if value:
                    metadata["tags_value"] = value
                    break

        return metadata

    def _match_category_by_name(
        self, name: str, transaction_type: Category.TransactionType
    ) -> Category | None:
        """Match or create category by name.

        Args:
            name: Category name.
            transaction_type: Transaction type (INCOME/EXPENSE).

        Returns:
            Category instance (existing or newly created), or None if not found.
        """
        # Try to find existing category
        category = Category.objects.filter(
            user=self.user,
            name__iexact=name,
            transaction_type=transaction_type,
        ).first()

        if category:
            return category

        # Create new category if not found
        category = Category.objects.create(
            user=self.user,
            name=name,
            transaction_type=transaction_type,
        )

        return category

    def _match_subcategory_by_name(
        self, name: str, category: Category
    ) -> Subcategory | None:
        """Match or create subcategory by name.

        Args:
            name: Subcategory name.
            category: Parent category.

        Returns:
            Subcategory instance (existing or newly created), or None if not found.
        """
        subcategory = Subcategory.objects.filter(
            user=self.user,
            name__iexact=name,
            category=category,
        ).first()

        if subcategory:
            return subcategory

        subcategory = Subcategory.objects.create(
            user=self.user,
            name=name,
            category=category,
        )

        return subcategory

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

    def _match_tags(self, tag_names: str | list[str]) -> list[Tag]:
        """Match tags by name (create if not exists).

        Args:
            tag_names: Comma-separated tag names string or list of tag names.

        Returns:
            List of Tag instances.
        """
        tags: list[Tag] = []

        # Handle both string and list inputs
        if isinstance(tag_names, str):
            tag_name_list = [
                name.strip() for name in tag_names.split(",") if name.strip()
            ]
        elif isinstance(tag_names, list):
            tag_name_list = [str(name).strip() for name in tag_names if name]
        else:
            return tags

        for tag_name in tag_name_list:
            # Try to find existing tag
            tag = Tag.objects.filter(user=self.user, name__iexact=tag_name).first()

            if not tag:
                # Create new tag if not found
                tag = Tag.objects.create(user=self.user, name=tag_name)

            tags.append(tag)

        return tags
