"""Match invoices with bank movements by reference. Paid means paid to the cent.

- Without a bank statement nothing is known: the status is UNKNOWN, never "unpaid".
- Each euro is allocated once: a transfer that cites several invoices only pays them if it
  adds up to their total; otherwise those invoices are AMBIGUOUS.
- Refunds (negative movements with the reference) subtract.
- Only movements up to the analysis date count.
"""

import re
from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from centra.data.model import BankMovement, Invoice


class PaymentStatus(StrEnum):
    PAID = "cobrada"
    PARTIAL = "pago incompleto"
    OVERPAID = "pago de más"
    AMBIGUOUS = "pago ambiguo"
    PENDING = "pendiente"
    UNKNOWN = "sin datos del banco"


OPEN_STATUSES = frozenset({PaymentStatus.PENDING, PaymentStatus.PARTIAL, PaymentStatus.AMBIGUOUS})


class InvoiceStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice: Invoice
    status: PaymentStatus
    paid: Decimal
    paid_on: date | None
    movements: tuple[BankMovement, ...]

    @property
    def outstanding(self) -> Decimal:
        if self.status not in OPEN_STATUSES:
            return Decimal(0)
        return max(self.invoice.amount - self.paid, Decimal(0))

    def days_overdue(self, on: date) -> int:
        if self.status not in OPEN_STATUSES or on <= self.invoice.due:
            return 0
        return (on - self.invoice.due).days

    def days_to_pay(self) -> int | None:
        if self.status is not PaymentStatus.PAID or self.paid_on is None:
            return None
        return (self.paid_on - self.invoice.issued).days


def reconcile(
    invoices: tuple[Invoice, ...], bank: tuple[BankMovement, ...], *, as_of: date | None = None
) -> tuple[InvoiceStatus, ...]:
    if not bank:
        return tuple(
            InvoiceStatus(
                invoice=i, status=PaymentStatus.UNKNOWN, paid=Decimal(0), paid_on=None, movements=()
            )
            for i in invoices
        )
    patterns = {i.id: re.compile(rf"(?<![\w-]){re.escape(i.id)}(?![\w-])") for i in invoices}
    by_id = {i.id: i for i in invoices}
    allocated: dict[str, Decimal] = {i.id: Decimal(0) for i in invoices}
    used: dict[str, list[BankMovement]] = {i.id: [] for i in invoices}
    ambiguous: set[str] = set()
    for movement in bank:
        if as_of is not None and movement.on > as_of:
            continue
        cited = [i for i, pattern in patterns.items() if pattern.search(movement.concept)]
        if not cited:
            continue
        sign = Decimal(1) if movement.amount > 0 else Decimal(-1)
        if len(cited) == 1:
            allocated[cited[0]] += movement.amount
        elif abs(movement.amount) == sum(by_id[i].amount for i in cited):
            for invoice_id in cited:
                allocated[invoice_id] += sign * by_id[invoice_id].amount
        else:
            ambiguous.update(cited)
            continue
        for invoice_id in cited:
            used[invoice_id].append(movement)
    return tuple(
        _status(i, allocated[i.id], tuple(used[i.id]), i.id in ambiguous) for i in invoices
    )


def _status(
    invoice: Invoice, paid: Decimal, movements: tuple[BankMovement, ...], ambiguous: bool
) -> InvoiceStatus:
    if paid == invoice.amount:
        status = PaymentStatus.PAID
    elif ambiguous:
        status = PaymentStatus.AMBIGUOUS
    elif paid <= 0:
        status = PaymentStatus.PENDING
    elif paid < invoice.amount:
        status = PaymentStatus.PARTIAL
    else:
        status = PaymentStatus.OVERPAID
    incoming = [m.on for m in movements if m.amount > 0]
    paid_on = max(incoming) if incoming and status is PaymentStatus.PAID else None
    return InvoiceStatus(
        invoice=invoice,
        status=status,
        paid=max(paid, Decimal(0)),
        paid_on=paid_on,
        movements=movements,
    )
