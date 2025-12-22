from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import CategoryViewSet, SubcategoryViewSet, TransactionViewSet
from apps.accounts.views.accounts import AccountViewSet
from apps.accounts.views.credit_cards import CreditCardViewSet
from apps.accounts.views.csv_import import CSVImportView

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("subcategories", SubcategoryViewSet, basename="subcategory")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("accounts", AccountViewSet, basename="account")
router.register("credit-cards", CreditCardViewSet, basename="credit-card")

urlpatterns = [
    path("transactions/import-csv/", CSVImportView.as_view(), name="transaction-import-csv"),
    path("", include(router.urls)),
]
