from django.urls import path
from . import views

urlpatterns = [
    path("", views.UserCreate.as_view(), name="user-create"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("check_auth/", views.CheckAuthView.as_view(), name="check_auth"),
]
