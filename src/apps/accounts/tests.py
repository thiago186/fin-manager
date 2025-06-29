# Create your tests here.

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.response import Response

from apps.accounts.models.categories import Category


class CategoryAPITestCase(TestCase):
    """Test cases for Category API endpoints."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_category(self) -> None:
        """Test creating a new category."""
        data = {
            "name": "Transportation",
            "transaction_type": "expense",
            "description": "Transportation expenses",
        }
        response = self.client.post("/api/v1/accounts/categories/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        category = Category.objects.first()
        assert category is not None
        self.assertEqual(category.name, "Transportation")
        self.assertEqual(category.user, self.user)

    def test_list_categories(self) -> None:
        """Test listing categories."""
        Category.objects.create(
            user=self.user,
            name="Food",
            transaction_type="expense",
        )
        Category.objects.create(
            user=self.user,
            name="Salary",
            transaction_type="income",
        )
        response = self.client.get("/api/v1/accounts/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_transaction_type(self) -> None:
        """Test filtering categories by transaction type."""
        Category.objects.create(
            user=self.user,
            name="Food",
            transaction_type="expense",
        )
        Category.objects.create(
            user=self.user,
            name="Salary",
            transaction_type="income",
        )
        response = self.client.get(
            "/api/v1/accounts/categories/?transaction_type=expense"
        )
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Food")

    def test_top_level_categories(self) -> None:
        """Test getting only top-level categories."""
        parent = Category.objects.create(
            user=self.user,
            name="Transportation",
            transaction_type="expense",
        )
        Category.objects.create(
            user=self.user,
            name="Fuel",
            transaction_type="expense",
            parent=parent,
        )
        response = self.client.get("/api/v1/accounts/categories/top_level/")
        self.assertIsInstance(response.data, list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Transportation")

    def test_soft_delete(self) -> None:
        """Test soft deleting a category."""
        category = Category.objects.create(
            user=self.user,
            name="Test Category",
            transaction_type="expense",
        )
        response = self.client.delete(f"/api/v1/accounts/categories/{category.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        category.refresh_from_db()
        self.assertFalse(category.is_active)
