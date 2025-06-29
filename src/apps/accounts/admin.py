from django.contrib import admin
from apps.accounts.models import Account


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
