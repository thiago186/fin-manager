"""
ViewSet for managing transactions with CRUD operations.

Provides endpoints for creating, reading, updating, and deleting transactions.
Transactions are filtered by the authenticated user and can be filtered by transaction type, account, credit card, category, and date.
"""

from typing import Any

from django.db import models
from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.transaction import Transaction
from apps.accounts.serializers import TransactionSerializer


class TransactionViewSet(ModelViewSet):
    """
    ViewSet for managing transactions with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting transactions.
    Transactions are filtered by the authenticated user and can be filtered by transaction type, account, credit card, category, and date.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self) -> QuerySet[Transaction]:  # type: ignore
        """
        Get queryset filtered by the authenticated user.

        Returns:
            QuerySet of transactions belonging to the authenticated user
        """
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """
        Automatically set the user when creating a transaction.

        Args:
            serializer: The transaction serializer instance
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["transactions"],
        summary="List transactions",
        description="Retrieve a list of transactions for the authenticated user with optional filtering.",
        parameters=[
            OpenApiParameter(
                name="transaction_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by transaction type (INCOME/EXPENSE/TRANSFER)",
                examples=[
                    OpenApiExample("Income", value="INCOME"),
                    OpenApiExample("Expense", value="EXPENSE"),
                    OpenApiExample("Transfer", value="TRANSFER"),
                ],
            ),
            OpenApiParameter(
                name="account_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by account ID",
            ),
            OpenApiParameter(
                name="credit_card_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by credit card ID",
            ),
            OpenApiParameter(
                name="category_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by category ID",
            ),
            OpenApiParameter(
                name="occurred_at",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by occurred_at date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="inactive_categories",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Include inactive categories in the response",
            ),
        ],
        responses={200: TransactionSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List transactions with optional filtering.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with list of transactions
        """
        queryset = self.get_queryset()

        transaction_type = request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        account_id = request.query_params.get("account_id")
        if account_id:
            queryset = queryset.filter(account_id=account_id)

        credit_card_id = request.query_params.get("credit_card_id")
        if credit_card_id:
            queryset = queryset.filter(credit_card_id=credit_card_id)

        category_id = request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        occurred_at = request.query_params.get("occurred_at")
        if occurred_at:
            queryset = queryset.filter(occurred_at=occurred_at)

        inactive_categories = request.query_params.get("inactive_categories")
        if not inactive_categories:
            queryset = queryset.filter(
                models.Q(category__isnull=True) | models.Q(category__is_active=True)
            ).filter(
                models.Q(subcategory__isnull=True)
                | models.Q(subcategory__is_active=True)
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["transactions"],
        summary="Create transaction",
        description="Create a new transaction for the authenticated user",
        request=TransactionSerializer,
        responses={201: TransactionSerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new transaction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created transaction
        """
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["transactions"],
        summary="Retrieve transaction",
        description="Retrieve detailed information about a specific transaction",
        responses={200: TransactionSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific transaction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with transaction details
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["transactions"],
        summary="Update transaction",
        description="Update an existing transaction",
        request=TransactionSerializer,
        responses={200: TransactionSerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a transaction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated transaction
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["transactions"],
        summary="Partial update transaction",
        description="Partially update an existing transaction",
        request=TransactionSerializer,
        responses={200: TransactionSerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a transaction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated transaction
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["transactions"],
        summary="Delete transaction",
        description="Delete a transaction",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a transaction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        return super().destroy(request, *args, **kwargs)
