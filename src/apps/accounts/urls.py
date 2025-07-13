from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import CategoryViewSet, TransactionViewSet
from apps.accounts.views.accounts import AccountViewSet
from apps.accounts.views.credit_cards import CreditCardViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("accounts", AccountViewSet, basename="account")
router.register("credit-cards", CreditCardViewSet, basename="credit-card")

urlpatterns = [
    path("", include(router.urls)),
]
