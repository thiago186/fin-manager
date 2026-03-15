from decimal import Decimal

from rest_framework import serializers

from apps.accounts.models.account import Account
from apps.accounts.models.categories import Category
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.installment_plan import InstallmentPlan
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.models.transaction import Transaction
from apps.accounts.serializers.general import AccountSerializer, CreditCardSerializer
from apps.accounts.serializers.categories import CategoryListSerializer
from apps.accounts.serializers.subcategory import SubcategoryListSerializer


class InstallmentPlanCreateSerializer(serializers.Serializer):
    """Write-only serializer for creating an installment plan."""

    INPUT_MODE_TOTAL = "total_and_count"
    INPUT_MODE_INSTALLMENT = "installment_and_count"

    transaction_type = serializers.ChoiceField(
        choices=Transaction.TransactionType.choices,
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    input_mode = serializers.ChoiceField(
        choices=[INPUT_MODE_TOTAL, INPUT_MODE_INSTALLMENT],
    )
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    installment_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    installments_count = serializers.IntegerField(min_value=2, max_value=360)
    first_due_date = serializers.DateField()

    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        source="account",
        required=False,
        allow_null=True,
    )
    credit_card_id = serializers.PrimaryKeyRelatedField(
        queryset=CreditCard.objects.all(),
        source="credit_card",
        required=False,
        allow_null=True,
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
        required=False,
        allow_null=True,
    )
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=Subcategory.objects.filter(is_active=True),
        source="subcategory",
        required=False,
        allow_null=True,
    )

    def validate(self, attrs: dict) -> dict:
        """Validate amount fields based on input_mode and enforce account/credit_card exclusivity."""
        input_mode = attrs.get("input_mode")
        total_amount = attrs.get("total_amount")
        installment_amount = attrs.get("installment_amount")

        if input_mode == self.INPUT_MODE_TOTAL:
            if not total_amount:
                raise serializers.ValidationError(
                    {"total_amount": "This field is required when input_mode is 'total_and_count'."}
                )
            attrs["installment_amount"] = None
        else:
            if not installment_amount:
                raise serializers.ValidationError(
                    {"installment_amount": "This field is required when input_mode is 'installment_and_count'."}
                )
            attrs["total_amount"] = None

        account = attrs.get("account")
        credit_card = attrs.get("credit_card")
        if account and credit_card:
            raise serializers.ValidationError(
                "An installment plan cannot be associated with both an account and a credit card."
            )

        return attrs


class InstallmentPlanSerializer(serializers.ModelSerializer):
    """Read serializer for installment plan with nested relations and transaction counts."""

    account = AccountSerializer(read_only=True)
    credit_card = CreditCardSerializer(read_only=True)
    category = CategoryListSerializer(read_only=True)
    subcategory = SubcategoryListSerializer(read_only=True)
    transactions_count = serializers.SerializerMethodField()

    class Meta:
        model = InstallmentPlan
        fields = [
            "id",
            "description",
            "total_amount",
            "installment_amount",
            "installments_count",
            "first_due_date",
            "transaction_type",
            "account",
            "credit_card",
            "category",
            "subcategory",
            "transactions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_transactions_count(self, obj: InstallmentPlan) -> int:
        """Return the number of transactions linked to this plan."""
        return obj.transactions.count()
