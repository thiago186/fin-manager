from typing import Any, Type

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.subcategory import Subcategory
from apps.accounts.serializers import (
    SubcategoryDetailSerializer,
    SubcategoryListSerializer,
    SubcategorySerializer,
)


class SubcategoryViewSet(ModelViewSet):
    """
    ViewSet for managing subcategories with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting subcategories.
    Subcategories are filtered by the authenticated user and belong to a Category.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SubcategorySerializer

    def get_queryset(self) -> QuerySet[Subcategory]:  # type: ignore
        """
        Get queryset filtered by the authenticated user.

        Returns:
            QuerySet of subcategories belonging to the authenticated user
        """
        return Subcategory.objects.filter(user=self.request.user, is_active=True)

    def get_serializer_class(self) -> Type[serializers.BaseSerializer]:
        """
        Return appropriate serializer class based on the action.

        Returns:
            The appropriate serializer class
        """
        if self.action == "list":
            return SubcategoryListSerializer
        elif self.action == "retrieve":
            return SubcategoryDetailSerializer
        return SubcategorySerializer

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """
        Automatically set the user when creating a subcategory.

        Args:
            serializer: The subcategory serializer instance
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["subcategories"],
        summary="List subcategories",
        description="Retrieve a list of subcategories for the authenticated user",
        parameters=[
            OpenApiParameter(
                name="category",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by category ID",
                examples=[
                    OpenApiExample("Category ID", value="1"),
                ],
            ),
        ],
        responses={200: SubcategoryListSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List subcategories with optional filtering.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with list of subcategories
        """
        queryset = self.get_queryset()

        category_param = request.query_params.get("category")
        if category_param:
            try:
                category_id = int(category_param)
                queryset = queryset.filter(category_id=category_id)
            except ValueError:
                pass

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["subcategories"],
        summary="Create subcategory",
        description="Create a new subcategory for the authenticated user",
        request=SubcategorySerializer,
        responses={201: SubcategorySerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new subcategory.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created subcategory
        """
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["subcategories"],
        summary="Retrieve subcategory",
        description="Retrieve detailed information about a specific subcategory",
        responses={200: SubcategoryDetailSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific subcategory.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with subcategory details
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["subcategories"],
        summary="Update subcategory",
        description="Update an existing subcategory",
        request=SubcategorySerializer,
        responses={200: SubcategorySerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a subcategory.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated subcategory
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["subcategories"],
        summary="Partial update subcategory",
        description="Partially update an existing subcategory",
        request=SubcategorySerializer,
        responses={200: SubcategorySerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a subcategory.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated subcategory
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["subcategories"],
        summary="Delete subcategory",
        description="Soft delete a subcategory (sets is_active to False)",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Soft delete a subcategory by setting is_active to False.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        subcategory = self.get_object()
        subcategory.is_active = False
        subcategory.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

