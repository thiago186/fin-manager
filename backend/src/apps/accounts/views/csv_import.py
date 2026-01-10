from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.serializers.csv_import import CSVImportSerializer
from apps.accounts.services.file_storage_service import get_file_storage_service
from apps.accounts.tasks import process_import_task  # type: ignore


class CSVImportView(APIView):
    """API view for importing transactions from CSV or JSON files."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]

    @extend_schema(
        tags=["transactions"],
        summary="Import transactions from CSV or JSON",
        description=(
            "Import transactions from a CSV or JSON file asynchronously. "
            "For CSV files, the format is auto-detected based on column headers. "
            "For JSON files, the format should be an array of transaction objects with fields: name, date, total, and optionally current_installment, total_installments. "
            "Categories and subcategories are matched by name and created if they don't exist. "
            "Accounts and credit cards are matched by name or ID (must exist). "
            "Tags are matched by name and created if they don't exist. "
            "Optionally specify account_id or credit_card_id to associate all imported transactions with a specific account or credit card. "
            "The import is processed asynchronously. Use the returned report_id to check status via the import-reports endpoint."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "CSV or JSON file containing transactions",
                    },
                    "account_id": {
                        "type": "integer",
                        "description": "Optional: ID of the bank account to associate with all imported transactions",
                    },
                    "credit_card_id": {
                        "type": "integer",
                        "description": "Optional: ID of the credit card to associate with all imported transactions",
                    },
                },
                "required": ["file"],
            }
        },
        responses={
            202: {
                "description": "Import request accepted",
                "type": "object",
                "properties": {
                    "report_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "status_url": {"type": "string"},
                },
            },
            400: {"description": "Invalid file or request"},
        },
        examples=[
            OpenApiExample(
                "Accepted Response",
                value={
                    "report_id": 1,
                    "status": "SENT",
                    "status_url": "/api/v1/finance/import-reports/1/",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle CSV or JSON file upload and trigger async import.

        Args:
            request: The HTTP request containing the CSV or JSON file.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with report_id and status endpoint (202 Accepted).
        """
        serializer = CSVImportSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file = serializer.validated_data["file"]
        account_id = serializer.validated_data.get("account_id")
        credit_card_id = serializer.validated_data.get("credit_card_id")

        try:
            storage_service = get_file_storage_service()
            file_path = storage_service.save_file(
                file,
                file.name,
                request.user.id,  # type: ignore
            )

            imported_report = ImportedReport.objects.create(
                user=request.user,
                status=ImportedReport.Status.SENT,
                file_name=file.name,
                file_path=file_path,
                account_id=account_id,
                credit_card_id=credit_card_id,
            )

            process_import_task.delay(imported_report.id)

            return Response(
                {
                    "report_id": imported_report.id,
                    "status": imported_report.status,
                    "status_url": f"/api/v1/finance/import-reports/{imported_report.id}/",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return Response(
                {"error": f"Error processing file upload: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
