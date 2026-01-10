"""
ViewSet for managing transactions with CRUD operations.

Provides endpoints for creating, reading, updating, and deleting transactions.
Transactions are filtered by the authenticated user and can be filtered by transaction type, account, credit card, category, subcategory, and date.
"""

from typing import Any

import structlog
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db import transaction as db_transaction
from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.transaction import Transaction
from apps.accounts.serializers import TransactionSerializer
from apps.accounts.serializers.transaction import (
    BulkTransactionUpdateRequestSerializer,
)

logger = structlog.stdlib.get_logger()


class TransactionPagination(PageNumberPagination):
    """Custom pagination for transaction list with default 100 and max 500."""

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class TransactionViewSet(ModelViewSet):
    """
    ViewSet for managing transactions with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting transactions.
    Transactions are filtered by the authenticated user and can be filtered by transaction type, account, credit card, category, subcategory, and date.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination

    def get_queryset(self) -> QuerySet[Transaction]:  # type: ignore
        """
        Get queryset filtered by the authenticated user with optimized queries.

        Uses select_related for ForeignKey relationships and prefetch_related
        for ManyToMany relationships to eliminate N+1 query problems.

        Returns:
            QuerySet of transactions belonging to the authenticated user
        """
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("account", "credit_card", "category", "subcategory")
            .prefetch_related("tags")
        )

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
                name="subcategory_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by subcategory ID",
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
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number (default: 1)",
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of results per page (default: 100, max: 500)",
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

        subcategory_id = request.query_params.get("subcategory_id")
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)

        occurred_at = request.query_params.get("occurred_at")
        if occurred_at:
            queryset = queryset.filter(occurred_at=occurred_at)

        inactive_categories = request.query_params.get("inactive_categories")
        if not inactive_categories:
            queryset = queryset.filter(
                (models.Q(category__isnull=True) | models.Q(category__is_active=True))
                & (
                    models.Q(subcategory__isnull=True)
                    | models.Q(subcategory__is_active=True)
                )
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
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

    @extend_schema(
        tags=["transactions"],
        summary="Bulk update transactions",
        description=(
            "Update multiple transactions in a single request. "
            "Each transaction update must include the transaction ID and the fields to update. "
            "All transactions must belong to the authenticated user. "
            "The operation is atomic - if any transaction fails validation, none are updated."
        ),
        request=BulkTransactionUpdateRequestSerializer,
        responses={
            200: TransactionSerializer(many=True),
            400: {"description": "Validation errors"},
        },
        examples=[
            OpenApiExample(
                "Bulk Update Request",
                value={
                    "transactions": [
                        {
                            "id": 1,
                            "category_id": 5,
                            "description": "Updated description",
                            "need_review": False,
                        },
                        {
                            "id": 2,
                            "amount": "150.00",
                            "subcategory_id": 10,
                            "need_review": True,
                        },
                    ]
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["patch"], url_path="bulk-update")
    def bulk_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Bulk update multiple transactions.

        Args:
            request: The HTTP request containing a list of transaction updates
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated transactions or validation errors
        """
        request_serializer = BulkTransactionUpdateRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = request_serializer.validated_data
        logger.debug(f"Validated data: {validated_data}")

        transaction_updates = validated_data["transactions"]
        transaction_ids = [update["id"] for update in transaction_updates]

        user_transactions = Transaction.objects.filter(
            id__in=transaction_ids, user=request.user
        )

        if user_transactions.count() != len(transaction_ids):
            found_ids = set(user_transactions.values_list("id", flat=True))
            missing_ids = set(transaction_ids) - found_ids
            return Response(
                {
                    "error": "Some transactions were not found or do not belong to the authenticated user",
                    "missing_transaction_ids": list(missing_ids),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction_map = {t.id: t for t in user_transactions}
        updated_transactions = []
        errors = []

        try:
            with db_transaction.atomic():
                for update_data in transaction_updates:
                    transaction_id = update_data.get("id")
                    if transaction_id is None:
                        errors.append(
                            {
                                "transaction_id": None,
                                "errors": {"id": ["This field is required."]},
                            }
                        )
                        continue

                    transaction = transaction_map.get(transaction_id)
                    if transaction is None:
                        errors.append(
                            {
                                "transaction_id": transaction_id,
                                "errors": {
                                    "id": [
                                        f"Transaction with id {transaction_id} not found or does not belong to user."
                                    ]
                                },
                            }
                        )
                        continue

                    # Convert validated_data to use _id fields for the update serializer
                    # The BulkTransactionUpdateItemSerializer converts category_id/subcategory_id
                    # to category/subcategory objects, but TransactionSerializer expects _id fields
                    serializer_data = {
                        k: v for k, v in update_data.items() if k != "id"
                    }
                    if "category" in serializer_data:
                        category = serializer_data.pop("category")
                        serializer_data["category_id"] = (
                            category.id if category is not None else None
                        )
                    if "subcategory" in serializer_data:
                        subcategory = serializer_data.pop("subcategory")
                        serializer_data["subcategory_id"] = (
                            subcategory.id if subcategory is not None else None
                        )

                    update_serializer = TransactionSerializer(
                        instance=transaction,
                        data=serializer_data,
                        partial=True,
                        context={"request": request},
                    )
                    if not update_serializer.is_valid():
                        errors.append(
                            {
                                "transaction_id": transaction_id,
                                "errors": update_serializer.errors,
                            }
                        )
                        continue

                    try:
                        updated_transaction = update_serializer.save()
                        updated_transactions.append(updated_transaction)
                    except DjangoValidationError as e:
                        errors.append(
                            {
                                "transaction_id": transaction_id,
                                "errors": {
                                    "non_field_errors": e.messages
                                    if hasattr(e, "messages")
                                    else [str(e)]
                                },
                            }
                        )
                    except Exception as e:
                        errors.append(
                            {
                                "transaction_id": transaction_id,
                                "errors": {"non_field_errors": [str(e)]},
                            }
                        )

                if errors:
                    raise serializers.ValidationError({"transaction_errors": errors})

        except serializers.ValidationError as e:
            return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to update transactions: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = TransactionSerializer(updated_transactions, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["transactions"],
        summary="List transactions needing review",
        description=(
            "Retrieve all transactions that need review after AI classification. "
            "Only returns transactions belonging to the authenticated user."
        ),
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number (default: 1)",
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of results per page (default: 100, max: 500)",
            ),
        ],
        responses={200: TransactionSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="needing-review")
    def needing_review(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve all transactions that need review.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with paginated list of transactions needing review
        """
        queryset = self.get_queryset().filter(need_review=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
