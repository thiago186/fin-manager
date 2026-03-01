from typing import Any

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.serializers.photo_import import PhotoImportSerializer
from apps.accounts.services.file_storage_service import get_file_storage_service
from apps.accounts.tasks import process_photo_import_task  # type: ignore


class PhotoImportView(APIView):
    """API view for importing transactions from photos of bank statements or receipts."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle photo upload and trigger async photo import."""
        serializer = PhotoImportSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        photos = serializer.validated_data["photos"]
        account_id = serializer.validated_data.get("account_id")
        credit_card_id = serializer.validated_data.get("credit_card_id")
        positive_as_expense = serializer.validated_data.get("positive_as_expense", True)

        try:
            storage_service = get_file_storage_service()
            photo_paths = []

            for photo in photos:
                path = storage_service.save_file(
                    photo,
                    photo.name,
                    request.user.id,  # type: ignore
                )
                photo_paths.append(path)

            file_name = f"photo_import_{len(photos)}_images"

            imported_report = ImportedReport.objects.create(
                user=request.user,
                status=ImportedReport.Status.SENT,
                file_name=file_name,
                file_path=photo_paths[0],
                photo_paths=photo_paths,
                account_id=account_id,
                credit_card_id=credit_card_id,
                positive_as_expense=positive_as_expense,
            )

            process_photo_import_task.delay(imported_report.id)

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
                {"error": f"Error processing photo upload: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
