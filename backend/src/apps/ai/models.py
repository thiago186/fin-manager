from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class AIClassifierInstruction(models.Model):
    """Represents a classifier instruction for the AI classifier."""

    id: int
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Classifier Instruction"
        verbose_name_plural = "AI Classifier Instructions"
        constraints = [
            models.UniqueConstraint(fields=["user"], name="unique_user_instruction"),
        ]
