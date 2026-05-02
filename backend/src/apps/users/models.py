from django.contrib.auth.models import User
from django.db import models


class UserNote(models.Model):
    """Stores a single editable note per user."""

    id: int
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="note")
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Note"
        verbose_name_plural = "User Notes"
