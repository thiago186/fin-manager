from typing import Any

from rest_framework import serializers

from apps.accounts.models.account import Account
from apps.accounts.models.credit_card import CreditCard

ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".heic")
ALLOWED_IMAGE_CONTENT_TYPES = (
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
)


class PhotoImportSerializer(serializers.Serializer):
    """Serializer for photo import validation (multiple image files)."""

    photos = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=10,
        help_text="Image files of bank statements or receipts (1-10 files)",
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
    positive_as_expense = serializers.BooleanField(
        required=False,
        default=True,
        help_text="If true, positive amounts are treated as expenses (default behavior)",
    )

    def validate_photos(self, value: list) -> list:
        """Validate that all uploaded files are images with allowed extensions."""
        for photo in value:
            file_name_lower = photo.name.lower()
            if not file_name_lower.endswith(ALLOWED_IMAGE_EXTENSIONS):
                raise serializers.ValidationError(
                    f"File '{photo.name}' has an unsupported extension. "
                    f"Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
                )

            if hasattr(photo, "content_type") and photo.content_type:
                if not photo.content_type.startswith("image/"):
                    raise serializers.ValidationError(
                        f"File '{photo.name}' is not an image. "
                        f"Content type: {photo.content_type}"
                    )

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that account_id and credit_card_id are not both provided."""
        account_id = attrs.get("account_id")
        credit_card_id = attrs.get("credit_card_id")

        if account_id is not None and credit_card_id is not None:
            raise serializers.ValidationError(
                "Cannot specify both account_id and credit_card_id. "
                "A transaction can only be associated with either an account or a credit card."
            )

        return attrs

    def validate_account_id(self, value: int | None) -> int | None:
        """Validate that the account exists and belongs to the user."""
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
        """Validate that the credit card exists and belongs to the user."""
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
