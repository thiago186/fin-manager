from datetime import datetime
from typing import Any

import structlog
from django.contrib.auth.models import User
from django.db import transaction as db_transaction

from apps.accounts.interfaces.xlsx_handler import BaseXlsxHandler
from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction
from apps.accounts.models.transaction_tag import Tag
from apps.accounts.services.file_storage_service import get_file_storage_service
from apps.accounts.services.xlsx_import_factory import XLSXImportFactory

logger = structlog.stdlib.get_logger()


class XLSXImportService:
    """Service for importing transactions from XLSX files."""

    def __init__(self, user: User):
        """Initialize the import service.

        Args:
            user: The user who owns the transactions to be imported.
        """
        self.user = user
        self.storage_service = get_file_storage_service()

    def process_import_report(self, imported_report_id: int) -> None:
        """Process import report asynchronously.

        This method handles all business logic for processing an import report:
        - Updates status to PROCESSING
        - Retrieves file from storage
        - Processes transactions
        - Updates report with results
        - Handles errors and updates status accordingly

        Args:
            imported_report_id: ID of the ImportedReport to process.
        """
        try:
            imported_report = ImportedReport.objects.get(
                id=imported_report_id, user=self.user
            )
        except ImportedReport.DoesNotExist:
            logger.error(
                "ImportedReport not found",
                imported_report_id=imported_report_id,
                user_id=self.user.id,  # type: ignore
            )
            raise

        file_format = self._detect_file_format(imported_report.file_name)

        logger.info(
            "Starting import processing",
            imported_report_id=imported_report_id,
            file_name=imported_report.file_name,
            file_path=imported_report.file_path,
            file_format=file_format,
            user_id=self.user.id,  # type: ignore
        )

        try:
            imported_report.status = ImportedReport.Status.PROCESSING
            imported_report.save(update_fields=["status", "updated_at"])

            logger.info(
                "Updated import report status to PROCESSING",
                imported_report_id=imported_report_id,
            )

            file_path = self.storage_service.get_file_path(imported_report.file_path)

            result = self.import_transactions(
                file_path, imported_report=imported_report
            )

            handler_type = result.get("handler_type", "")

            imported_report.success_count = result["success_count"]
            imported_report.error_count = result["error_count"]
            imported_report.errors = result["errors"]
            imported_report.handler_type = handler_type
            imported_report.processed_at = datetime.now()

            if result["error_count"] == 0 and result["success_count"] > 0:
                imported_report.status = ImportedReport.Status.IMPORTED
                logger.info(
                    "Import completed successfully",
                    imported_report_id=imported_report_id,
                    success_count=result["success_count"],
                    handler_type=handler_type,
                )
            elif result["error_count"] > 0:
                imported_report.status = ImportedReport.Status.FAILED
                imported_report.failed_reason = (
                    f"Import completed with {result['error_count']} errors. "
                    f"See errors list for details."
                )
                logger.warning(
                    "Import completed with errors",
                    imported_report_id=imported_report_id,
                    success_count=result["success_count"],
                    error_count=result["error_count"],
                    handler_type=handler_type,
                )
            else:
                imported_report.status = ImportedReport.Status.FAILED
                imported_report.failed_reason = "No transactions were imported"
                logger.warning(
                    "Import completed with no transactions",
                    imported_report_id=imported_report_id,
                    handler_type=handler_type,
                )

            imported_report.save(
                update_fields=[
                    "status",
                    "success_count",
                    "error_count",
                    "errors",
                    "handler_type",
                    "failed_reason",
                    "processed_at",
                    "updated_at",
                ]
            )

            logger.info(
                "Updated import report with results",
                imported_report_id=imported_report_id,
                status=imported_report.status,
            )

        except Exception as e:
            logger.exception(
                "Error processing import report",
                imported_report_id=imported_report_id,
                error=str(e),
                user_id=self.user.id,  # type: ignore
            )

            imported_report.status = ImportedReport.Status.FAILED
            imported_report.failed_reason = str(e)
            imported_report.processed_at = datetime.now()
            imported_report.save(
                update_fields=[
                    "status",
                    "failed_reason",
                    "processed_at",
                    "updated_at",
                ]
            )

            raise

    def import_transactions(
        self, file_path: str, imported_report: ImportedReport | None = None
    ) -> dict[str, Any]:
        """Import transactions from XLSX file.

        Args:
            file_path: Path to the XLSX file.
            imported_report: Optional ImportedReport instance with account/credit_card association.

        Returns:
            Dictionary with import results:
            {
                "success_count": int,
                "error_count": int,
                "errors": list[str],
                "handler_type": str
            }
        """
        logger.info(
            "Starting transaction import",
            file_path=file_path,
            user_id=self.user.id,  # type: ignore
        )

        handler: BaseXlsxHandler = XLSXImportFactory.create_handler(file_path)
        handler_type = type(handler).__name__

        logger.info(
            "Handler selected for XLSX import",
            handler_type=handler_type,
            file_path=file_path,
        )

        transactions = handler.parse_transactions_from_file(file_path, self.user)

        logger.info(
            "Parsed transactions from XLSX",
            transaction_count=len(transactions),
            handler_type=handler_type,
        )

        result = self._process_transactions(
            transactions, imported_report=imported_report
        )
        result["handler_type"] = handler_type

        logger.info(
            "Transaction import completed",
            success_count=result["success_count"],
            error_count=result["error_count"],
            handler_type=handler_type,
        )

        return result

    def _process_transactions(
        self,
        transactions: list[Transaction],
        imported_report: ImportedReport | None = None,
    ) -> dict[str, Any]:
        """Process and save transactions with matching logic.

        All transactions are processed in a single database transaction.
        If any transaction fails validation or saving, the entire import is rolled back.
        All errors are collected and returned so the user can fix them at once.

        Args:
            transactions: List of parsed Transaction objects.
            imported_report: Optional ImportedReport instance with account/credit_card association.

        Returns:
            Dictionary with import results.
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
        report_account = imported_report.account if imported_report else None
        report_credit_card = imported_report.credit_card if imported_report else None

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

                # Match account if identifier provided in file
                account_identifier = None
                if (
                    hasattr(transaction, "_xlsx_account_identifier")
                    and transaction._xlsx_account_identifier
                ):  # type: ignore
                    account_identifier = transaction._xlsx_account_identifier  # type: ignore

                if account_identifier:
                    account = self._match_account(account_identifier)
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
                credit_card_identifier = None
                if (
                    hasattr(transaction, "_xlsx_credit_card_identifier")
                    and transaction._xlsx_credit_card_identifier
                ):  # type: ignore
                    credit_card_identifier = transaction._xlsx_credit_card_identifier  # type: ignore

                if credit_card_identifier:
                    credit_card = self._match_credit_card(credit_card_identifier)
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
                category_name = None
                if (
                    hasattr(transaction, "_xlsx_category_name")
                    and transaction._xlsx_category_name
                ):  # type: ignore
                    category_name = transaction._xlsx_category_name  # type: ignore

                if category_name:
                    # Convert Transaction.TransactionType to Category.TransactionType
                    transaction_type_str = transaction.transaction_type.lower()
                    category_transaction_type = (
                        Category.TransactionType.INCOME
                        if transaction_type_str == "income"
                        else Category.TransactionType.EXPENSE
                    )
                    category = self._match_category_by_name(
                        category_name,
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

                subcategory_name = None
                if (
                    hasattr(transaction, "_xlsx_subcategory_name")
                    and transaction._xlsx_subcategory_name
                ):  # type: ignore
                    subcategory_name = transaction._xlsx_subcategory_name  # type: ignore

                if subcategory_name:
                    parent_category = transaction.category
                    if not parent_category:
                        error_msg = f"Transaction {idx}: Cannot set subcategory without category"
                        errors.append(error_msg)
                        logger.warning(
                            "Cannot set subcategory without category",
                            transaction_index=idx,
                        )
                    else:
                        subcategory = self._match_subcategory_by_name(
                            subcategory_name,
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
                tags_to_set: list[Tag] = []
                tags_value = None
                if (
                    hasattr(transaction, "_xlsx_tags_value")
                    and transaction._xlsx_tags_value
                ):  # type: ignore
                    tags_value = transaction._xlsx_tags_value  # type: ignore

                if tags_value:
                    tags_to_set = self._match_tags(tags_value)
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
                    if imported_report:
                        transaction_obj.origin = imported_report.file_name
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

    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from file path.

        Args:
            file_path: Path to the file.

        Returns:
            File format string: "xlsx".
        """
        return "xlsx"
