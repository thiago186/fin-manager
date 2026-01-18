from typing import Any

from rest_framework import serializers

from apps.accounts.models.account import Account
from apps.accounts.models.credit_card import CreditCard


class CSVImportSerializer(serializers.Serializer):
    """Serializer for CSV, JSON, or XLSX file upload validation."""

    file = serializers.FileField(
        help_text="CSV, JSON, or XLSX file containing transactions to import"
    )
    account_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the bank account to associate with all imported transactions",
    )
    credit_card_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of the credit card to associate with all imported transactions",
    )

    def validate_file(self, value: Any) -> Any:
        """Validate that the uploaded file is a CSV, JSON, or XLSX file.

        Args:
            value: Uploaded file.

        Returns:
            Validated file.

        Raises:
            serializers.ValidationError: If file is not a CSV, JSON, or XLSX file.
        """
        file_name_lower = value.name.lower()

        if not (file_name_lower.endswith(".csv") or file_name_lower.endswith(".json") or file_name_lower.endswith(".xlsx")):
            raise serializers.ValidationError(
                "File must be a CSV file (.csv extension), JSON file (.json extension), or XLSX file (.xlsx extension)"
            )

        if hasattr(value, "content_type"):
            content_type = value.content_type
            csv_content_types = [
                "text/csv",
                "application/csv",
                "text/plain",
                "application/vnd.ms-excel",
            ]
            json_content_types = [
                "application/json",
                "text/json",
            ]
            xlsx_content_types = [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "application/xlsx",
            ]

            if content_type not in csv_content_types + json_content_types + xlsx_content_types:
                raise serializers.ValidationError(
                    f"Invalid file type: {content_type}. Expected CSV, JSON, or XLSX file."
                )

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that account_id and credit_card_id are not both provided.

        Args:
            attrs: Dictionary of validated attributes.

        Returns:
            Validated attributes.

        Raises:
            serializers.ValidationError: If both account_id and credit_card_id are provided.
        """
        account_id = attrs.get("account_id")
        credit_card_id = attrs.get("credit_card_id")

        if account_id is not None and credit_card_id is not None:
            raise serializers.ValidationError(
                "Cannot specify both account_id and credit_card_id. "
                "A transaction can only be associated with either an account or a credit card."
            )

        return attrs

    def validate_account_id(self, value: int | None) -> int | None:
        """Validate that the account exists and belongs to the user.

        Args:
            value: Account ID.

        Returns:
            Validated account ID.

        Raises:
            serializers.ValidationError: If account does not exist or does not belong to user.
        """
        if value is None:
            return value

        user = self.context.get("request").user  # type: ignore
        try:
            account = Account.objects.get(id=value, user=user)
            return account.id
        except Account.DoesNotExist:
            raise serializers.ValidationError(
                f"Account with ID {value} does not exist or does not belong to you."
            )

    def validate_credit_card_id(self, value: int | None) -> int | None:
        """Validate that the credit card exists and belongs to the user.

        Args:
            value: Credit card ID.

        Returns:
            Validated credit card ID.

        Raises:
            serializers.ValidationError: If credit card does not exist or does not belong to user.
        """
        if value is None:
            return value

        user = self.context.get("request").user  # type: ignore
        try:
            credit_card = CreditCard.objects.get(id=value, user=user)
            return credit_card.id
        except CreditCard.DoesNotExist:
            raise serializers.ValidationError(
                f"Credit card with ID {value} does not exist or does not belong to you."
            )


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
