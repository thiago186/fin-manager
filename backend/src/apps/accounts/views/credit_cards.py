from typing import Any, Type

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.credit_card import CreditCard
from apps.accounts.serializers import CreditCardSerializer


class CreditCardViewSet(ModelViewSet):
    """
    ViewSet for managing credit cards with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting credit cards.
    Credit cards are filtered by the authenticated user and can be filtered by is_active.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CreditCardSerializer

    def get_queryset(self) -> QuerySet[CreditCard]:  # type: ignore
        """
        Get queryset filtered by the authenticated user.

        Returns:
            QuerySet of credit cards belonging to the authenticated user
        """
        return CreditCard.objects.filter(user=self.request.user)

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """
        Automatically set the user when creating a credit card.

        Args:
            serializer: The credit card serializer instance
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["credit-cards"],
        summary="List credit cards",
        description="Retrieve a list of credit cards for the authenticated user with optional filtering.",
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
        ],
        responses={200: CreditCardSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List credit cards with optional filtering.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with list of credit cards
        """
        queryset = self.get_queryset()

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["credit-cards"],
        summary="Create credit card",
        description="Create a new credit card for the authenticated user",
        request=CreditCardSerializer,
        responses={201: CreditCardSerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new credit card.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created credit card
        """
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["credit-cards"],
        summary="Retrieve credit card",
        description="Retrieve detailed information about a specific credit card",
        responses={200: CreditCardSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific credit card.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with credit card details
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["credit-cards"],
        summary="Update credit card",
        description="Update an existing credit card",
        request=CreditCardSerializer,
        responses={200: CreditCardSerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a credit card.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated credit card
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["credit-cards"],
        summary="Partial update credit card",
        description="Partially update an existing credit card",
        request=CreditCardSerializer,
        responses={200: CreditCardSerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a credit card.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated credit card
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["credit-cards"],
        summary="Delete credit card",
        description="Delete a credit card",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a credit card.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        return super().destroy(request, *args, **kwargs)
