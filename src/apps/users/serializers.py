from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        """
        Meta class for UserSerializer.
        """

        model = User
        fields = ["username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data: dict) -> User:
        """
        Create a new user.
        """
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="User's username")
    password = serializers.CharField(help_text="User's password", write_only=True)

    class Meta:
        extra_kwargs = {
            "username": {"example": "john_doe"},
            "password": {"example": "secure_password123"},
        }


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class AuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Authentication status message")
    user = UserResponseSerializer(help_text="User information")

    class Meta:
        extra_kwargs = {"message": {"example": "Authentication successful"}}
