from django.contrib.auth.models import User
from django.db import models


class Tag(models.Model):
    """Represents a tag for a transaction.

    The tag is a label that can be applied to a transaction to categorize it.
    It can be used to group transactions by category, purpose, or any other criteria.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tags",
        help_text="The user who owns this tag",
    )
    name = models.CharField(
        max_length=50,
        help_text="The name of the tag",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the tag was created",
    )

    class Meta:
        """Meta options for the Tag model."""

        db_table = "tags"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["-created_at"]
        unique_together = ("user", "name")

    def __str__(self) -> str:
        """Return the string representation of the tag."""
        return self.name
