from datetime import date
from decimal import Decimal

from vigia.data.model import BankMovement, ClientType, CompanyData, Invoice
from vigia.finance.reconciliation import PaymentStatus, reconcile

INVOICE = Invoice(
    id="F-2026-07-ASG-BETA",
    client_id="ASG-BETA",
    client_name="Mutua Beta (ficticia)",
    client_type=ClientType.INSURER,
    contact_email="pagos@mutuabeta.example",
    issued=date(2026, 7, 31),
    due=date(2026, 8, 30),
    amount=Decimal("3007.80"),
)


def _movement(concept: str, amount: str) -> BankMovement:
    return BankMovement(
        on=date(2026, 11, 20), concept=concept, amount=Decimal(amount), balance=Decimal(0)
    )


def test_exact_payment_with_reference_closes_the_invoice() -> None:
    [status] = reconcile((INVOICE,), (_movement("TRANSF REF F-2026-07-ASG-BETA", "3007.80"),))
    assert status.status is PaymentStatus.PAID
    assert status.days_overdue(date(2026, 12, 2)) == 0


def test_one_cent_short_is_not_paid() -> None:
    [status] = reconcile((INVOICE,), (_movement("TRANSF REF F-2026-07-ASG-BETA", "3007.79"),))
    assert status.status is PaymentStatus.PARTIAL
    assert status.outstanding == Decimal("0.01")
    assert status.days_overdue(date(2026, 12, 2)) > 0


def test_payment_without_reference_is_not_assumed() -> None:
    [status] = reconcile((INVOICE,), (_movement("TRANSFERENCIA MUTUA BETA", "3007.80"),))
    assert status.status is PaymentStatus.PENDING


def test_reference_must_match_whole_id() -> None:
    [status] = reconcile((INVOICE,), (_movement("REF F-2026-07-ASG-BETA-2", "3007.80"),))
    assert status.status is PaymentStatus.PENDING


def test_overpayment_is_flagged() -> None:
    [status] = reconcile((INVOICE,), (_movement("REF F-2026-07-ASG-BETA", "3007.81"),))
    assert status.status is PaymentStatus.OVERPAID


def test_demo_before_has_beta_and_gamma_overdue(before: CompanyData) -> None:
    statuses = reconcile(before.invoices, before.bank)
    overdue = {s.invoice.id for s in statuses if s.days_overdue(before.company.analysis_date) > 0}
    assert overdue == {
        "F-2026-07-ASG-BETA",
        "F-2026-08-ASG-BETA",
        "F-2026-09-ASG-BETA",
        "F-2026-09-ASG-GAMMA",
    }
