import structlog
from typing import Type

from apps.accounts.interfaces.xlsx_handler import BaseXlsxHandler
from apps.accounts.transactions_handlers.bb_bank_statement_xlsx_handler import (
    BBBankStatementXlsxHandler,
)

logger = structlog.stdlib.get_logger()


class XLSXImportFactory:
    """Factory for creating appropriate XLSX handlers based on file format detection."""

    # Registry of format handlers (order matters - more specific handlers first)
    _handlers: list[Type[BaseXlsxHandler]] = [
        BBBankStatementXlsxHandler,
    ]

    @classmethod
    def create_handler(cls, xlsx_file_path: str) -> BaseXlsxHandler:
        """Create appropriate XLSX handler based on format detection.

        Iterates through registered handlers in order and returns the first one
        that can handle the file. Handlers are responsible for their own
        detection logic.

        Args:
            xlsx_file_path: Path to the XLSX file.

        Returns:
            Appropriate XLSX handler instance.

        Raises:
            ValueError: If no suitable handler can be determined.
        """
        for handler_class in cls._handlers:
            handler_instance = handler_class()
            try:
                if handler_instance.can_handle_file(xlsx_file_path):
                    logger.debug(
                        "Using handler",
                        handler_type=handler_class.__name__,
                        file_path=xlsx_file_path,
                    )
                    return handler_instance
                else:
                    logger.debug(
                        "Handler cannot handle file",
                        handler_type=handler_class.__name__,
                        file_path=xlsx_file_path,
                    )
            except Exception as e:
                logger.debug(
                    "Handler raised error during detection",
                    handler_type=handler_class.__name__,
                    file_path=xlsx_file_path,
                    error=str(e),
                )
                continue

        raise ValueError(
            f"No handler could process XLSX file: {xlsx_file_path}"
        )
