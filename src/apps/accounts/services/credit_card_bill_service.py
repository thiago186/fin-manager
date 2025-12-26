import os
from django.contrib.auth.models import User

from apps.accounts.interfaces.credit_card_bill_handler import BaseCreditCardBillHandler
from apps.accounts.models import Transaction
from apps.accounts.models.credit_card import CreditCard
from apps.accounts.transactions_handlers import JSONCreditCardHandler


class CreditCardBillImporterService:
    """Service for handling credit card bills."""

    def __init__(self, user: User):
        self.user = user

    def import_transactions(self, filename: str, credit_card: CreditCard) -> None:
        """Handle the credit card bill.

        Args:
            filename: Path to the credit card bill file
            credit_card: CreditCard instance to associate transactions with
        """
        parser = JSONCreditCardHandler()
        transactions = parser.parse_transactions_from_file(filename)
        # Extract filename from path
        origin_filename = os.path.basename(filename)
        for transaction in transactions:
            transaction.user = self.user
            transaction.credit_card = credit_card
            transaction.origin = origin_filename
            transaction.save()


service = CreditCardBillImporterService(user=User.objects.get(id=2))
card = CreditCard.objects.get(id=1)
service.import_transactions(filename="bills/jan.json", credit_card=card)
