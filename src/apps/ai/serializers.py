"""Serializers for AI classification."""

from rest_framework import serializers

from apps.accounts.models.transaction import Transaction


class AIClassificationRequestSerializer(serializers.Serializer):
    """Serializer for AI classification request."""

    transaction_type = serializers.ChoiceField(
        choices=Transaction.TransactionType.choices,
        required=False,
        allow_null=True,
        help_text="Filter transactions by type (INCOME, EXPENSE, TRANSFER)",
    )
    limit = serializers.IntegerField(
        default=50,
        min_value=1,
        max_value=100,
        required=False,
        help_text="Maximum number of transactions to classify (1-100)",
    )


class AIClassificationResponseSerializer(serializers.Serializer):
    """Serializer for AI classification response."""

    classified_count = serializers.IntegerField(
        help_text="Number of transactions successfully classified"
    )
    failed_count = serializers.IntegerField(
        help_text="Number of transactions that failed to classify"
    )
    total_processed = serializers.IntegerField(
        help_text="Total number of transactions processed"
    )
    errors = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of error messages (limited to first 10)",
    )

