"""Acceptance tests for the red-team findings (RT-01 … RT-18). Each one reproduces the defect."""

import smtplib
import ssl
from datetime import date
from decimal import Decimal
from email.message import EmailMessage
from typing import Any

import pytest
from pydantic import SecretStr

from vigia.actions.collections import EmailDraft, Origin, prepare_claim
from vigia.actions.mailer import SmtpMailer
from vigia.audit import AuditLog
from vigia.config import Settings, SmtpSettings
from vigia.coordinator.causes import LlmCause, LlmCrossing
from vigia.coordinator.causes import Origin as CauseOrigin
from vigia.coordinator.plan import Kind
from vigia.data.model import BankMovement, ClientType, CompanyData, Invoice, Review
from vigia.domain.findings import Confidence, Signal
from vigia.domain.money import eur
from vigia.finance.reconciliation import PaymentStatus, reconcile
from vigia.llm.base import LlmCall, OfflineModel, Tier
from vigia.pipeline import Execution, analyze, execute_plan, measure_after
from vigia.remeasure import Effect
from vigia.specialists.competition import CompetitionSpecialist, ReviewTag, ReviewTags, Theme
from vigia.specialists.finance import FinanceSpecialist, overdue_by_client


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> str:
        self.sent.append(message)
        return "prueba"


class ScriptedModel:
    def __init__(self, answers: dict[type, object]) -> None:
        self._answers = answers

    @property
    def mode(self) -> str:
        return "guion"

    @property
    def calls(self) -> tuple[LlmCall, ...]:
        return ()

    def structured(self, *, task, tier: Tier, system: str, prompt: str, schema):  # type: ignore[no-untyped-def]
        return self._answers.get(schema)


def _invoice(invoice_id: str, amount: str, due: date = date(2026, 10, 1)) -> Invoice:
    return Invoice(
        id=invoice_id,
        client_id="C1",
        client_name="Cliente (ficticio)",
        client_type=ClientType.COMPANY,
        contact_email="c1@cliente.example",
        issued=date(2026, 9, 1),
        due=due,
        amount=Decimal(amount),
    )


def _move(concept: str, amount: str, on: date = date(2026, 10, 15)) -> BankMovement:
    return BankMovement(on=on, concept=concept, amount=Decimal(amount), balance=Decimal(0))


# RT-01: without a bank statement nothing is "unpaid"; it is unknown.
def test_rt01_no_bank_means_unknown_not_unpaid(before: CompanyData) -> None:
    data = before.model_copy(update={"bank": (), "missing_sources": ("banco.csv",)})
    report = FinanceSpecialist().analyze(data, OfflineModel(), AuditLog())
    vencido = report.kpi("vencido")
    assert vencido is not None and vencido.value is None
    assert not any(f.id.startswith("FIN-COBRO") for f in report.findings)
    mailer = FakeMailer()
    execution = execute_plan(
        analyze(data, OfflineModel(), AuditLog()), OfflineModel(), mailer, AuditLog(), Settings()
    )
    assert not mailer.sent and not execution.pending


# RT-02: one euro is allocated once; refunds subtract.
def test_rt02_one_transfer_cannot_pay_two_invoices() -> None:
    invoices = (_invoice("F-1", "100.00"), _invoice("F-2", "100.00"))
    statuses = reconcile(invoices, (_move("PAGO F-1 F-2", "100.00"),))
    assert all(s.status is PaymentStatus.AMBIGUOUS for s in statuses)
    exact = reconcile(invoices, (_move("PAGO F-1 F-2", "200.00"),))
    assert all(s.status is PaymentStatus.PAID for s in exact)


def test_rt02_refund_reopens_the_invoice() -> None:
    statuses = reconcile(
        (_invoice("F-3", "120.00"),),
        (_move("COBRO F-3", "120.00"), _move("DEVOLUCION RECIBO F-3", "-120.00")),
    )
    assert statuses[0].status is PaymentStatus.PENDING


# RT-03: an overpaid client is not chased for 0,00 €.
def test_rt03_overpaid_is_not_overdue() -> None:
    statuses = reconcile((_invoice("F-4", "100.00"),), (_move("PAGO F-4", "150.00"),))
    assert statuses[0].status is PaymentStatus.OVERPAID
    assert overdue_by_client(statuses, date(2026, 11, 1)) == {}


