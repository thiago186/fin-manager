import structlog
from celery import shared_task
from django.utils import timezone as dj_timezone

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


@shared_task
def process_photo_import_task(imported_report_id: int) -> None:
    """Celery task to process photo import asynchronously.

    Uses PhotoImportService to extract transactions from photos via a vision LLM,
    then saves them using TransactionProcessor.

    Args:
        imported_report_id: ID of the ImportedReport to process.
    """
    try:
        imported_report = ImportedReport.objects.get(id=imported_report_id)
        logger.info(
            "Starting photo import task",
            imported_report_id=imported_report_id,
            user_id=imported_report.user.pk,
            photo_count=len(imported_report.photo_paths or []),
        )

        imported_report.status = ImportedReport.Status.PROCESSING
        imported_report.save(update_fields=["status", "updated_at"])

        from apps.accounts.services.transaction_processor import TransactionProcessor
        from apps.ai.services.photo_import_service import PhotoImportService

        photo_service = PhotoImportService(user=imported_report.user)
        transactions = photo_service.extract_transactions(
            imported_report.photo_paths or []
        )

        if not transactions:
            imported_report.status = ImportedReport.Status.IMPORTED
            imported_report.success_count = 0
            imported_report.error_count = 0
            imported_report.handler_type = "PhotoImportService"
            imported_report.processed_at = dj_timezone.now()
            imported_report.save(
                update_fields=[
                    "status",
                    "success_count",
                    "error_count",
                    "handler_type",
                    "processed_at",
                    "updated_at",
                ]
            )
            logger.info(
                "Photo import completed with no transactions",
                imported_report_id=imported_report_id,
            )
            return

        # Set account/credit_card from imported_report onto transactions
        for txn in transactions:
            if imported_report.account:
                txn.account = imported_report.account
            if imported_report.credit_card:
                txn.credit_card = imported_report.credit_card

        processor = TransactionProcessor(
            user=imported_report.user, imported_report=imported_report
        )
        result = processor.process_transactions(transactions)

        imported_report.status = ImportedReport.Status.IMPORTED
        imported_report.success_count = result.get("success_count", 0)
        imported_report.error_count = result.get("error_count", 0)
        imported_report.errors = result.get("errors", [])
        imported_report.handler_type = "PhotoImportService"
        imported_report.processed_at = dj_timezone.now()

        if imported_report.success_count == 0 and imported_report.error_count > 0:
            imported_report.status = ImportedReport.Status.FAILED
            imported_report.failed_reason = (
                f"All {imported_report.error_count} transactions failed to import"
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
            "Photo import task completed",
            imported_report_id=imported_report_id,
            success_count=imported_report.success_count,
            error_count=imported_report.error_count,
        )
    except ImportedReport.DoesNotExist:
        logger.error(
            "ImportedReport not found in photo import task",
            imported_report_id=imported_report_id,
        )
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error in photo import task",
            imported_report_id=imported_report_id,
            error=str(e),
        )
        try:
            imported_report = ImportedReport.objects.get(id=imported_report_id)
            imported_report.status = ImportedReport.Status.FAILED
            imported_report.failed_reason = str(e)
            imported_report.processed_at = dj_timezone.now()
            imported_report.save(
                update_fields=[
                    "status",
                    "failed_reason",
                    "processed_at",
                    "updated_at",
                ]
            )
        except Exception:
            pass
        raise
