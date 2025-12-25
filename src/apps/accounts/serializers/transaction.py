from typing import Any, cast

from rest_framework import serializers

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.transaction import Transaction
from apps.accounts.models.transaction_tag import Tag
from apps.accounts.serializers import (
    AccountSerializer,
    CategoryListSerializer,
    CreditCardSerializer,
    SubcategoryListSerializer,
    TagSerializer,
)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model with validation rules."""

    account = AccountSerializer(read_only=True)
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="account",
        required=False,
        allow_null=True,
        write_only=True,
    )

    credit_card = CreditCardSerializer(read_only=True)
    credit_card_id = serializers.PrimaryKeyRelatedField(
        queryset=CreditCard.objects.all(),
        source="credit_card",
        required=False,
        allow_null=True,
        write_only=True,
    )

    category = CategoryListSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
        required=False,
        allow_null=True,
        write_only=True,
    )

    subcategory = SubcategoryListSerializer(read_only=True)
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=Subcategory.objects.filter(is_active=True),
        source="subcategory",
        required=False,
        allow_null=True,
        write_only=True,
    )

    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "transaction_type",
            "amount",
            "description",
            "occurred_at",
            "installments_total",
            "installment_number",
            "installment_group_id",
            "created_at",
            "updated_at",
            "account",
            "account_id",
            "credit_card",
            "credit_card_id",
            "category",
            "category_id",
            "subcategory",
            "subcategory_id",
            "tags",
            "tag_ids",
            "need_review",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "installment_group_id"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate transaction data according to business rules."""
        account = attrs.get("account")
        credit_card = attrs.get("credit_card")

        if account and credit_card:
            raise serializers.ValidationError(
                "A transaction cannot be associated with both an account and a credit card. "
                "Please choose either an account or a credit card."
            )

        installments_total = attrs.get("installments_total", 1)
        installment_number = attrs.get("installment_number", 1)

        if installments_total > 1 or installment_number > 1:
            if installments_total <= 0:
                raise serializers.ValidationError(
                    "installments_total must be greater than 0."
                )

            if installment_number <= 0:
                raise serializers.ValidationError(
                    "installment_number must be greater than 0."
                )

            if installment_number > installments_total:
                raise serializers.ValidationError(
                    f"installment_number ({installment_number}) cannot be greater than "
                    f"installments_total ({installments_total})."
                )

        category = attrs.get("category")
        subcategory = attrs.get("subcategory")

        if category and subcategory:
            if subcategory.category != category:
                raise serializers.ValidationError(
                    "Subcategory must belong to the selected category."
                )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Transaction:
        """Create a new transaction with automatic user assignment."""
        validated_data["user"] = self.context["request"].user
        return cast(Transaction, super().create(validated_data))


class BulkTransactionUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating multiple transactions."""

    id = serializers.IntegerField(help_text="Transaction ID to update")
    transaction_type = serializers.ChoiceField(
        choices=Transaction.TransactionType.choices,
        required=False,
        allow_null=True,
    )
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    occurred_at = serializers.DateField(required=False, allow_null=True)
    account_id = serializers.IntegerField(required=False, allow_null=True)
    credit_card_id = serializers.IntegerField(required=False, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_null=True,
    )
    installments_total = serializers.IntegerField(
        min_value=1, required=False, allow_null=True
    )
    installment_number = serializers.IntegerField(
        min_value=1, required=False, allow_null=True
    )

    def validate_account_id(self, value: int | None) -> int | None:
        """Validate that account_id exists if provided."""
        if value is not None:
            if not Account.objects.filter(id=value).exists():
                raise serializers.ValidationError(
                    f"Account with id {value} does not exist."
                )
        return value

    def validate_credit_card_id(self, value: int | None) -> int | None:
        """Validate that credit_card_id exists if provided."""
        if value is not None:
            if not CreditCard.objects.filter(id=value).exists():
                raise serializers.ValidationError(
                    f"Credit card with id {value} does not exist."
                )
        return value

    def validate_category_id(self, value: int | None) -> int | None:
        """Validate that category_id exists and is active if provided."""
        if value is not None:
            category = Category.objects.filter(id=value, is_active=True).first()
            if not category:
                raise serializers.ValidationError(
                    f"Category with id {value} does not exist or is not active."
                )
        return value

    def validate_subcategory_id(self, value: int | None) -> int | None:
        """Validate that subcategory_id exists and is active if provided."""
        if value is not None:
            subcategory = Subcategory.objects.filter(id=value, is_active=True).first()
            if not subcategory:
                raise serializers.ValidationError(
                    f"Subcategory with id {value} does not exist or is not active."
                )
        return value

    def validate_tag_ids(self, value: list[int] | None) -> list[int] | None:
        """Validate that all tag_ids exist if provided."""
        if value is not None:
            existing_tag_ids = set(
                Tag.objects.filter(id__in=value).values_list("id", flat=True)
            )
            missing_ids = set(value) - existing_tag_ids
            if missing_ids:
                raise serializers.ValidationError(
                    f"Tags with ids {list(missing_ids)} do not exist."
                )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate transaction update data according to business rules."""
        account_id = attrs.get("account_id")
        credit_card_id = attrs.get("credit_card_id")

        if account_id is not None and credit_card_id is not None:
            raise serializers.ValidationError(
                "A transaction cannot be associated with both an account and a credit card. "
                "Please choose either an account or a credit card."
            )

        installments_total = attrs.get("installments_total")
        installment_number = attrs.get("installment_number")

        if installments_total is not None:
            if installments_total <= 0:
                raise serializers.ValidationError(
                    "installments_total must be greater than 0."
                )

        if installment_number is not None:
            if installment_number <= 0:
                raise serializers.ValidationError(
                    "installment_number must be greater than 0."
                )

        if installments_total is not None and installment_number is not None:
            if installment_number > installments_total:
                raise serializers.ValidationError(
                    f"installment_number ({installment_number}) cannot be greater than "
                    f"installments_total ({installments_total})."
                )

        category_id = attrs.get("category_id")
        subcategory_id = attrs.get("subcategory_id")

        if category_id is not None and subcategory_id is not None:
            subcategory = Subcategory.objects.filter(
                id=subcategory_id, is_active=True
            ).first()
            if subcategory and subcategory.category.id != category_id:
                raise serializers.ValidationError(
                    "Subcategory must belong to the selected category."
                )

        return attrs

    def update_transaction(self, transaction: Transaction) -> Transaction:
        """Update a transaction instance with validated data.

        Args:
            transaction: The transaction instance to update

        Returns:
            The updated transaction instance

        Raises:
            ValidationError: If the transaction validation fails
        """
        validated_data = self.validated_data.copy()
        validated_data.pop("id", None)

        if "account_id" in validated_data:
            account_id = validated_data.pop("account_id")
            if account_id is not None:
                transaction.account = Account.objects.get(id=account_id)
            else:
                transaction.account = None

        if "credit_card_id" in validated_data:
            credit_card_id = validated_data.pop("credit_card_id")
            if credit_card_id is not None:
                transaction.credit_card = CreditCard.objects.get(id=credit_card_id)
            else:
                transaction.credit_card = None

        if "category_id" in validated_data:
            category_id = validated_data.pop("category_id")
            if category_id is not None:
                transaction.category = Category.objects.get(id=category_id)
            else:
                transaction.category = None

        if "subcategory_id" in validated_data:
            subcategory_id = validated_data.pop("subcategory_id")
            if subcategory_id is not None:
                transaction.subcategory = Subcategory.objects.get(id=subcategory_id)
            else:
                transaction.subcategory = None

        if "tag_ids" in validated_data:
            tag_ids = validated_data.pop("tag_ids")
            if tag_ids is not None:
                tags = Tag.objects.filter(id__in=tag_ids)
                transaction.tags.set(tags)
            else:
                transaction.tags.clear()

        for field, value in validated_data.items():
            setattr(transaction, field, value)

        transaction.full_clean()
        transaction.save()

        return transaction


class BulkTransactionUpdateRequestSerializer(serializers.Serializer):
    """Serializer for the bulk update request containing a list of transaction updates."""

    transactions = BulkTransactionUpdateSerializer(
        many=True, help_text="List of transaction updates"
    )
