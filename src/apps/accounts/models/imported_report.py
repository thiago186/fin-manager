from typing import Any

from django.contrib.auth.models import User
from django.db import models

from apps.accounts.models.account import Account
from apps.accounts.models.credit_card import CreditCard


class ImportedReport(models.Model):
    """Represents a CSV import report with status tracking."""

    class Status(models.TextChoices):
        """Import report status choices."""

        SENT = "SENT", "Sent"
        PROCESSING = "PROCESSING", "Processing"
        IMPORTED = "IMPORTED", "Imported"
        FAILED = "FAILED", "Failed"

    id: int

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="imported_reports",
        help_text="The user who uploaded this import",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imported_reports",
        help_text="Bank account to associate with all imported transactions",
    )
    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imported_reports",
        help_text="Credit card to associate with all imported transactions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SENT,
        help_text="Current status of the import",
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Original filename of the uploaded CSV file",
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Storage path/key returned by file storage service",
    )
    handler_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Handler class name used for processing (e.g., BancoInterCreditCardCsvHandler)",
    )
    failed_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Error details if import failed",
    )
    success_count = models.IntegerField(
        default=0,
        help_text="Number of successfully imported transactions",
    )
    error_count = models.IntegerField(
        default=0,
        help_text="Number of failed transactions",
    )
    errors: dict[str, Any] = models.JSONField(
        default=list,
        help_text="List of error messages for failed transactions",
    )  # type: ignore
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the import was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when the import was last updated",
    )
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time when processing completed",
    )

    class Meta:
        """Meta options for the ImportedReport model."""

        db_table = "imported_reports"
        ordering = ["-created_at"]
        verbose_name = "Imported Report"
        verbose_name_plural = "Imported Reports"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """String representation of the import report."""
        return f"{self.file_name} - {self.status} ({self.user.username})"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"ImportedReport(id={self.pk}, file_name='{self.file_name}', "
            f"status='{self.status}', user_id={self.user.pk})"
        )
