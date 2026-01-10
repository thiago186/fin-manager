from typing import Any, Type

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.account import Account
from apps.accounts.serializers import AccountSerializer


class AccountViewSet(ModelViewSet):
    """
    ViewSet for managing accounts with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting accounts.
    Accounts are filtered by the authenticated user and can be filtered by is_active, account_type, and currency.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AccountSerializer

    def get_queryset(self) -> QuerySet[Account]:  # type: ignore
        """
        Get queryset filtered by the authenticated user.

        Returns:
            QuerySet of accounts belonging to the authenticated user
        """
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """
        Automatically set the user when creating an account.

        Args:
            serializer: The account serializer instance
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["accounts"],
        summary="List accounts",
        description="Retrieve a list of accounts for the authenticated user with optional filtering.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter by active status (true/false)",
                examples=[
                    OpenApiExample("Active", value=True),
                    OpenApiExample("Inactive", value=False),
                ],
            ),
            OpenApiParameter(
                name="account_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by account type (e.g., checking)",
                examples=[
                    OpenApiExample("Checking", value="checking"),
                ],
            ),
            OpenApiParameter(
                name="currency",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by currency (e.g., BRL)",
                examples=[
                    OpenApiExample("BRL", value="BRL"),
                ],
            ),
        ],
        responses={200: AccountSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List accounts with optional filtering.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with list of accounts
        """
        queryset = self.get_queryset()

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)

        account_type = request.query_params.get("account_type")
        if account_type:
            queryset = queryset.filter(account_type=account_type)

        currency = request.query_params.get("currency")
        if currency:
            queryset = queryset.filter(currency=currency)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["accounts"],
        summary="Create account",
        description="Create a new account for the authenticated user",
        request=AccountSerializer,
        responses={201: AccountSerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new account.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created account
        """
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["accounts"],
        summary="Retrieve account",
        description="Retrieve detailed information about a specific account",
        responses={200: AccountSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific account.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with account details
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["accounts"],
        summary="Update account",
        description="Update an existing account",
        request=AccountSerializer,
        responses={200: AccountSerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update an account.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated account
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["accounts"],
        summary="Partial update account",
        description="Partially update an existing account",
        request=AccountSerializer,
        responses={200: AccountSerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update an account.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated account
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["accounts"],
        summary="Delete account",
        description="Delete an account",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete an account.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        return super().destroy(request, *args, **kwargs)
