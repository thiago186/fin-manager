from typing import Any

from django.contrib.auth.models import User

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.services.csv_import_service import CSVImportService
from apps.accounts.services.xlsx_import_service import XLSXImportService


class ImportService:
    """Generic service for importing transactions from CSV, JSON, or XLSX files.

    This is a thin wrapper that routes to the appropriate import service based on file format.
    """

    def __init__(self, user: User):
        """Initialize the import service.

        Args:
            user: The user who owns the transactions to be imported.
        """
        self.user = user
        self._csv_service = CSVImportService(user)
        self._xlsx_service = XLSXImportService(user)

    def _get_service_for_file(self, file_path: str):
        """Get the appropriate import service based on file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Appropriate import service instance.
        """
        file_path_lower = file_path.lower()
        if file_path_lower.endswith(".xlsx"):
            return self._xlsx_service
        else:
            # Default to CSV service for CSV and JSON files
            return self._csv_service

    def process_import_report(self, imported_report_id: int) -> None:
        """Process import report asynchronously.

        Args:
            imported_report_id: ID of the ImportedReport to process.
        """
        # Need to get the file path to determine which service to use
        imported_report = ImportedReport.objects.get(id=imported_report_id, user=self.user)
        service = self._get_service_for_file(imported_report.file_name)
        service.process_import_report(imported_report_id)

    def import_transactions(
        self, file_path: str, imported_report: ImportedReport | None = None
    ) -> dict[str, Any]:
        """Import transactions from file.

        Args:
            file_path: Path to the file.
            imported_report: Optional ImportedReport instance with account/credit_card association.

        Returns:
            Dictionary with import results.
        """
        service = self._get_service_for_file(file_path)
        return service.import_transactions(file_path, imported_report)
