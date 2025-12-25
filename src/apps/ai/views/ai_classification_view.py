"""API view for AI transaction classification."""

import structlog
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.serializers import (
    AIClassificationRequestSerializer,
    AIClassificationResponseSerializer,
)
from apps.ai.services.ai_classification_service import AIClassificationService

logger = structlog.get_logger(__name__)


@extend_schema(
    tags=["AI"],
    summary="Classify transactions using AI",
    description="Use AI to automatically classify uncategorized transactions into subcategories",
    request=AIClassificationRequestSerializer,
    responses={
        200: OpenApiResponse(
            description="Classification completed",
            response=AIClassificationResponseSerializer,
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={
                        "classified_count": 15,
                        "failed_count": 2,
                        "total_processed": 17,
                        "errors": [],
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad request",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    value={"transaction_type": ["Invalid transaction type"]},
                )
            ],
        ),
        401: OpenApiResponse(
            description="Unauthorized",
            examples=[
                OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                )
            ],
        ),
    },
    examples=[
        OpenApiExample(
            "Classify All Transactions",
            value={},
        ),
        OpenApiExample(
            "Classify Expenses Only",
            value={"transaction_type": "EXPENSE"},
        ),
    ],
)
class AIClassificationView(APIView):
    """API endpoint for AI-powered transaction classification."""

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Classify transactions using AI.

        Args:
            request: HTTP request with optional transaction_type filter

        Returns:
            Response with classification summary
        """
        serializer = AIClassificationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        transaction_type = serializer.validated_data.get("transaction_type")
        limit = serializer.validated_data.get("limit", 50)

        logger.info(
            "AI classification request",
            user_id=request.user.id,
            transaction_type=transaction_type,
            limit=limit,
        )

        try:
            service = AIClassificationService(user=request.user)
            result = service.classify_transactions(
                transaction_type=transaction_type, limit=limit
            )

            response_serializer = AIClassificationResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "AI classification error",
                user_id=request.user.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return Response(
                {"error": f"Classification failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
