from collections import defaultdict
from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.accounts.models import (
    Account,
    CashFlowGroup,
    CashFlowResult,
    CashFlowView,
    Category,
    CreditCard,
    ImportedReport,
    Subcategory,
    Tag,
    Transaction,
)
from apps.accounts.tasks import process_csv_import_task
from apps.ai.services.ai_classification_service import AIClassificationService


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
        "is_active",
        "created_at",
    ]
    list_filter = [
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
        ("Basic Information", {"fields": ("user", "name")}),
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
        "category",
        "installments_total",
        "installment_number",
        "need_review",
    ]
    list_filter = [
        "transaction_type",
        "occurred_at",
        "category",
        "subcategory",
        "installments_total",
        "need_review",
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
        "need_review",
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
    actions = [
        "classify_with_ai",
    ]

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
                "fields": ("account", "credit_card"),
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
        (
            "AI Classification",
            {
                "fields": ("need_review",),
                "description": "Flag indicating if this transaction needs review after AI classification.",
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

    @admin.action(description="Classify selected transactions with AI")
    def classify_with_ai(
        self, request: HttpRequest, queryset: QuerySet[Transaction]
    ) -> None:
        """Admin action to classify selected transactions using AI.

        This action groups transactions by user and classifies them using the
        AI classification service. Only uncategorized transactions will be processed.

        Args:
            request: HTTP request object.
            queryset: QuerySet of Transaction instances to classify.
        """
        # Filter to only uncategorized transactions
        uncategorized = queryset.filter(subcategory__isnull=True)

        if not uncategorized.exists():
            self.message_user(
                request,
                "No uncategorized transactions selected. All selected transactions already have subcategories.",
                level="warning",
            )
            return

        # Group by user
        transactions_by_user: dict[int, list[Transaction]] = defaultdict(list)

        for transaction in uncategorized.select_related("user"):
            transactions_by_user[transaction.user.id].append(transaction)

        total_classified = 0
        total_failed = 0
        total_processed = 0
        errors: list[str] = []

        for user_id, user_transactions in transactions_by_user.items():
            user = user_transactions[0].user
            try:
                service = AIClassificationService(user=user)
                result = service.classify_specific_transactions(user_transactions)

                total_classified += result["classified_count"]
                total_failed += result["failed_count"]
                total_processed += result["total_processed"]
                errors.extend(result["errors"])

            except Exception as e:
                total_failed += len(user_transactions)
                total_processed += len(user_transactions)
                errors.append(
                    f"Error classifying transactions for user {user.username}: {str(e)}"
                )

        # Build success message
        message_parts = [
            f"Processed {total_processed} transaction{'s' if total_processed != 1 else ''}.",
        ]

        if total_classified > 0:
            message_parts.append(
                f"Successfully classified {total_classified} transaction{'s' if total_classified != 1 else ''}."
            )

        if total_failed > 0:
            message_parts.append(
                f"Failed to classify {total_failed} transaction{'s' if total_failed != 1 else ''}."
            )

        if errors:
            error_summary = "; ".join(errors[:5])
            if len(errors) > 5:
                error_summary += f" (and {len(errors) - 5} more errors)"
            message_parts.append(f"Errors: {error_summary}")

        level = "success" if total_classified > 0 else "warning"
        self.message_user(request, " ".join(message_parts), level=level)


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


class CashFlowGroupInline(admin.TabularInline):
    """Inline admin for CashFlowGroup within CashFlowView."""

    model = CashFlowGroup
    extra = 0
    fields = [
        "name",
        "position",
        "categories",
    ]
    autocomplete_fields = [
        "categories",
    ]
    filter_horizontal = [
        "categories",
    ]


class CashFlowResultInline(admin.TabularInline):
    """Inline admin for CashFlowResult within CashFlowView."""

    model = CashFlowResult
    extra = 0
    fields = [
        "name",
        "position",
    ]


@admin.register(CashFlowView)
class CashFlowViewAdmin(admin.ModelAdmin):
    """Admin configuration for the CashFlowView model."""

    list_display = [
        "name",
        "user",
        "groups_count",
        "results_count",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "created_at",
        "updated_at",
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
    ordering = [
        "-created_at",
    ]
    inlines = [
        CashFlowGroupInline,
        CashFlowResultInline,
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "name")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[CashFlowView]:
        """Optimize queryset with select_related and prefetch_related for better performance."""
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .prefetch_related("groups", "results")
        )

    def groups_count(self, obj: CashFlowView) -> int:
        """Get the number of groups in this view."""
        return obj.groups.count()

    groups_count.short_description = "Groups"

    def results_count(self, obj: CashFlowView) -> int:
        """Get the number of results in this view."""
        return obj.results.count()

    results_count.short_description = "Results"


@admin.register(CashFlowGroup)
class CashFlowGroupAdmin(admin.ModelAdmin):
    """Admin configuration for the CashFlowGroup model."""

    list_display = [
        "name",
        "cash_flow_view",
        "user",
        "position",
        "categories_count",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "cash_flow_view",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "name",
        "cash_flow_view__name",
        "cash_flow_view__user__username",
        "cash_flow_view__user__email",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    ordering = [
        "cash_flow_view",
        "position",
    ]
    autocomplete_fields = [
        "cash_flow_view",
        "categories",
    ]
    filter_horizontal = [
        "categories",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("cash_flow_view", "name", "position")},
        ),
        ("Categories", {"fields": ("categories",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[CashFlowGroup]:
        """Optimize queryset with select_related and prefetch_related for better performance."""
        return (
            super()
            .get_queryset(request)
            .select_related("cash_flow_view", "cash_flow_view__user")
            .prefetch_related("categories")
        )

    def user(self, obj: CashFlowGroup) -> str:
        """Get the user who owns the cash flow view."""
        return obj.cash_flow_view.user

    user.short_description = "User"

    def categories_count(self, obj: CashFlowGroup) -> int:
        """Get the number of categories in this group."""
        return obj.categories.count()

    categories_count.short_description = "Categories"


@admin.register(CashFlowResult)
class CashFlowResultAdmin(admin.ModelAdmin):
    """Admin configuration for the CashFlowResult model."""

    list_display = [
        "name",
        "cash_flow_view",
        "user",
        "position",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "cash_flow_view",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "name",
        "cash_flow_view__name",
        "cash_flow_view__user__username",
        "cash_flow_view__user__email",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    ordering = [
        "cash_flow_view",
        "position",
    ]
    autocomplete_fields = [
        "cash_flow_view",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("cash_flow_view", "name", "position")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[CashFlowResult]:
        """Optimize queryset with select_related for better performance."""
        return (
            super()
            .get_queryset(request)
            .select_related("cash_flow_view", "cash_flow_view__user")
        )

    def user(self, obj: CashFlowResult) -> str:
        """Get the user who owns the cash flow view."""
        return obj.cash_flow_view.user

    user.short_description = "User"
