from typing import Any, Type

from django.contrib.auth.models import User
from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.budget import Budget
from apps.accounts.serializers import (
    BudgetInsightSerializer,
    BudgetListSerializer,
    BudgetSerializer,
)
from apps.accounts.services.budget_insight_service import BudgetInsightService


class BudgetViewSet(ModelViewSet):
    """ViewSet for managing budgets with CRUD operations."""

    permission_classes = [IsAuthenticated]
    serializer_class = BudgetSerializer

    def get_queryset(self) -> QuerySet[Budget]:  # type: ignore
        return Budget.objects.filter(user=self.request.user).select_related("category")

    def get_serializer_class(self) -> Type[serializers.BaseSerializer]:
        if self.action == "list":
            return BudgetListSerializer
        return BudgetSerializer

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["budgets"],
        summary="List budgets",
        description="Retrieve a list of budgets for the authenticated user",
        parameters=[
            OpenApiParameter(
                name="transaction_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by category transaction type (income/expense)",
                examples=[
                    OpenApiExample("Income", value="income"),
                    OpenApiExample("Expense", value="expense"),
                ],
            ),
            OpenApiParameter(
                name="is_active",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter by active status",
            ),
        ],
        responses={200: BudgetListSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.get_queryset()

        transaction_type = request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(category__transaction_type=transaction_type)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["budgets"],
        summary="Create budget",
        description="Create a new budget for the authenticated user",
        request=BudgetSerializer,
        responses={201: BudgetSerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["budgets"],
        summary="Retrieve budget",
        description="Retrieve detailed information about a specific budget",
        responses={200: BudgetSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["budgets"],
        summary="Update budget",
        description="Update an existing budget",
        request=BudgetSerializer,
        responses={200: BudgetSerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["budgets"],
        summary="Partial update budget",
        description="Partially update an existing budget",
        request=BudgetSerializer,
        responses={200: BudgetSerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["budgets"],
        summary="Delete budget",
        description="Delete a budget permanently",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=["budgets"],
        summary="Budget insights",
        description="Retrieve budget insights for the current month showing categories that have spent the threshold percentage or more of their budget.",
        parameters=[
            OpenApiParameter(
                name="threshold",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Minimum percentage spent to include in results (default: 80, use 0 for all)",
            ),
        ],
        responses={200: BudgetInsightSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="insights")
    def insights(self, request: Request) -> Response:
        """Return budget insights for the current month."""
        user = request.user
        assert isinstance(user, User)

        threshold_param = request.query_params.get("threshold", "80")
        try:
            threshold = int(threshold_param)
        except ValueError:
            threshold = 80

        service = BudgetInsightService(user=user)
        data = service.get_insights(threshold_percentage=threshold)
        serializer = BudgetInsightSerializer(data, many=True)
        return Response(serializer.data)