# RT-04 and RT-12: a claimed invoice missing afterwards makes the result not measurable.
def test_rt04_missing_invoice_after_is_not_confirmed(
    before: CompanyData, after: CompanyData
) -> None:
    log, mailer = AuditLog(), FakeMailer()
    analysis = analyze(before, OfflineModel(), log)
    execution = execute_plan(analysis, OfflineModel(), mailer, log, Settings())
    gamma = "PLAN-COBRO-ASG-GAMMA"
    assert gamma in execution.claimed
    missing = after.model_copy(
        update={"invoices": tuple(i for i in after.invoices if i.id != "F-2026-09-ASG-GAMMA")}
    )
    _, result = measure_after(analysis, missing, execution, OfflineModel(), log)
    effect = next(r.effect for r in result.results if r.item.id == gamma)
    assert effect is Effect.NOT_MEASURABLE
    no_bank = after.model_copy(update={"bank": ()})
    _, result = measure_after(analysis, no_bank, execution, OfflineModel(), log)
    assert next(r.effect for r in result.results if r.item.id == gamma) is Effect.NOT_MEASURABLE


# RT-05: analysing again never sends the same claim twice.
def test_rt05_reanalysis_does_not_resend(before: CompanyData) -> None:
    log, mailer, execution = AuditLog(), FakeMailer(), Execution()
    for _ in range(2):
        analysis = analyze(before, OfflineModel(), log)
        execute_plan(analysis, OfflineModel(), mailer, log, Settings(), execution=execution)
    assert len(mailer.sent) == 1


# RT-06: invented amounts, threats or a formal tone never pass as a verified friendly e-mail.
@pytest.mark.parametrize(
    ("subject", "extra"),
    [
        ("Recordatorio", "Se aplicará un recargo de 300 € y gastos de 1500 euros."),
        ("Recordatorio", "Importe adicional: 1234.56 €."),
        ("Recordatorio", "Si no paga iniciaremos acciones judiciales y le incluiremos en ASNEF."),
        ("Requerimiento formal", ""),
        ("Debe 9.999,99 €", ""),
    ],
)
def test_rt06_unsafe_drafts_fall_back_to_template(
    before: CompanyData, subject: str, extra: str
) -> None:
    today = before.company.analysis_date
    statuses = reconcile(before.invoices, before.bank, as_of=today)
    items = overdue_by_client(statuses, today)["ASG-GAMMA"]
    body = f"Factura F-2026-09-ASG-GAMMA pendiente: 1.920,60 €. {extra}"
    model = ScriptedModel({EmailDraft: EmailDraft(subject=subject, body=body)})
    claim = prepare_claim(before.company, items, model, AuditLog(), today=today)
    assert claim.origin is Origin.TEMPLATE


def test_rt06_clean_friendly_draft_is_accepted(before: CompanyData) -> None:
    today = before.company.analysis_date
    statuses = reconcile(before.invoices, before.bank, as_of=today)
    items = overdue_by_client(statuses, today)["ASG-GAMMA"]
    draft = EmailDraft(
        subject="Recordatorio\nde pago",
        body="Hola: la factura F-2026-09-ASG-GAMMA de 1.920,60 € consta pendiente. ¡Gracias!",
    )
    claim = prepare_claim(
        before.company, items, ScriptedModel({EmailDraft: draft}), AuditLog(), today=today
    )
    assert claim.origin is Origin.AI
    assert "\n" not in claim.subject  # RT-15


# RT-07: the rule-based cause states only figures taken from the findings.
def test_rt07_cash_cause_figures_come_from_data(before: CompanyData) -> None:
    analysis = analyze(before, OfflineModel(), AuditLog())
    cash = next(c for c in analysis.crossing.causes if "caja" in c.title.lower())
    assert "duplica" not in cash.explanation
    assert "Mutua Beta (ficticia)" in cash.title
    assert "8.633,50 €" in cash.explanation and "7.993,85 €" in cash.explanation


def test_rt09_ai_cause_with_invented_amount_is_rejected(before: CompanyData) -> None:
    invented = LlmCrossing(
        causes=[
            LlmCause(
                title="Mutua Beta os debe 50.000 €",
                explanation="x",
                finding_ids=["FIN-COBRO-ASG-BETA", "FIN-CAJA"],
                confidence=Confidence.HIGH,
            )
        ],
        discarded=[],
    )
    analysis = analyze(before, ScriptedModel({LlmCrossing: invented}), AuditLog())
    assert analysis.crossing.origin is CauseOrigin.RULES


