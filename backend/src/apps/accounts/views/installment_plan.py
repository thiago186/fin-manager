from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, mixins

from apps.accounts.models.installment_plan import InstallmentPlan
from apps.accounts.serializers import TransactionSerializer
from apps.accounts.serializers.installment_plan import (
    InstallmentPlanCreateSerializer,
    InstallmentPlanSerializer,
)
from apps.accounts.services.installment_service import InstallmentService


class InstallmentPlanViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """ViewSet for managing installment plans."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[InstallmentPlan]:
        """Return plans belonging to the authenticated user."""
        return (
            InstallmentPlan.objects.filter(user=self.request.user)
            .select_related("account", "credit_card", "category", "subcategory")
            .prefetch_related("transactions")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return InstallmentPlanCreateSerializer
        return InstallmentPlanSerializer

    @extend_schema(
        tags=["installment-plans"],
        summary="Create installment plan",
        description=(
            "Create an installment plan and automatically generate all installment transactions. "
            "Provide either total_amount (with input_mode='total_and_count') or "
            "installment_amount (with input_mode='installment_and_count')."
        ),
        request=InstallmentPlanCreateSerializer,
        responses={201: InstallmentPlanSerializer},
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create an installment plan and generate all its transactions."""
        serializer = InstallmentPlanCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = InstallmentService()
        plan, _ = service.create_plan_with_transactions(
            user=request.user,
            description=data.get("description"),
            transaction_type=data["transaction_type"],
            total_amount=data.get("total_amount"),
            installment_amount=data.get("installment_amount"),
            installments_count=data["installments_count"],
            first_due_date=data["first_due_date"],
            account=data.get("account"),
            credit_card=data.get("credit_card"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
        )

        output = InstallmentPlanSerializer(plan, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["installment-plans"],
        summary="List installment plans",
        responses={200: InstallmentPlanSerializer(many=True)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """List all installment plans for the authenticated user."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["installment-plans"],
        summary="Retrieve installment plan",
        responses={200: InstallmentPlanSerializer},
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a specific installment plan."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["installment-plans"],
        summary="Delete installment plan",
        description="Delete an installment plan and all its linked transactions.",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete an installment plan and cascade-delete its transactions."""
        plan = self.get_object()
        plan.transactions.all().delete()
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["installment-plans"],
        summary="List plan transactions",
        description="Retrieve all transactions linked to this installment plan, ordered by installment number.",
        responses={200: TransactionSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="transactions")
    def transactions(self, request: Request, pk: int | None = None) -> Response:
        """List all transactions for the given installment plan."""
        plan = self.get_object()
        qs = (
            plan.transactions.select_related(
                "account", "credit_card", "category", "subcategory"
            )
            .prefetch_related("tags")
            .order_by("installment_number")
        )
        serializer = TransactionSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
