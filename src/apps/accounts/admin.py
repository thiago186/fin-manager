from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.accounts.models import (
    Account,
    Category,
    CreditCard,
    ImportedReport,
    Subcategory,
    Tag,
    Transaction,
)
from apps.accounts.tasks import process_csv_import_task


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
        "transaction_type",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "transaction_type",
        "is_active",
        "created_at",
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
    ]
    list_editable = [
        "is_active",
    ]
    ordering = [
        "name",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "name", "transaction_type")},
        ),
        ("Display", {"fields": ("description",)}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user")


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    """Admin configuration for the Subcategory model."""

    list_display = [
        "name",
        "user",
        "category",
        "transaction_type",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "category",
        "is_active",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
        "user__username",
        "user__email",
        "category__name",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "transaction_type",
    ]
    list_editable = [
        "is_active",
    ]
    ordering = [
        "name",
    ]
    autocomplete_fields = [
        "category",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "name", "category")},
        ),
        ("Display", {"fields": ("description",)}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "transaction_type"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Subcategory]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user", "category")

    def transaction_type(self, obj: Subcategory) -> str:
        """Get transaction type from parent category."""
        return obj.category.transaction_type

    transaction_type.short_description = "Transaction Type"


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


@admin.register(ImportedReport)
class ImportedReportAdmin(admin.ModelAdmin):
    """Admin configuration for the ImportedReport model."""

    list_display = [
        "file_name",
        "user",
        "status",
        "handler_type",
        "success_count",
        "error_count",
        "created_at",
        "processed_at",
    ]
    list_filter = [
        "status",
        "handler_type",
        "created_at",
        "processed_at",
    ]
    search_fields = [
        "file_name",
        "file_path",
        "user__username",
        "user__email",
        "handler_type",
        "failed_reason",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "processed_at",
        "errors",
    ]
    ordering = [
        "-created_at",
    ]
    date_hierarchy = "created_at"
    actions = [
        "rerun_import",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "file_name", "file_path", "status")},
        ),
        (
            "Processing Details",
            {
                "fields": (
                    "handler_type",
                    "success_count",
                    "error_count",
                    "errors",
                )
            },
        ),
        (
            "Failure Information",
            {"fields": ("failed_reason",), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "processed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[ImportedReport]:
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related("user")

    @admin.action(description="Re-run import for selected reports")
    def rerun_import(
        self, request: HttpRequest, queryset: QuerySet[ImportedReport]
    ) -> None:
        """Admin action to re-run CSV import for selected reports.

        This action schedules Celery tasks to process the selected ImportedReport
        instances asynchronously. The status will be updated to PROCESSING when
        the task starts.

        Args:
            request: HTTP request object.
            queryset: QuerySet of ImportedReport instances to re-run.
        """
        count = 0
        for imported_report in queryset:
            # Reset status to SENT so it can be processed again
            imported_report.status = ImportedReport.Status.SENT
            imported_report.failed_reason = None
            imported_report.save(
                update_fields=["status", "failed_reason", "updated_at"]
            )

            # Schedule the Celery task
            process_csv_import_task.delay(imported_report.id)
            count += 1

        self.message_user(
            request,
            f"Successfully scheduled {count} import{'s' if count != 1 else ''} for re-processing.",
        )
