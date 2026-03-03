from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import BudgetViewSet, CategoryViewSet, SubcategoryViewSet, TransactionViewSet
from apps.accounts.views.accounts import AccountViewSet
from apps.accounts.views.cash_flow_view import CashFlowViewViewSet
from apps.accounts.views.credit_cards import CreditCardViewSet
from apps.accounts.views.csv_import import CSVImportView
from apps.accounts.views.imported_report import ImportedReportViewSet
from apps.accounts.views.photo_import import PhotoImportView

router = DefaultRouter()
router.register("budgets", BudgetViewSet, basename="budget")
router.register("categories", CategoryViewSet, basename="category")
router.register("subcategories", SubcategoryViewSet, basename="subcategory")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("accounts", AccountViewSet, basename="account")
router.register("credit-cards", CreditCardViewSet, basename="credit-card")
router.register("import-reports", ImportedReportViewSet, basename="import-report")
router.register("cash-flow-views", CashFlowViewViewSet, basename="cash-flow-view")

urlpatterns = [
    path(
        "transactions/import-report/",
        CSVImportView.as_view(),
        name="transaction-import-report",
    ),
    path(
        "transactions/import-photo/",
        PhotoImportView.as_view(),
        name="transaction-import-photo",
    ),
    path("", include(router.urls)),
]
