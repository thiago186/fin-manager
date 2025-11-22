from typing import Any

from rest_framework import serializers


class CSVImportSerializer(serializers.Serializer):
    """Serializer for CSV file upload validation."""

    file = serializers.FileField(help_text="CSV file containing transactions to import")

    def validate_file(self, value: Any) -> Any:
        """Validate that the uploaded file is a CSV file.

        Args:
            value: Uploaded file.

        Returns:
            Validated file.

        Raises:
            serializers.ValidationError: If file is not a CSV file.
        """
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError(
                "File must be a CSV file (.csv extension)"
            )

        if hasattr(value, "content_type"):
            content_type = value.content_type
            if content_type not in [
                "text/csv",
                "application/csv",
                "text/plain",
                "application/vnd.ms-excel",
            ]:
                raise serializers.ValidationError(
                    f"Invalid file type: {content_type}. Expected CSV file."
                )

        return value


class CSVImportResultSerializer(serializers.Serializer):
    """Serializer for CSV import results."""

    success_count = serializers.IntegerField(
        help_text="Number of successfully imported transactions"
    )
    error_count = serializers.IntegerField(help_text="Number of failed transactions")
    errors = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of error messages for failed transactions",
    )
