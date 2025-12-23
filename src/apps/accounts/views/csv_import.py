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
from apps.accounts.tasks import process_csv_import_task


class CSVImportView(APIView):
    """API view for importing transactions from CSV files."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]

    @extend_schema(
        tags=["transactions"],
        summary="Import transactions from CSV",
        description=(
            "Import transactions from a CSV file asynchronously. The CSV format is auto-detected based on column headers. "
            "Categories and subcategories are matched by name and created if they don't exist. "
            "Accounts and credit cards are matched by name or ID (must exist). "
            "Tags are matched by name and created if they don't exist. "
            "The import is processed asynchronously. Use the returned report_id to check status via the import-reports endpoint."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "CSV file containing transactions",
                    }
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
        """Handle CSV file upload and trigger async import.

        Args:
            request: The HTTP request containing the CSV file.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with report_id and status endpoint (202 Accepted).
        """
        serializer = CSVImportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        csv_file = serializer.validated_data["file"]

        try:
            storage_service = get_file_storage_service()
            file_path = storage_service.save_file(
                csv_file,
                csv_file.name,
                request.user.id,  # type: ignore
            )

            imported_report = ImportedReport.objects.create(
                user=request.user,
                status=ImportedReport.Status.SENT,
                file_name=csv_file.name,
                file_path=file_path,
            )

            process_csv_import_task.delay(imported_report.id)

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
                {"error": f"Error processing CSV file upload: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
