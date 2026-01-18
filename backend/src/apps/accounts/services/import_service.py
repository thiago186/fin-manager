from datetime import datetime
from typing import Any, Union

import structlog
from django.contrib.auth.models import User

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.interfaces.json_handler import BaseJsonHandler
from apps.accounts.interfaces.xlsx_handler import BaseXlsxHandler
from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.services.csv_import_factory import CSVImportFactory
from apps.accounts.services.file_storage_service import get_file_storage_service
from apps.accounts.services.json_import_factory import JSONImportFactory
from apps.accounts.services.transaction_processor import TransactionProcessor
from apps.accounts.services.xlsx_import_factory import XLSXImportFactory

logger = structlog.stdlib.get_logger()


class ImportService:
    """Service for importing transactions from CSV, JSON, or XLSX files.

    This service handles all file formats by:
    - Detecting file format from extension
    - Using appropriate factory to select handler
    - Parsing transactions from file
    - Processing transactions with TransactionProcessor
    """

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
        """Import transactions from CSV, JSON, or XLSX file.

        Args:
            file_path: Path to the CSV, JSON, or XLSX file.
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

        file_format = self._detect_file_format(file_path)
        factory = self._get_factory_for_format(file_format)

        handler: Union[BaseCSVHandler, BaseJsonHandler, BaseXlsxHandler] = (
            factory.create_handler(file_path)
        )
        handler_type = type(handler).__name__

        format_name = file_format.upper()

        logger.info(
            f"Handler selected for {format_name} import",
            handler_type=handler_type,
            file_path=file_path,
            file_format=file_format,
        )

        transactions = handler.parse_transactions_from_file(file_path, self.user)

        logger.info(
            f"Parsed transactions from {format_name}",
            transaction_count=len(transactions),
            handler_type=handler_type,
        )

        processor = TransactionProcessor(self.user, imported_report)
        result = processor.process_transactions(transactions)
        result["handler_type"] = handler_type

        logger.info(
            "Transaction import completed",
            success_count=result["success_count"],
            error_count=result["error_count"],
            handler_type=handler_type,
        )

        return result

    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from file path.

        Args:
            file_path: Path to the file.

        Returns:
            File format string: "csv", "json", or "xlsx".
        """
        file_path_lower = file_path.lower()

        if file_path_lower.endswith(".xlsx"):
            return "xlsx"
        elif file_path_lower.endswith(".json"):
            return "json"
        elif file_path_lower.endswith(".csv"):
            return "csv"
        else:
            # Default to CSV for backward compatibility
            logger.warning(
                "Unknown file extension, defaulting to CSV",
                file_path=file_path,
            )
            return "csv"

    def _get_factory_for_format(self, file_format: str):
        """Get the appropriate factory for the file format.

        Args:
            file_format: File format string ("csv", "json", or "xlsx").

        Returns:
            Appropriate factory instance (CSVImportFactory, JSONImportFactory, or XLSXImportFactory).
        """
        if file_format == "json":
            return JSONImportFactory
        elif file_format == "xlsx":
            return XLSXImportFactory
        else:
            # Default to CSV factory
            return CSVImportFactory
