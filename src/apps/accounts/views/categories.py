from typing import Any, Type

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.categories import Category
from apps.accounts.serializers import (
    CategoryDetailSerializer,
    CategoryListSerializer,
    CategorySerializer,
)


class CategoryViewSet(ModelViewSet):
    """
    ViewSet for managing categories with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting categories.
    Categories are filtered by the authenticated user and can be organized hierarchically.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self) -> QuerySet[Category]:  # type: ignore
        """
        Get queryset filtered by the authenticated user.

        Returns:
            QuerySet of categories belonging to the authenticated user
        """
        return Category.objects.filter(user=self.request.user, is_active=True)

    def get_serializer_class(self) -> Type[serializers.BaseSerializer]:
        """
        Return appropriate serializer class based on the action.

        Returns:
            The appropriate serializer class
        """
        if self.action == "list":
            return CategoryListSerializer
        elif self.action == "retrieve":
            return CategoryDetailSerializer
        return CategorySerializer

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """
        Automatically set the user when creating a category.

        Args:
            serializer: The category serializer instance
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["categories"],
        summary="List categories",
        description="Retrieve a list of categories for the authenticated user",
        parameters=[
            OpenApiParameter(
                name="transaction_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by transaction type (income/expense)",
                examples=[
                    OpenApiExample("Income", value="income"),
                    OpenApiExample("Expense", value="expense"),
                ],
            ),
            OpenApiParameter(
                name="parent",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter by parent category ID (null for top-level)",
                examples=[
                    OpenApiExample("Top-level", value="null"),
                    OpenApiExample("With parent", value="1"),
                ],
            ),
        ],
        responses={200: CategoryListSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List categories with optional filtering.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with list of categories
        """
        queryset = self.get_queryset()

        transaction_type = request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        parent_param = request.query_params.get("parent")
        if parent_param == "null":
            queryset = queryset.filter(parent__isnull=True)
        elif parent_param:
            try:
                parent_id = int(parent_param)
                queryset = queryset.filter(parent_id=parent_id)
            except ValueError:
                pass

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["categories"],
        summary="Create category",
        description="Create a new category for the authenticated user",
        request=CategorySerializer,
        responses={201: CategorySerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new category.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created category
        """
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["categories"],
        summary="Retrieve category",
        description="Retrieve detailed information about a specific category",
        responses={200: CategoryDetailSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific category.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with category details
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["categories"],
        summary="Update category",
        description="Update an existing category",
        request=CategorySerializer,
        responses={200: CategorySerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a category.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated category
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["categories"],
        summary="Partial update category",
        description="Partially update an existing category",
        request=CategorySerializer,
        responses={200: CategorySerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a category.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated category
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["categories"],
        summary="Delete category",
        description="Soft delete a category (sets is_active to False)",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Soft delete a category by setting is_active to False.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        category = self.get_object()
        category.is_active = False
        category.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["categories"],
        summary="List top-level categories",
        description="Retrieve only top-level categories (no parent)",
        responses={200: CategoryListSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def top_level(self, request: Request) -> Response:
        """
        Get only top-level categories.

        Args:
            request: The HTTP request

        Returns:
            Response with list of top-level categories
        """
        queryset = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["categories"],
        summary="List subcategories",
        description="Retrieve subcategories of a specific category",
        parameters=[
            OpenApiParameter(
                name="category_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the parent category",
            ),
        ],
        responses={200: CategoryListSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def subcategories(self, request: Request, pk: int | None = None) -> Response:
        """
        Get subcategories of a specific category.

        Args:
            request: The HTTP request
            pk: The primary key of the parent category

        Returns:
            Response with list of subcategories
        """
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True)
        serializer = CategoryListSerializer(subcategories, many=True)
        return Response(serializer.data)
