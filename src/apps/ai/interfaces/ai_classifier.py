"""Interface for AI classifiers."""

from abc import ABC, abstractmethod
from typing import Any


class AIClassifierInterface(ABC):
    """Abstract interface for AI classifiers."""

    @abstractmethod
    def classify(self, messages: list[dict[str, Any]]) -> str:
        """Classify transactions based on the provided messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Should include system and user messages already formatted.

        Returns:
            The AI's response as a string (typically JSON)

        Raises:
            Exception: If classification fails
        """
        pass
