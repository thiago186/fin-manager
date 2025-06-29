from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet


class Category(models.Model):
    """
    Represents a category for classifying income and expenses.

    Categories can have subcategories, allowing for hierarchical organization.
    For example, a "Transportation" category can have subcategories like "Fuel", "Maintenance", etc.
    """

    class TransactionType(models.TextChoices):
        """Transaction type choices for categorizing income vs expenses."""

        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
        help_text="The owner of this category",
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the category (e.g., 'Transportation', 'Food', 'Salary')",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        help_text="Parent category. If null, this is a top-level category.",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        help_text="Type of transactions this category is used for",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the category",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the category was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the category was last updated",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the category is active and can be used for transactions",
    )

    # Type hints
    id: int
    subcategories: models.Manager["Category"]

    class Meta:
        """Meta options for the Category model."""

        db_table = "categories"
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["transaction_type"]),
        ]
        unique_together = [
            ["user", "name", "parent"],
        ]

    def __str__(self) -> str:
        """String representation of the category."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        parent_name = self.parent.name if self.parent is not None else None
        return f"Category(id={self.id}, name='{self.name}', user_id={self.user.pk}, parent={parent_name})"

    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level category (no parent)."""
        return self.parent is None

    @property
    def is_subcategory(self) -> bool:
        """Check if this is a subcategory (has a parent)."""
        return self.parent is not None

    @property
    def level(self) -> int:
        """Get the hierarchical level of the category (0 for top-level)."""
        if self.parent is None:
            return 0
        return self.parent.level + 1

    def get_all_subcategories(self, only_active: bool = True) -> list["Category"]:
        """
        Get all subcategories recursively (including subcategories of subcategories).

        Args:
            only_active: If True, only return active subcategories. If False, return all subcategories.

        Returns:
            List of all subcategories at any level below this category
        """
        subcategories: list["Category"] = []

        immediate_subcategories = self.subcategories.all()
        if only_active:
            immediate_subcategories = immediate_subcategories.filter(is_active=True)

        for subcategory in immediate_subcategories:
            subcategories.append(subcategory)
            subcategories.extend(subcategory.get_all_subcategories(only_active))

        return subcategories

    def get_ancestors(self) -> list["Category"]:
        """
        Get all ancestor categories from root to parent.

        Returns:
            List of ancestor categories ordered from root to immediate parent
        """
        ancestors: list["Category"] = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_siblings(self) -> QuerySet["Category"]:
        """
        Get categories that share the same parent.

        Returns:
            QuerySet of sibling categories
        """
        if self.parent:
            return self.parent.subcategories.filter(is_active=True).exclude(id=self.id)

        query_set: QuerySet["Category"] = Category.objects.filter(
            parent__isnull=True, is_active=True
        ).exclude(id=self.id)

        return query_set
