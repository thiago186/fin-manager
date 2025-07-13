from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import CategoryViewSet, TransactionViewSet
from apps.accounts.views.accounts import AccountViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("accounts", AccountViewSet, basename="account")


urlpatterns = [
    path("", include(router.urls)),
]
