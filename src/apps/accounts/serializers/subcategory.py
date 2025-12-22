from typing import Any, cast

from rest_framework import serializers

from apps.accounts.models.subcategory import Subcategory


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = "__all__"
        read_only_fields = ["user"]


class SubcategoryListSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Subcategory
        fields = ["id", "name", "category", "transaction_type", "is_active"]


class SubcategoryDetailSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = Subcategory
        fields = "__all__"

    def get_category(self, obj: Subcategory) -> dict[str, Any]:
        """Get category details."""
        from apps.accounts.serializers.categories import CategoryListSerializer

        return cast(
            dict[str, Any],
            CategoryListSerializer(obj.category).data,
        )
