from django.contrib import admin

from apps.ai.models import AIClassifierInstruction


@admin.register(AIClassifierInstruction)
class AIClassifierInstructionAdmin(admin.ModelAdmin):
    """Admin configuration for AI Classifier Instructions."""

    list_display = ("id", "user", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "user__email", "instructions")
    readonly_fields = ("created_at", "updated_at")
    fields = ("user", "instructions", "created_at", "updated_at")
