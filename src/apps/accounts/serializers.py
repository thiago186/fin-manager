from typing import Any, cast
from rest_framework import serializers

from apps.accounts.models.categories import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["user"]


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "transaction_type", "parent", "is_active"]


class CategoryDetailSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    parent_category = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"

    def get_subcategories(self, obj: Category) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            CategoryListSerializer(
                obj.subcategories.filter(is_active=True), many=True
            ).data,
        )

    def get_parent_category(self, obj: Category) -> dict | None:
        if obj.parent:
            return CategoryListSerializer(obj.parent).data
        return None
