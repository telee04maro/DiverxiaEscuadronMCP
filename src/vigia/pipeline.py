"""The whole Vigía loop: specialists → coordinator → plan → act → re-measure."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from vigia.actions.collections import Claim, SentClaim, prepare_claim, send_claim
from vigia.actions.mailer import Mailer
from vigia.audit import AuditLog, EventKind
from vigia.config import Settings
from vigia.coordinator.causes import NAME as COORDINATOR
from vigia.coordinator.causes import CrossAnalysis, cross_findings
from vigia.coordinator.plan import Autonomy, Kind, Plan, PlanItem, build_plan
from vigia.data.model import BankMovement, CompanyData
from vigia.domain.findings import Finding, SpecialistReport
from vigia.domain.vocabulary import vocabulary_for
from vigia.finance.reconciliation import reconcile
from vigia.llm.base import LanguageModel
from vigia.remeasure import Remeasurement, remeasure
from vigia.specialists.base import Specialist
from vigia.specialists.competition import CompetitionSpecialist
from vigia.specialists.customers import CustomersSpecialist
from vigia.specialists.finance import NAME as FINANCE_NAME
from vigia.specialists.finance import FinanceSpecialist, overdue_by_client

ONE_CENT = Decimal("0.01")


def default_specialists() -> tuple[Specialist, ...]:
    return (FinanceSpecialist(), CompetitionSpecialist(), CustomersSpecialist())


class Analysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    data: CompanyData
    reports: tuple[SpecialistReport, ...]
    crossing: CrossAnalysis
    plan: Plan

    @property
    def findings(self) -> tuple[Finding, ...]:
        return tuple(f for r in self.reports for f in r.findings)

    def finding(self, finding_id: str) -> Finding | None:
        return next((f for f in self.findings if f.id == finding_id), None)


def analyze(
    data: CompanyData,
    model: LanguageModel,
    log: AuditLog,
    specialists: tuple[Specialist, ...] | None = None,
) -> Analysis:
    team = specialists if specialists is not None else default_specialists()
    reports = tuple(s.analyze(data, model, log) for s in team)
    findings = tuple(f for r in reports for f in r.findings)
    kinds = {i.client_name: i.client_type.value for i in data.invoices}
    crossing = cross_findings(findings, model, log, vocabulary_for(data.company), kinds)
    plan = build_plan(data, findings, crossing)
    log.record(
        COORDINATOR,
        EventKind.DECIDED,
        f"Plan con {len(plan.items)} acciones a 7, 30 y 90 días a partir de "
        f"{len(crossing.causes)} causa(s)",
    )
    return Analysis(data=data, reports=reports, crossing=crossing, plan=plan)


@dataclass
class Execution:
    """What has been done so far; ``claimed`` feeds the re-measurement.

    ``ledger`` remembers every claim sent (client, invoices, tone) so a new analysis of the
    same situation never sends it twice.
    """

    sent: list[SentClaim] = field(default_factory=list)
    pending: dict[str, Claim] = field(default_factory=dict)
    claimed: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ledger: set[tuple[str, tuple[str, ...], str]] = field(default_factory=set)


def _ledger_key(claim: Claim) -> tuple[str, tuple[str, ...], str]:
    return (claim.client_id, tuple(sorted(claim.invoice_ids)), claim.tone.value)


def _claim_for(
    analysis: Analysis, item: PlanItem, model: LanguageModel, log: AuditLog, settings: Settings
) -> Claim | None:
    today = analysis.data.company.analysis_date
    statuses = reconcile(analysis.data.invoices, analysis.data.bank, as_of=today)
    items = overdue_by_client(statuses, today).get(item.client_id or "")
    if not items:
        return None
    if not items[0].invoice.contact_email:
        log.record(
            FINANCE_NAME,
            EventKind.REJECTED,
            f"Sin correo de cobro de {items[0].invoice.client_name}: no se reclama",
            *(i.invoice.id for i in items),
        )
        return None
    return prepare_claim(
        analysis.data.company,
        items,
        model,
        log,
        today=today,
        interest_rate_pct=settings.late_interest_rate_pct,
    )


def execute_plan(
    analysis: Analysis,
    model: LanguageModel,
    mailer: Mailer,
    log: AuditLog,
    settings: Settings,
    *,
    execution: Execution | None = None,
) -> Execution:
    """Do what the agents may do alone; prepare (but do not send) what needs approval."""
    state = execution or Execution()
    for item in analysis.plan.items:
        if item.kind is not Kind.COLLECT or item.id in state.claimed or item.id in state.pending:
            continue
        claim = _claim_for(analysis, item, model, log, settings)
        if claim is None:
            continue
        if _ledger_key(claim) in state.ledger:
            state.claimed[item.id] = claim.invoice_ids
            log.record(
                COORDINATOR,
                EventKind.CHECKED,
                f"La reclamación a {claim.client_name} ya se envió: no se repite",
                item.id,
            )
        elif item.autonomy is Autonomy.AUTO and not claim.needs_approval:
            state.sent.append(send_claim(claim, analysis.data.company, mailer, log))
            state.ledger.add(_ledger_key(claim))
            state.claimed[item.id] = claim.invoice_ids
        else:
            state.pending[item.id] = claim
            log.record(
                COORDINATOR,
                EventKind.ESCALATED,
                f"Reclamación {claim.tone.value} a {claim.client_name}: espera aprobación",
                item.id,
            )
    return state


def approve(
    analysis: Analysis,
    item_id: str,
    execution: Execution,
    mailer: Mailer,
    log: AuditLog,
    *,
    approver: str = "Gerencia",
) -> SentClaim | None:
    claim = execution.pending.pop(item_id, None)
    if claim is None or item_id in execution.claimed or _ledger_key(claim) in execution.ledger:
        return None
    log.record(
        approver, EventKind.DECIDED, f"Aprueba la reclamación a {claim.client_name}", item_id
    )
    sent = send_claim(claim, analysis.data.company, mailer, log)
    execution.sent.append(sent)
    execution.ledger.add(_ledger_key(claim))
    execution.claimed[item_id] = claim.invoice_ids
    return sent


def mark_done(item_id: str, execution: Execution, log: AuditLog, *, who: str = "Gerencia") -> None:
    """A person confirms a non-automatic action was carried out."""
    if item_id not in execution.claimed:
        execution.claimed[item_id] = ()
        log.record(who, EventKind.DID, "Confirma que la acción se ha hecho", item_id)


def measure_after(
    analysis: Analysis,
    after_data: CompanyData,
    execution: Execution,
    model: LanguageModel,
    log: AuditLog,
) -> tuple[tuple[SpecialistReport, ...], Remeasurement]:
    after_reports = tuple(s.analyze(after_data, model, log) for s in default_specialists())
    result = remeasure(
        analysis.plan,
        before=analysis.reports,
        after=after_reports,
        after_data=after_data,
        claimed=dict(execution.claimed),
        log=log,
    )
    return after_reports, result


def inject_short_payment(data: CompanyData, invoice_id: str) -> CompanyData:
    """Demo fault: the payment for ``invoice_id`` arrives one cent short."""
    shifted = False
    bank: list[BankMovement] = []
    for movement in data.bank:
        amount, balance = movement.amount, movement.balance
        if not shifted and amount > 0 and invoice_id in movement.concept:
            amount -= ONE_CENT
            shifted = True
        if shifted:
            balance -= ONE_CENT
        bank.append(movement.model_copy(update={"amount": amount, "balance": balance}))
    if not shifted:
        raise ValueError(f"No hay ningún cobro con la referencia {invoice_id}")
    return data.model_copy(update={"bank": tuple(bank)})


def first_paid_reference(data: CompanyData, client_id: str, since: date) -> str | None:
    """Invoice of ``client_id`` paid on or after ``since`` (used to pick the demo fault)."""
    for status in reconcile(data.invoices, data.bank):
        if status.invoice.client_id == client_id and status.paid_on and status.paid_on >= since:
            return status.invoice.id
    return None
