from django.urls import include, path

urlpatterns = [
    path("v1/accounts/", include("apps.accounts.urls")),
]