import uuid
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import transaction as db_transaction

from apps.accounts.models.installment_plan import InstallmentPlan
from apps.accounts.models.transaction import Transaction


class InstallmentService:
    """Creates an installment plan and generates all related transactions atomically."""

    def create_plan_with_transactions(
        self,
        user: User,
        description: str | None,
        transaction_type: str,
        total_amount: Decimal | None,
        installment_amount: Decimal | None,
        installments_count: int,
        first_due_date: object,
        account: object | None,
        credit_card: object | None,
        category: object | None,
        subcategory: object | None,
    ) -> tuple[InstallmentPlan, list[Transaction]]:
        """Create an installment plan and all its transactions in a single atomic operation.

        Accepts either total_amount or installment_amount; the other is derived.
        Rounding remainder (cent difference) is absorbed by the first installment.

        Args:
            user: The owning user.
            description: Optional purchase description.
            transaction_type: One of Transaction.TransactionType values.
            total_amount: Full purchase amount (provide this or installment_amount).
            installment_amount: Per-installment amount (provide this or total_amount).
            installments_count: Number of installments to create.
            first_due_date: Date of the first installment.
            account: Optional Account instance.
            credit_card: Optional CreditCard instance.
            category: Optional Category instance.
            subcategory: Optional Subcategory instance.

        Returns:
            Tuple of (InstallmentPlan, list of created Transactions).
        """
        cent = Decimal("0.01")

        if total_amount is not None:
            base_installment = (total_amount / installments_count).quantize(
                cent, rounding=ROUND_HALF_UP
            )
            # Recalculate total from base to find rounding remainder
            remainder = total_amount - (base_installment * installments_count)
            first_installment_amount = (base_installment + remainder).quantize(cent)
            derived_total = total_amount
        else:
            base_installment = installment_amount.quantize(cent, rounding=ROUND_HALF_UP)  # type: ignore[union-attr]
            first_installment_amount = base_installment
            derived_total = (base_installment * installments_count).quantize(cent)

        plan = InstallmentPlan(
            user=user,
            description=description,
            transaction_type=transaction_type,
            total_amount=derived_total,
            installment_amount=base_installment,
            installments_count=installments_count,
            first_due_date=first_due_date,
            account=account,
            credit_card=credit_card,
            category=category,
            subcategory=subcategory,
        )
        plan.full_clean()

        group_id = str(uuid.uuid4())

        with db_transaction.atomic():
            plan.save()

            transactions: list[Transaction] = []
            for i in range(installments_count):
                amount = first_installment_amount if i == 0 else base_installment
                occurred_at = first_due_date + relativedelta(months=i)

                txn = Transaction(
                    user=user,
                    transaction_type=transaction_type,
                    amount=amount,
                    description=description,
                    occurred_at=occurred_at,
                    installments_total=installments_count,
                    installment_number=i + 1,
                    installment_group_id=group_id,
                    installment_plan=plan,
                    account=account,
                    credit_card=credit_card,
                    category=category,
                    subcategory=subcategory,
                    origin="manual",
                )
                txn.save()
                transactions.append(txn)

        return plan, transactions
