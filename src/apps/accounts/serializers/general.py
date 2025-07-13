from rest_framework import serializers
from apps.accounts.models.account import Account
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.transaction_tag import Tag


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "current_balance",
            "account_type",
            "currency",
            "created_at",
            "updated_at",
            "is_active",
        ]


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = [
            "id",
            "name",
            "close_date",
            "due_date",
            "created_at",
            "updated_at",
            "is_active",
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "created_at"]
