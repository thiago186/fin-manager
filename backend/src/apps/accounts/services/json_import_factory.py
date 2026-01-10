import structlog
from typing import Type

from apps.accounts.interfaces.json_handler import BaseJsonHandler
from apps.accounts.transactions_handlers.default_json_handler import DefaultJsonHandler

logger = structlog.stdlib.get_logger()


class JSONImportFactory:
    """Factory for creating appropriate JSON handlers based on file format detection."""

    # Registry of format handlers (order matters - more specific handlers first)
    _handlers: list[Type[BaseJsonHandler]] = [
        DefaultJsonHandler,
    ]

    @classmethod
    def create_handler(cls, json_file_path: str) -> BaseJsonHandler:
        """Create appropriate JSON handler based on format detection.

        Iterates through registered handlers in order and returns the first one
        that can handle the file. Handlers are responsible for their own
        detection logic.

        Args:
            json_file_path: Path to the JSON file.

        Returns:
            Appropriate JSON handler instance.

        Raises:
            ValueError: If no suitable handler can be determined.
        """
        for handler_class in cls._handlers:
            handler_instance = handler_class()
            try:
                if handler_instance.can_handle_file(json_file_path):
                    logger.debug(
                        "Using handler",
                        handler_type=handler_class.__name__,
                        file_path=json_file_path,
                    )
                    return handler_instance
                else:
                    logger.debug(
                        "Handler cannot handle file",
                        handler_type=handler_class.__name__,
                        file_path=json_file_path,
                    )
            except Exception as e:
                logger.debug(
                    "Handler raised error during detection",
                    handler_type=handler_class.__name__,
                    file_path=json_file_path,
                    error=str(e),
                )
                continue

        logger.warning(
            "No handler could process file, using default handler",
            file_path=json_file_path,
        )
        return DefaultJsonHandler()
