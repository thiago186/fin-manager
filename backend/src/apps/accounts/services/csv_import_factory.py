import structlog
from typing import Type

from apps.accounts.interfaces.csv_handler import BaseCSVHandler
from apps.accounts.transactions_handlers.banco_inter_bank_statement_csv_handler import (
    BancoInterBankStatementCsvHandler,
)
from apps.accounts.transactions_handlers.banco_inter_credit_card_csv_handler import (
    BancoInterCreditCardCsvHandler,
)
from apps.accounts.transactions_handlers.default_csv_handler import DefaultCSVHandler

logger = structlog.stdlib.get_logger()


class CSVImportFactory:
    """Factory for creating appropriate CSV handlers based on file format detection."""

    # Registry of format handlers (order matters - more specific handlers first)
    _handlers: list[Type[BaseCSVHandler]] = [
        BancoInterBankStatementCsvHandler,
        BancoInterCreditCardCsvHandler,
        DefaultCSVHandler,
    ]

    @classmethod
    def create_handler(cls, csv_file_path: str) -> BaseCSVHandler:
        """Create appropriate CSV handler based on format detection.

        Iterates through registered handlers in order and returns the first one
        that can handle the file. Handlers are responsible for their own
        detection logic.

        Args:
            csv_file_path: Path to the CSV file.

        Returns:
            Appropriate CSV handler instance.

        Raises:
            ValueError: If no suitable handler can be determined.
        """
        for handler_class in cls._handlers:
            handler_instance = handler_class()
            try:
                if handler_instance.can_handle_file(csv_file_path):
                    logger.debug(
                        "Using handler",
                        handler_type=handler_class.__name__,
                        file_path=csv_file_path,
                    )
                    return handler_instance
                else:
                    logger.debug(
                        "Handler cannot handle file",
                        handler_type=handler_class.__name__,
                        file_path=csv_file_path,
                    )
            except Exception as e:
                logger.debug(
                    "Handler raised error during detection",
                    handler_type=handler_class.__name__,
                    file_path=csv_file_path,
                    error=str(e),
                )
                continue

        logger.warning(
            "No handler could process file, using default handler",
            file_path=csv_file_path,
        )
        return DefaultCSVHandler()
