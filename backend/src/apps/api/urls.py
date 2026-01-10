from django.urls import include, path

urlpatterns = [
    path("v1/finance/", include("apps.accounts.urls")),
    path("v1/users/", include("apps.users.urls")),
    path("v1/ai/", include("apps.ai.urls")),
]