# RT-08: SMTP must verify the server certificate before sending the password.
def test_rt08_starttls_verifies_certificate(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    class FakeSmtp:
        def __init__(self, *args: object, **kwargs: object) -> None: ...
        def __enter__(self) -> "FakeSmtp":
            return self

        def __exit__(self, *args: object) -> None: ...
        def starttls(self, context: ssl.SSLContext | None = None) -> None:
            seen["context"] = context

        def login(self, user: str, password: str) -> None: ...
        def send_message(self, message: EmailMessage) -> None: ...

    monkeypatch.setattr(smtplib, "SMTP", FakeSmtp)
    smtp = SmtpSettings(host="h", port=587, user="u", password=SecretStr("p"), sender="s@x.example")
    message = EmailMessage()
    message["To"] = "cliente@x.example"
    SmtpMailer(smtp, "prueba@x.example").send(message)
    context = seen["context"]
    assert context is not None and context.verify_mode is ssl.CERT_REQUIRED
    assert context.check_hostname


# RT-09: a prompt injection inside reviews cannot flip the wait statistics.
def test_rt09_review_tags_far_from_rules_are_rejected(before: CompanyData) -> None:
    happy = tuple(
        Review(on=date(2026, 10, d), rating=5, text="Genial, muy buen trato.") for d in range(1, 7)
    )
    data = before.model_copy(update={"reviews": happy})
    tags = ReviewTags(reviews=[ReviewTag(index=i, themes=[Theme.WAIT]) for i in range(len(happy))])
    report = CompetitionSpecialist().analyze(data, ScriptedModel({ReviewTags: tags}), AuditLog())
    assert not any(Signal.WAIT_COMPLAINTS in f.signals for f in report.findings)


# RT-10: no "the rating drops" when it does not.
def test_rt10_title_does_not_claim_a_drop(before: CompanyData) -> None:
    flat = tuple(
        Review(on=date(2026, month, 10), rating=4, text="Tardaron semanas en darme cita.")
        for month in (6, 7, 9, 10)
    )
    report = CompetitionSpecialist().analyze(
        before.model_copy(update={"reviews": flat}), OfflineModel(), AuditLog()
    )
    review = next(f for f in report.findings if f.id == "COMP-RESENAS")
    assert "cae" not in review.title


# RT-13: balance from the last row of the last day; broken statements are flagged.
def test_rt13_last_row_balance_and_invariant(before: CompanyData) -> None:
    rows = (
        BankMovement(
            on=date(2026, 10, 30), concept="A", amount=Decimal("1000"), balance=Decimal("1000")
        ),
        BankMovement(
            on=date(2026, 10, 31), concept="B", amount=Decimal("-10"), balance=Decimal("990")
        ),
        BankMovement(
            on=date(2026, 10, 31), concept="C", amount=Decimal("-900"), balance=Decimal("90")
        ),
    )
    report = FinanceSpecialist().analyze(
        before.model_copy(update={"bank": rows}), OfflineModel(), AuditLog()
    )
    cash = report.kpi("caja")
    assert cash is not None and cash.value == Decimal("90")
    broken = (*rows[:2], rows[2].model_copy(update={"balance": Decimal("95")}))
    report = FinanceSpecialist().analyze(
        before.model_copy(update={"bank": broken}), OfflineModel(), AuditLog()
    )
    assert any(g.missing == "Extracto bancario coherente" for g in report.gaps)


# RT-14: ambiguous number formats are read as written in Spanish or English.
def test_rt14_number_formats() -> None:
    assert eur("1.234") == Decimal("1234.00")
    assert eur("1,234.56") == Decimal("1234.56")
    assert eur("1.234,56") == Decimal("1234.56")


# RT-18: payments after the analysis date do not count yet.
def test_rt18_future_payments_are_ignored() -> None:
    statuses = reconcile(
        (_invoice("F-5", "100.00"),),
        (
            _move("SALDO INICIAL", "0.00", on=date(2026, 8, 1)),  # the statement covers F-5
            _move("PAGO F-5", "100.00", on=date(2026, 12, 31)),
        ),
        as_of=date(2026, 11, 2),
    )
    assert statuses[0].status is PaymentStatus.PENDING


def test_plan_never_chases_unknown_clients(before: CompanyData) -> None:
    data = before.model_copy(update={"bank": ()})
    plan = analyze(data, OfflineModel(), AuditLog()).plan
    assert not any(i.kind is Kind.COLLECT for i in plan.items)
