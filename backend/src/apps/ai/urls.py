"""URL configuration for AI app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ai.views.ai_classification_view import AIClassificationView
from apps.ai.views.classifier_instruction_view import AIClassifierInstructionViewSet

app_name = "ai"

router = DefaultRouter()
router.register(
    "classifier-instructions",
    AIClassifierInstructionViewSet,
    basename="classifier-instruction",
)

urlpatterns = [
    path("classify-transactions/", AIClassificationView.as_view(), name="classify-transactions"),
    path("", include(router.urls)),
]

