from django.contrib.auth import authenticate, login, logout
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import (
    AuthResponseSerializer,
    LoginSerializer,
    UserResponseSerializer,
    UserSerializer,
)


@extend_schema(
    tags=["Users"],
    summary="Create a new user",
    description="Register a new user account with username and password",
    request=UserSerializer,
    responses={
        201: OpenApiResponse(
            description="User created successfully",
            response=UserResponseSerializer,
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={
                        "id": 1,
                        "username": "john_doe",
                        "email": "",
                        "first_name": "",
                        "last_name": "",
                        "date_joined": "2024-01-01T00:00:00Z",
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad request - validation errors",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    value={
                        "username": ["This field is required."],
                        "password": ["This field is required."],
                    },
                )
            ],
        ),
    },
    examples=[
        OpenApiExample(
            "Create User",
            value={"username": "john_doe", "password": "secure_password123"},
        )
    ],
)
class UserCreate(APIView):
    def post(self, request: Request) -> Response:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserResponseSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Users"],
    summary="User login",
    description="Authenticate user with username and password",
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful",
            response=AuthResponseSerializer,
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={
                        "message": "Login successful",
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "date_joined": "2024-01-01T00:00:00Z",
                        },
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Invalid credentials",
            examples=[
                OpenApiExample(
                    "Invalid Credentials",
                    value={"error": "Invalid username or password"},
                )
            ],
        ),
    },
    examples=[
        OpenApiExample(
            "Login Request",
            value={"username": "john_doe", "password": "secure_password123"},
        )
    ],
)
class LoginView(APIView):
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            response_data = {
                "message": "Login successful",
                "user": UserResponseSerializer(user).data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Invalid username or password"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema(
    tags=["Users"],
    summary="User logout",
    description="Logout the currently authenticated user",
    responses={
        200: OpenApiResponse(
            description="Logout successful",
            examples=[
                OpenApiExample(
                    "Success Response", value={"message": "Logout successful"}
                )
            ],
        ),
        401: OpenApiResponse(
            description="Unauthorized - user not authenticated",
            examples=[
                OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                )
            ],
        ),
    },
)
class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Users"],
    summary="Check authentication status",
    description="Verify if the current user is authenticated and return user information",
    responses={
        200: OpenApiResponse(
            description="User is authenticated",
            response=UserResponseSerializer,
            examples=[
                OpenApiExample(
                    "Authenticated User",
                    value={
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "date_joined": "2024-01-01T00:00:00Z",
                    },
                )
            ],
        ),
        401: OpenApiResponse(
            description="User is not authenticated",
            examples=[
                OpenApiExample(
                    "Unauthorized",
                    value={"detail": "Authentication credentials were not provided."},
                )
            ],
        ),
    },
)
class CheckAuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
