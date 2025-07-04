# Generated by Django 5.2.3 on 2025-06-29 03:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_creditcard"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Name of the category (e.g., 'Transportation', 'Food', 'Salary')",
                        max_length=100,
                    ),
                ),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[
                            ("income", "Income"),
                            ("expense", "Expense"),
                            ("both", "Both Income and Expense"),
                        ],
                        default="both",
                        help_text="Type of transactions this category is used for",
                        max_length=10,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="Optional description of the category"
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        blank=True,
                        help_text="Hex color code for UI display (e.g., '#FF5733')",
                        max_length=7,
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        blank=True,
                        help_text="Icon identifier for UI display",
                        max_length=50,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date and time when the category was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Date and time when the category was last updated",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether the category is active and can be used for transactions",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        help_text="Parent category. If null, this is a top-level category.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategories",
                        to="accounts.category",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="The owner of this category",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Category",
                "verbose_name_plural": "Categories",
                "db_table": "categories",
                "ordering": ["name"],
                "indexes": [
                    models.Index(
                        fields=["user", "is_active"],
                        name="categories_user_id_51102f_idx",
                    ),
                    models.Index(
                        fields=["parent"], name="categories_parent__7983b2_idx"
                    ),
                    models.Index(
                        fields=["transaction_type"],
                        name="categories_transac_0692be_idx",
                    ),
                ],
                "unique_together": {("user", "name", "parent")},
            },
        ),
    ]
