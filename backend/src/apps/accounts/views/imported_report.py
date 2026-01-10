from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models.imported_report import ImportedReport
from apps.accounts.serializers.imported_report import ImportedReportSerializer


class ImportedReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing import reports."""

    serializer_class = ImportedReportSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["transactions"],
        summary="List import reports",
        description="List all CSV import reports for the authenticated user.",
    )
    def list(self, request, *args, **kwargs):
        """List user's import reports."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["transactions"],
        summary="Get import report",
        description="Get details of a specific CSV import report.",
    )
    def retrieve(self, request, *args, **kwargs):
        """Get specific import report."""
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        """Filter queryset to only include user's import reports."""
        return ImportedReport.objects.filter(user=self.request.user)

