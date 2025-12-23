from rest_framework import serializers

from apps.accounts.models.imported_report import ImportedReport


class ImportedReportSerializer(serializers.ModelSerializer):
    """Serializer for ImportedReport model."""

    class Meta:
        """Meta options for ImportedReportSerializer."""

        model = ImportedReport
        fields = [
            "id",
            "status",
            "file_name",
            "file_path",
            "handler_type",
            "failed_reason",
            "success_count",
            "error_count",
            "errors",
            "created_at",
            "updated_at",
            "processed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "file_path",
            "handler_type",
            "failed_reason",
            "success_count",
            "error_count",
            "errors",
            "created_at",
            "updated_at",
            "processed_at",
        ]

