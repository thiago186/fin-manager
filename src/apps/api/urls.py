from django.urls import path, include

urlpatterns = [
    path("users/", include("apps.users.urls")),
    path("accounts/", include("apps.accounts.urls")),
]
