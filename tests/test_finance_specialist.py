from decimal import Decimal

from centra.audit import AuditLog
from centra.data.model import CompanyData
from centra.domain.findings import Signal
from centra.finance.offers import check_first_visit_offer
from centra.llm.base import OfflineModel
from centra.specialists.finance import FinanceSpecialist


def _report(data: CompanyData):  # type: ignore[no-untyped-def]
    return FinanceSpecialist().analyze(data, OfflineModel(), AuditLog())


def test_detects_slow_insurer_tight_cash_and_private_drop(before: CompanyData) -> None:
    report = _report(before)
    signals = {s for f in report.findings for s in f.signals}
    assert Signal.SLOW_PAYER in signals
    assert Signal.TIGHT_CASH in signals
    assert {Signal.PRIVATE_PATIENTS_DROP, Signal.NOT_SEASONAL} <= signals
    assert Signal.RECENT_OVERDUE in signals  # Gamma: only a few days late


def test_every_finding_has_evidence(before: CompanyData) -> None:
    for finding in _report(before).findings:
        assert finding.evidence


def test_cash_kpi_matches_bank_balance(before: CompanyData) -> None:
    report = _report(before)
    cash = report.kpi("caja")
    assert cash is not None
    assert cash.value == before.bank[-1].balance


def test_without_bank_cash_is_not_available_not_zero(before: CompanyData) -> None:
    data = before.model_copy(update={"bank": (), "missing_sources": ("banco.csv",)})
    report = _report(data)
    cash = report.kpi("caja")
    assert cash is not None
    assert cash.value is None
    assert any(gap.missing == "banco.csv" for gap in report.gaps)
    assert not any(Signal.TIGHT_CASH in f.signals for f in report.findings)


def test_offer_validation(before: CompanyData) -> None:
    company = before.company
    assert not check_first_visit_offer(company, Decimal("20.00")).viable
    assert check_first_visit_offer(company, Decimal("30.00")).viable


def test_offer_cannot_be_validated_without_sessions_per_patient(before: CompanyData) -> None:
    company = before.company.model_copy(update={"avg_sessions_per_new_patient": None})
    check = check_first_visit_offer(company, Decimal("30.00"))
    assert not check.viable
    assert "Falta" in check.reason
