# Generated by Django 5.2.3 on 2025-06-29 03:32

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
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
                        help_text="Descriptive name for the account (e.g., 'Checking Account Bank X')",
                        max_length=100,
                    ),
                ),
                (
                    "current_balance",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        help_text="Current balance of the account. Updated automatically when transactions are created/edited/deleted.",
                        max_digits=15,
                    ),
                ),
                (
                    "account_type",
                    models.CharField(
                        choices=[("checking", "Checking Account")],
                        default="checking",
                        help_text="Type of account (checking, savings, investment, etc.)",
                        max_length=20,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[("BRL", "Brazilian Real")],
                        default="BRL",
                        help_text="Currency of the account",
                        max_length=3,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date and time when the account was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Date and time when the account was last updated",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether the account is active and can be used for transactions",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="The owner of this account",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Account",
                "verbose_name_plural": "Accounts",
                "db_table": "accounts",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["user", "is_active"], name="accounts_user_id_bfbe44_idx"
                    ),
                    models.Index(
                        fields=["account_type"], name="accounts_account_8fba74_idx"
                    ),
                ],
            },
        ),
    ]
