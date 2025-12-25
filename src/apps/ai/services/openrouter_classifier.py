"""OpenRouter implementation of AI classifier."""

from typing import Any

import structlog
from django.conf import settings
from openrouter import OpenRouter

from apps.ai.interfaces.ai_classifier import AIClassifierInterface

logger = structlog.get_logger(__name__)


class OpenRouterClassifier(AIClassifierInterface):
    """OpenRouter implementation of the AI classifier interface."""

    def __init__(self) -> None:
        """Initialize the OpenRouter classifier with API configuration."""
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must be set in settings")

        self.api_key = api_key
        self.model = getattr(settings, "OPENROUTER_MODEL", None)

    def classify(self, messages: list[dict[str, Any]]) -> str:
        """Classify transactions using OpenRouter API.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Should include system and user messages already formatted.

        Returns:
            The AI's response as a string (typically JSON)

        Raises:
            Exception: If classification fails
        """
        try:
            total_length = sum(len(msg.get("content", "")) for msg in messages)
            logger.info(
                "Calling OpenRouter API for classification",
                model=self.model,
                messages_count=len(messages),
                total_content_length=total_length,
            )

            with OpenRouter(api_key=self.api_key) as client:
                response = client.chat.send(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    response_format={"type": "json_object"},
                    timeout_ms=30 * 100,
                )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenRouter API")

            result = str(content)

            logger.info(
                "OpenRouter API call successful",
                model=self.model,
                response_length=len(result),
            )

            return result

        except Exception as e:
            logger.error(
                "OpenRouter API call failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
