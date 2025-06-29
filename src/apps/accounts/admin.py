from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.accounts.models import Account, Category


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin configuration for the Account model."""

    list_display = [
        "name",
        "user",
        "account_type",
        "current_balance",
        "currency",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "account_type",
        "currency",
        "is_active",
        "created_at",
    ]
    search_fields = [
        "name",
        "user__username",
        "user__email",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    list_editable = [
        "is_active",
    ]
    ordering = [
        "-created_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "name", "account_type", "currency")}),
        ("Financial Information", {"fields": ("current_balance", "is_active")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for the Category model."""

    list_display = [
        "name",
        "user",
        "parent",
        "transaction_type",
        "level",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "transaction_type",
        "is_active",
        "created_at",
        "parent",
    ]
    search_fields = [
        "name",
        "description",
        "user__username",
        "user__email",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "level",
    ]
    list_editable = [
        "is_active",
    ]
    ordering = [
        "name",
    ]
    autocomplete_fields = [
        "parent",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "name", "parent", "transaction_type")},
        ),
        ("Display", {"fields": ("description", "color", "icon")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "level"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user", "parent")
