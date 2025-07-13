from typing import Any
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.accounts.models import Account, Category, CreditCard, Tag, Transaction


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
        ("Display", {"fields": ("description",)}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "level"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user", "parent")


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    """Admin configuration for the CreditCard model."""

    list_display = [
        "name",
        "user",
        "close_date",
        "due_date",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "created_at",
        "close_date",
        "due_date",
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
        ("Basic Information", {"fields": ("user", "name")}),
        ("Billing Cycle", {"fields": ("close_date", "due_date")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[CreditCard]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for the Tag model."""

    list_display = [
        "name",
        "user",
        "created_at",
    ]
    list_filter = [
        "created_at",
    ]
    search_fields = [
        "name",
        "user__username",
        "user__email",
    ]
    readonly_fields = [
        "created_at",
    ]
    ordering = [
        "-created_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "name")}),
        (
            "Timestamps",
            {"fields": ("created_at",), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for the Transaction model."""

    list_display = [
        "description",
        "user",
        "transaction_type",
        "amount",
        "account",
        "credit_card",
        "occurred_at",
        "charge_at_card",
        "category",
        "installments_total",
        "installment_number",
    ]
    list_filter = [
        "transaction_type",
        "occurred_at",
        "charge_at_card",
        "category",
        "subcategory",
        "installments_total",
    ]
    search_fields = [
        "description",
        "user__username",
        "user__email",
        "account__name",
        "credit_card__name",
        "category__name",
        "subcategory__name",
    ]
    readonly_fields = [
        "installment_group_id",
    ]
    list_editable = [
        "transaction_type",
        "amount",
    ]
    ordering = [
        "-occurred_at",
    ]
    autocomplete_fields = [
        "account",
        "credit_card",
        "category",
        "subcategory",
        "tags",
    ]
    filter_horizontal = [
        "tags",
    ]
    date_hierarchy = "occurred_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "transaction_type",
                    "amount",
                    "description",
                    "occurred_at",
                )
            },
        ),
        (
            "Account/Credit Card",
            {
                "fields": ("account", "credit_card", "charge_at_card"),
                "description": "Choose either an account or a credit card, not both.",
            },
        ),
        (
            "Categorization",
            {"fields": ("category", "subcategory", "tags")},
        ),
        (
            "Installments",
            {
                "fields": (
                    "installments_total",
                    "installment_number",
                    "installment_group_id",
                ),
                "description": "For installment transactions, set total and current number.",
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Transaction]:
        """Optimize queryset with select_related for better performance."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user",
                "account",
                "credit_card",
                "category",
                "subcategory",
            )
            .prefetch_related("tags")
        )
