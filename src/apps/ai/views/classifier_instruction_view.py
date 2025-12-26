"""ViewSet for AI Classifier Instruction singleton operations."""

from typing import Any

from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.ai.models import AIClassifierInstruction
from apps.ai.serializers import AIClassifierInstructionSerializer


class AIClassifierInstructionViewSet(ModelViewSet):
    """
    ViewSet for managing the user's AI Classifier Instruction (singleton).

    Each user has exactly one classifier instruction. Provides endpoints for
    retrieving, updating, and deleting the instruction.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AIClassifierInstructionSerializer

    def get_object(self) -> AIClassifierInstruction:
        """
        Get the classifier instruction for the authenticated user.

        Returns:
            The user's classifier instruction

        Raises:
            Http404: If the instruction does not exist
        """
        try:
            return AIClassifierInstruction.objects.get(user=self.request.user)
        except AIClassifierInstruction.DoesNotExist:
            raise Http404("Classifier instruction not found")

    @extend_schema(
        tags=["AI"],
        summary="Get classifier instruction",
        description="Retrieve the classifier instruction for the authenticated user (singleton)",
        responses={
            200: AIClassifierInstructionSerializer,
        },
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve the user's classifier instruction (singleton pattern).

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with classifier instruction details or empty dict if not found
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response({})

    @extend_schema(
        tags=["AI"],
        summary="Create or update classifier instruction",
        description="Create a new classifier instruction or update existing one for the authenticated user",
        request=AIClassifierInstructionSerializer,
        responses={
            200: AIClassifierInstructionSerializer,
            201: AIClassifierInstructionSerializer,
        },
    )
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create or update the user's classifier instruction.

        If an instruction already exists for the user, it will be updated.
        Otherwise, a new instruction will be created.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created or updated classifier instruction
        """
        instance = AIClassifierInstruction.objects.filter(user=request.user).first()

        if instance:
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["AI"],
        summary="Get classifier instruction",
        description="Retrieve the classifier instruction for the authenticated user",
        responses={
            200: AIClassifierInstructionSerializer,
        },
    )
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve the user's classifier instruction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with classifier instruction details or empty dict if not found
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response({})

    @extend_schema(
        tags=["AI"],
        summary="Create or update classifier instruction",
        description="Create a new classifier instruction or update existing one",
        request=AIClassifierInstructionSerializer,
        responses={
            200: AIClassifierInstructionSerializer,
            201: AIClassifierInstructionSerializer,
        },
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create or update the user's classifier instruction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with created or updated classifier instruction
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        except Http404:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["AI"],
        summary="Partially update classifier instruction",
        description="Partially update the user's classifier instruction",
        request=AIClassifierInstructionSerializer,
        responses={
            200: AIClassifierInstructionSerializer,
            201: AIClassifierInstructionSerializer,
        },
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update or create the user's classifier instruction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response with updated or created classifier instruction
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        except Http404:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["AI"],
        summary="Delete classifier instruction",
        description="Delete the user's classifier instruction",
        responses={204: None},
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete the user's classifier instruction.

        Args:
            request: The HTTP request
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Empty response with 204 status
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
