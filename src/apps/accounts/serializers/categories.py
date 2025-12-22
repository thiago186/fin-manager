from typing import Any, cast

from rest_framework import serializers

from apps.accounts.models.categories import Category
from apps.accounts.models.subcategory import Subcategory
from apps.accounts.serializers.subcategory import SubcategoryListSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["user"]


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "transaction_type", "is_active"]


class CategoryDetailSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"

    def get_subcategories(self, obj: Category) -> list[dict[str, Any]]:
        """Get subcategories for this category."""

        subcategories = Subcategory.objects.filter(category=obj, is_active=True)
        return cast(
            list[dict[str, Any]],
            SubcategoryListSerializer(subcategories, many=True).data,
        )
