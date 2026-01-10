import structlog

from celery import shared_task

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.services.import_service import ImportService

logger = structlog.stdlib.get_logger()


@shared_task
def process_import_task(imported_report_id: int) -> None:
    """Celery task to process CSV or JSON import asynchronously.

    This is a thin wrapper that instantiates ImportService and calls
    process_import_report(). All business logic lives in the service.

    Args:
        imported_report_id: ID of the ImportedReport to process.
    """
    try:
        imported_report = ImportedReport.objects.get(id=imported_report_id)
        logger.info(
            "Starting import task",
            imported_report_id=imported_report_id,
            user_id=imported_report.user.pk,
            file_name=imported_report.file_name,
        )

        service = ImportService(user=imported_report.user)
        service.process_import_report(imported_report_id)

        logger.info(
            "Import task completed",
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
            "Unexpected error in import task",
            imported_report_id=imported_report_id,
            error=str(e),
        )
        raise


# Keep backward compatibility alias
process_csv_import_task = process_import_task
