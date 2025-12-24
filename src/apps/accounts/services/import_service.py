from typing import Any

from django.contrib.auth.models import User

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.services.csv_import_service import CSVImportService


class ImportService:
    """Generic service for importing transactions from CSV or JSON files.

    This is a thin wrapper around CSVImportService which now handles both formats.
    """

    def __init__(self, user: User):
        """Initialize the import service.

        Args:
            user: The user who owns the transactions to be imported.
        """
        self.user = user
        self._service = CSVImportService(user)

    def process_import_report(self, imported_report_id: int) -> None:
        """Process import report asynchronously.

        Args:
            imported_report_id: ID of the ImportedReport to process.
        """
        self._service.process_import_report(imported_report_id)

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
        return self._service.import_transactions(file_path, imported_report)
