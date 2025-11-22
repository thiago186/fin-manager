from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers.csv_import import (
    CSVImportResultSerializer,
    CSVImportSerializer,
)
from apps.accounts.services.csv_import_service import CSVImportService


class CSVImportView(APIView):
    """API view for importing transactions from CSV files."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]

    @extend_schema(
        tags=["transactions"],
        summary="Import transactions from CSV",
        description=(
            "Import transactions from a CSV file. The CSV format is auto-detected based on column headers. "
            "Categories and subcategories are matched by name and created if they don't exist. "
            "Accounts and credit cards are matched by name or ID (must exist). "
            "Tags are matched by name and created if they don't exist."
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
            200: CSVImportResultSerializer,
            400: {"description": "Invalid file or request"},
        },
        examples=[
            OpenApiExample(
                "Success Response",
                value={
                    "success_count": 10,
                    "error_count": 2,
                    "errors": [
                        "Transaction 5: Invalid date format: 2024-13-01",
                        "Transaction 8: Missing required field: amount",
                    ],
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle CSV file upload and import transactions.

        Args:
            request: The HTTP request containing the CSV file.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response with import results (success count, error count, errors).
        """
        serializer = CSVImportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        csv_file = serializer.validated_data["file"]

        try:
            # Create import service and process file
            import_service = CSVImportService(user=request.user)
            result = import_service.import_transactions(csv_file)

            # Serialize and return results
            result_serializer = CSVImportResultSerializer(data=result)
            result_serializer.is_valid()

            return Response(result_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error importing CSV file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

