from rest_framework import serializers

from apps.accounts.models.budget import Budget
from apps.accounts.models.categories import Category


class CategoryNestedSerializer(serializers.ModelSerializer):
    """Lightweight category representation for budget responses."""

    class Meta:
        model = Category
        fields = ["id", "name", "transaction_type"]


class BudgetSerializer(serializers.ModelSerializer):
    category = CategoryNestedSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
    )

    class Meta:
        model = Budget
        fields = [
            "id",
            "category",
            "category_id",
            "amount",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user"]

    def validate_category(self, category: Category) -> Category:
        """Ensure the category belongs to the requesting user."""
        request = self.context.get("request")
        if request and category.user != request.user:
            raise serializers.ValidationError("Category does not belong to you.")
        return category


class BudgetListSerializer(serializers.ModelSerializer):
    category = CategoryNestedSerializer(read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "category", "amount", "is_active", "created_at", "updated_at"]
