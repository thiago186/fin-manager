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
            "charge_at_card",
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

        if credit_card and not attrs.get("charge_at_card"):
            raise serializers.ValidationError(
                "When a transaction is associated with a credit card, the 'charge_at_card' field must be filled."
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
