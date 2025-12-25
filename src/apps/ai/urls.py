"""URL configuration for AI app."""

from django.urls import path

from apps.ai.views.ai_classification_view import AIClassificationView

app_name = "ai"

urlpatterns = [
    path("classify-transactions/", AIClassificationView.as_view(), name="classify-transactions"),
]

