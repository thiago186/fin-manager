import structlog

from celery import shared_task

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.services.csv_import_service import CSVImportService

logger = structlog.stdlib.get_logger()


@shared_task
def process_csv_import_task(imported_report_id: int) -> None:
    """Celery task to process CSV import asynchronously.

    This is a thin wrapper that instantiates CSVImportService and calls
    process_import_report(). All business logic lives in the service.

    Args:
        imported_report_id: ID of the ImportedReport to process.
    """
    try:
        imported_report = ImportedReport.objects.get(id=imported_report_id)
        logger.info(
            "Starting CSV import task",
            imported_report_id=imported_report_id,
            user_id=imported_report.user.pk,
        )

        service = CSVImportService(user=imported_report.user)
        service.process_import_report(imported_report_id)

        logger.info(
            "CSV import task completed",
            imported_report_id=imported_report_id,
        )
    except ImportedReport.DoesNotExist:
        logger.error(
            "ImportedReport not found in task",
            imported_report_id=imported_report_id,
        )
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error in CSV import task",
            imported_report_id=imported_report_id,
            error=str(e),
        )
        raise
