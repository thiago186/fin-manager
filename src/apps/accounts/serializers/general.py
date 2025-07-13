from rest_framework import serializers
from apps.accounts.models.account import Account
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.models.transaction_tag import Tag


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "balance", "account_type"]


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ["id", "name", "limit", "due_day", "closing_day"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]
