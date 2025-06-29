from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts.views import CategoryViewSet

router = DefaultRouter()
router.register("", CategoryViewSet, basename="category")

urlpatterns = [
    path("categories/", include(router.urls)),
]
