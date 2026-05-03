from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.db import transaction as db_transaction

from apps.accounts.models.installment_plan import InstallmentPlan
from apps.accounts.models.transaction import Transaction


class InstallmentUpdateService:
    """Updates an installment plan and all its transactions when any plan
    transaction is edited.

    Structural fields (amount, installments_total, occurred_at, account,
    credit_card, category, subcategory, transaction_type) are cascaded to all
    transactions in the plan.  Description and tags are left untouched on
    siblings.
    """

    def update_plan_from_transaction(
        self,
        plan: InstallmentPlan,
        trigger_transaction: Transaction,
        changed_fields: dict[str, Any],
    ) -> None:
        """Synchronize the entire installment plan after a transaction edit.

        Args:
            plan: The InstallmentPlan to update.
            trigger_transaction: The transaction that triggered the update.
            changed_fields: Dict of field names -> new values that changed.
        """
        with db_transaction.atomic():
            # Order matters: count first, then amount, then dates, then structural.
            if "installments_total" in changed_fields:
                self._apply_count_change(plan, changed_fields["installments_total"])

            if "amount" in changed_fields:
                self._apply_amount_change(plan, changed_fields["amount"])

            if "occurred_at" in changed_fields:
                self._apply_date_change(plan, trigger_transaction, changed_fields["occurred_at"])

            self._apply_structural_changes(plan, changed_fields)

            plan.save()

    def _apply_count_change(self, plan: InstallmentPlan, new_count: int) -> None:
        """Add or remove transactions to match the new installment count."""
        old_count = plan.installments_count

        if new_count > old_count:
            self._add_transactions(plan, new_count)
        elif new_count < old_count:
            self._remove_transactions(plan, new_count)

        plan.installments_count = new_count
        plan.total_amount = plan.installment_amount * Decimal(new_count)

    def _add_transactions(self, plan: InstallmentPlan, new_count: int) -> None:
        """Create new transactions to reach *new_count* installments."""
        existing = list(
            plan.transactions.order_by("installment_number").values_list(  # type: ignore[attr-defined]
                "installment_number", "occurred_at", flat=False
            )
        )
        last_txn = plan.transactions.order_by("installment_number").last()  # type: ignore[attr-defined]

        for i in range(plan.installments_count + 1, new_count + 1):
            occurred_at = last_txn.occurred_at + relativedelta(months=(i - plan.installments_count))

            txn = Transaction(
                user=plan.user,
                transaction_type=plan.transaction_type,
                amount=plan.installment_amount,
                description=plan.description,
                occurred_at=occurred_at,
                installments_total=new_count,
                installment_number=i,
                installment_group_id=last_txn.installment_group_id,
                installment_plan=plan,
                account=plan.account,
                credit_card=plan.credit_card,
                category=plan.category,
                subcategory=plan.subcategory,
                origin="manual",
            )
            txn.save()

        # Update installments_total on all existing transactions
        plan.transactions.filter(installment_number__lte=plan.installments_count).update(  # type: ignore[attr-defined]
            installments_total=new_count
        )

    def _remove_transactions(self, plan: InstallmentPlan, new_count: int) -> None:
        """Delete transactions whose number exceeds *new_count*."""
        plan.transactions.filter(installment_number__gt=new_count).delete()  # type: ignore[attr-defined]

        # Update installments_total on the remaining transactions
        plan.transactions.update(installments_total=new_count)  # type: ignore[attr-defined]

    def _apply_amount_change(self, plan: InstallmentPlan, new_amount: Decimal) -> None:
        """Set the same amount on every transaction and recalc plan totals."""
        plan.installment_amount = new_amount
        plan.total_amount = new_amount * Decimal(plan.installments_count)

        for txn in plan.transactions.all():  # type: ignore[attr-defined]
            txn.amount = new_amount
            txn.save(update_fields=["amount", "updated_at"])

    def _apply_date_change(
        self,
        plan: InstallmentPlan,
        trigger_transaction: Transaction,
        new_date: Any,
    ) -> None:
        """Shift the trigger transaction and all subsequent ones by month."""
        trigger_transaction.occurred_at = new_date
        trigger_transaction.save(update_fields=["occurred_at", "updated_at"])

        # Shift all subsequent transactions
        subsequent = plan.transactions.filter(  # type: ignore[attr-defined]
            installment_number__gt=trigger_transaction.installment_number
        ).order_by("installment_number")

        for txn in subsequent:
            months_delta = txn.installment_number - trigger_transaction.installment_number
            txn.occurred_at = new_date + relativedelta(months=months_delta)
            txn.save(update_fields=["occurred_at", "updated_at"])

        # Update plan.first_due_date from transaction 1
        first = plan.transactions.filter(installment_number=1).first()  # type: ignore[attr-defined]
        if first:
            plan.first_due_date = first.occurred_at

    def _apply_structural_changes(
        self, plan: InstallmentPlan, changed_fields: dict[str, Any]
    ) -> None:
        """Cascade account, credit_card, category, subcategory, transaction_type."""
        structural_fields = [
            "account",
            "credit_card",
            "category",
            "subcategory",
            "transaction_type",
        ]

        plan_modified = False
        for field in structural_fields:
            if field in changed_fields:
                setattr(plan, field, changed_fields[field])
                plan_modified = True

        # Enforce account/credit_card mutual exclusivity on the plan
        if "account" in changed_fields and plan.account and plan.credit_card:
            plan.credit_card = None
        if "credit_card" in changed_fields and plan.credit_card and plan.account:
            plan.account = None

        if plan_modified:
            update_fields = []
            for field in structural_fields:
                if field in changed_fields:
                    update_fields.append(field)
            update_fields.append("updated_at")

            for txn in plan.transactions.all():  # type: ignore[attr-defined]
                for field in structural_fields:
                    if field in changed_fields:
                        setattr(txn, field, changed_fields[field])
                # Enforce mutual exclusivity on each transaction too
                if "account" in changed_fields and txn.account and txn.credit_card:
                    txn.credit_card = None
                if "credit_card" in changed_fields and txn.credit_card and txn.account:
                    txn.account = None
                txn.save(update_fields=update_fields)
