"""Match invoices with bank income by reference. Paid means paid to the cent."""

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
    PENDING = "pendiente"


class InvoiceStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice: Invoice
    status: PaymentStatus
    paid: Decimal
    paid_on: date | None
    movements: tuple[BankMovement, ...]

    @property
    def outstanding(self) -> Decimal:
        return max(self.invoice.amount - self.paid, Decimal(0))

    def days_overdue(self, on: date) -> int:
        if self.status is PaymentStatus.PAID or on <= self.invoice.due:
            return 0
        return (on - self.invoice.due).days

    def days_to_pay(self) -> int | None:
        if self.status is not PaymentStatus.PAID or self.paid_on is None:
            return None
        return (self.paid_on - self.invoice.issued).days


def reconcile(
    invoices: tuple[Invoice, ...], bank: tuple[BankMovement, ...]
) -> tuple[InvoiceStatus, ...]:
    return tuple(_status(invoice, bank) for invoice in invoices)


def _status(invoice: Invoice, bank: tuple[BankMovement, ...]) -> InvoiceStatus:
    reference = re.compile(rf"(?<![\w-]){re.escape(invoice.id)}(?![\w-])")
    movements = tuple(m for m in bank if m.amount > 0 and reference.search(m.concept))
    paid = sum((m.amount for m in movements), Decimal(0))
    if paid == 0:
        status = PaymentStatus.PENDING
    elif paid == invoice.amount:
        status = PaymentStatus.PAID
    elif paid < invoice.amount:
        status = PaymentStatus.PARTIAL
    else:
        status = PaymentStatus.OVERPAID
    paid_on = max((m.on for m in movements), default=None)
    return InvoiceStatus(
        invoice=invoice, status=status, paid=paid, paid_on=paid_on, movements=movements
    )
