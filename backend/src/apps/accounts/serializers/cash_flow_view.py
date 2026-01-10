from typing import Any

from rest_framework import serializers

from apps.accounts.models.cash_flow_view import (
    CashFlowGroup,
    CashFlowResult,
    CashFlowView,
)
from apps.accounts.models.categories import Category
from apps.accounts.serializers.categories import CategoryListSerializer


class CashFlowGroupSerializer(serializers.ModelSerializer):
    """Serializer for CashFlowGroup model."""

    categories = CategoryListSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="categories",
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = CashFlowGroup
        fields = [
            "id",
            "name",
            "position",
            "categories",
            "category_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate group data."""
        attrs = super().validate(attrs)
        cash_flow_view = attrs.get("cash_flow_view") or (
            self.instance.cash_flow_view if self.instance else None
        )
        position = attrs.get("position") or (
            self.instance.position if self.instance else None
        )

        if cash_flow_view and position is not None:
            groups = CashFlowGroup.objects.filter(
                cash_flow_view=cash_flow_view, position=position
            )
            results = CashFlowResult.objects.filter(
                cash_flow_view=cash_flow_view, position=position
            )
            if self.instance:
                groups = groups.exclude(pk=self.instance.pk)
            if groups.exists() or results.exists():
                raise serializers.ValidationError(
                    {
                        "position": f"Position {position} is already taken by another group or result in this view."
                    }
                )

        return attrs


class CashFlowResultSerializer(serializers.ModelSerializer):
    """Serializer for CashFlowResult model."""

    class Meta:
        model = CashFlowResult
        fields = [
            "id",
            "name",
            "position",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate result data."""
        attrs = super().validate(attrs)
        cash_flow_view = attrs.get("cash_flow_view") or (
            self.instance.cash_flow_view if self.instance else None
        )
        position = attrs.get("position") or (
            self.instance.position if self.instance else None
        )

        if cash_flow_view and position is not None:
            groups = CashFlowGroup.objects.filter(
                cash_flow_view=cash_flow_view, position=position
            )
            results = CashFlowResult.objects.filter(
                cash_flow_view=cash_flow_view, position=position
            )
            if self.instance:
                results = results.exclude(pk=self.instance.pk)
            if groups.exists() or results.exists():
                raise serializers.ValidationError(
                    {
                        "position": f"Position {position} is already taken by another group or result in this view."
                    }
                )

        return attrs


class CashFlowViewSerializer(serializers.ModelSerializer):
    """Serializer for CashFlowView model with nested groups and results."""

    groups = CashFlowGroupSerializer(many=True, required=False)
    results = CashFlowResultSerializer(many=True, required=False)

    class Meta:
        model = CashFlowView
        fields = [
            "id",
            "name",
            "groups",
            "results",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data: dict[str, Any]) -> CashFlowView:
        """Create a cash flow view with nested groups and results."""
        groups_data = validated_data.pop("groups", [])
        results_data = validated_data.pop("results", [])

        view = CashFlowView.objects.create(**validated_data)

        for group_data in groups_data:
            categories = group_data.pop("categories", [])
            group = CashFlowGroup.objects.create(cash_flow_view=view, **group_data)
            if categories:
                group.categories.set(categories)

        for result_data in results_data:
            CashFlowResult.objects.create(cash_flow_view=view, **result_data)

        return view

    def update(
        self, instance: CashFlowView, validated_data: dict[str, Any]
    ) -> CashFlowView:
        """
        Update a cash flow view with nested groups and results.

        Completely replaces all existing groups and results with the provided data.
        All existing groups and results are deleted before creating new ones.
        """
        groups_data = validated_data.pop("groups", [])
        results_data = validated_data.pop("results", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.groups.all().delete()
        instance.results.all().delete()

        for group_data in groups_data:
            categories = group_data.pop("categories", [])
            group_data.pop("id", None)
            group = CashFlowGroup.objects.create(cash_flow_view=instance, **group_data)
            if categories:
                group.categories.set(categories)

        for result_data in results_data:
            result_data.pop("id", None)
            CashFlowResult.objects.create(cash_flow_view=instance, **result_data)

        return instance


class MonthlyTotalsSerializer(serializers.Serializer):
    """Serializer for monthly totals in report."""

    def to_representation(self, instance: dict[str, str]) -> dict[str, str]:
        """Convert monthly totals to string keys."""
        return {str(k): str(v) for k, v in instance.items()}


class SubcategoryReportItemSerializer(serializers.Serializer):
    """Serializer for subcategory items in report."""

    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField()
    monthly_totals = MonthlyTotalsSerializer()
    annual_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class CategoryReportItemSerializer(serializers.Serializer):
    """Serializer for category items in report with nested subcategories."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    monthly_totals = MonthlyTotalsSerializer()
    annual_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    subcategories = SubcategoryReportItemSerializer(many=True)


class GroupReportItemSerializer(serializers.Serializer):
    """Serializer for group items in report."""

    type = serializers.CharField(default="group")
    name = serializers.CharField()
    position = serializers.IntegerField()
    categories = CategoryReportItemSerializer(many=True)
    monthly_totals = MonthlyTotalsSerializer()
    annual_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class ResultReportItemSerializer(serializers.Serializer):
    """Serializer for result items in report."""

    type = serializers.CharField(default="result")
    name = serializers.CharField()
    position = serializers.IntegerField()
    monthly_totals = MonthlyTotalsSerializer()
    annual_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class UncategorizedReportItemSerializer(serializers.Serializer):
    """Serializer for uncategorized items in report."""

    type = serializers.CharField(default="uncategorized")
    name = serializers.CharField()
    monthly_totals = MonthlyTotalsSerializer()
    annual_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class CashFlowReportSerializer(serializers.Serializer):
    """Serializer for cash flow report response."""

    view_id = serializers.IntegerField()
    view_name = serializers.CharField()
    year = serializers.IntegerField()
    items = serializers.ListField(child=serializers.DictField(), allow_empty=True)
