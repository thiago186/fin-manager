from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models.cash_flow_view import CashFlowView
from apps.accounts.serializers import CashFlowReportSerializer, CashFlowViewSerializer
from apps.accounts.services.cash_flow_report_service import CashFlowReportService


class CashFlowViewViewSet(ModelViewSet):
    """
    ViewSet for managing cash flow views with CRUD operations.

    Provides endpoints for creating, reading, updating, and deleting cash flow views.
    Views are filtered by the authenticated user and can contain groups and results.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CashFlowViewSerializer

    def get_queryset(self) -> QuerySet[CashFlowView]:  # type: ignore
        """
        Get queryset filtered by the authenticated user.

        Returns:
            QuerySet of cash flow views belonging to the authenticated user
        """
        return CashFlowView.objects.filter(user=self.request.user).prefetch_related(
            "groups__categories", "results"
        )

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        """
        Automatically set the user when creating a cash flow view.

        Args:
            serializer: The cash flow view serializer instance
        """
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="List cash flow views",
        description="Retrieve a list of cash flow views for the authenticated user",
        responses={200: CashFlowViewSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List cash flow views.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with list of cash flow views
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="Create cash flow view",
        description="Create a new cash flow view for the authenticated user",
        request=CashFlowViewSerializer,
        responses={201: CashFlowViewSerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new cash flow view.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created cash flow view
        """
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="Retrieve cash flow view",
        description="Retrieve detailed information about a specific cash flow view",
        responses={200: CashFlowViewSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific cash flow view.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with cash flow view details
        """
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="Update cash flow view",
        description="Update an existing cash flow view (full replace)",
        request=CashFlowViewSerializer,
        responses={200: CashFlowViewSerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a cash flow view.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated cash flow view
        """
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="Partial update cash flow view",
        description="Partially update an existing cash flow view",
        request=CashFlowViewSerializer,
        responses={200: CashFlowViewSerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a cash flow view.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated cash flow view
        """
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="Delete cash flow view",
        description="Delete a cash flow view",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a cash flow view.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=["cash-flow-views"],
        summary="Get cash flow report",
        description=(
            "Generate a cash flow report for a specific view and year. "
            "Returns monthly aggregated data for all groups and results."
        ),
        parameters=[
            OpenApiParameter(
                name="year",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Year to generate the report for (e.g., 2025)",
                required=True,
            ),
        ],
        responses={200: CashFlowReportSerializer},
    )
    @action(detail=True, methods=["get"], url_path="report")
    def report(self, request: Request, pk: int | None = None) -> Response:
        """
        Generate a cash flow report for a specific view and year.

        Args:
            request: The HTTP request
            pk: The primary key of the cash flow view

        Returns:
            Response with report data including monthly totals
        """
        view = self.get_object()
        year_param = request.query_params.get("year")

        if not year_param:
            return Response(
                {"error": "Year parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            year = int(year_param)
        except ValueError:
            return Response(
                {"error": "Year must be a valid integer"}, status=status.HTTP_400_BAD_REQUEST
            )

        if year < 1900 or year > 2100:
            return Response(
                {"error": "Year must be between 1900 and 2100"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = CashFlowReportService(user=request.user)
        report_data = service.generate_report(view, year)

        serializer = CashFlowReportSerializer(data=report_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

