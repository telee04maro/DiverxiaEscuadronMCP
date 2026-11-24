"""End to end: the whole demo journey with a fake mailer and scripted or absent AI."""

from email.message import EmailMessage

from centra.actions.collections import Tone
from centra.audit import AuditLog, EventKind
from centra.config import Settings
from centra.coordinator.causes import LlmCause, LlmCrossing, Origin
from centra.coordinator.plan import Autonomy, Kind
from centra.data.model import CompanyData
from centra.domain.findings import Area, Confidence
from centra.domain.priority import Horizon
from centra.llm.base import LlmCall, OfflineModel, Tier
from centra.pipeline import (
    analyze,
    approve,
    execute_plan,
    first_paid_reference,
    inject_short_payment,
    mark_done,
    measure_after,
)
from centra.remeasure import Effect


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> str:
        self.sent.append(message)
        return "buzón de prueba"


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


def test_rules_find_the_cross_cause_and_discard_seasonality(before: CompanyData) -> None:
    analysis = analyze(before, OfflineModel(), AuditLog())
    assert analysis.crossing.origin is Origin.RULES
    cross = [c for c in analysis.crossing.causes if c.is_cross]
    assert cross, "debe haber al menos una causa con evidencia de finanzas y de competencia"
    assert {Area.FINANCE, Area.COMPETITION} <= set(cross[0].areas)
    assert any("temporada" in d.hypothesis for d in analysis.crossing.discarded)


def test_counter_offer_is_validated_by_finance(before: CompanyData) -> None:
    plan = analyze(before, OfflineModel(), AuditLog()).plan
    offer = next(i for i in plan.items if i.kind is Kind.COUNTER_OFFER)
    assert "30,00 €" in offer.title  # 20 € and 25 € do not pay off; 30 € does
    assert offer.autonomy is Autonomy.APPROVAL
    assert [c.viable for c in plan.offer_checks] == [False, False, True]


def test_plan_has_three_horizons_and_levels_of_autonomy(before: CompanyData) -> None:
    plan = analyze(before, OfflineModel(), AuditLog()).plan
    assert {i.horizon for i in plan.items} == {Horizon.WEEK, Horizon.MONTH, Horizon.QUARTER}
    assert {i.autonomy for i in plan.items} == set(Autonomy)


def test_ai_cause_citing_missing_findings_is_rejected(before: CompanyData) -> None:
    bogus = LlmCrossing(
        causes=[
            LlmCause(
                title="Inventada",
                explanation="x",
                finding_ids=["NO-EXISTE"],
                confidence=Confidence.HIGH,
            )
        ],
        discarded=[],
    )
    log = AuditLog()
    analysis = analyze(before, ScriptedModel({LlmCrossing: bogus}), log)
    assert analysis.crossing.origin is Origin.RULES
    assert any(e.kind is EventKind.REJECTED for e in log.events)


def test_valid_ai_cause_is_accepted(before: CompanyData) -> None:
    good = LlmCrossing(
        causes=[
            LlmCause(
                title="Precio y espera",
                explanation="x",
                finding_ids=["FIN-PARTICULARES", "COMP-OFERTA-1"],
                confidence=Confidence.HIGH,
            )
        ],
        discarded=[],
    )
    analysis = analyze(before, ScriptedModel({LlmCrossing: good}), AuditLog())
    assert analysis.crossing.origin is Origin.AI
    assert analysis.crossing.causes[0].is_cross


def _run(before: CompanyData, after: CompanyData):  # type: ignore[no-untyped-def]
    log, mailer, settings = AuditLog(), FakeMailer(), Settings()
    analysis = analyze(before, OfflineModel(), log)
    execution = execute_plan(analysis, OfflineModel(), mailer, log, settings)
    return analysis, execution, mailer, log


def test_friendly_reminder_is_sent_alone_and_formal_claim_waits(
    before: CompanyData, after: CompanyData
) -> None:
    _, execution, mailer, _ = _run(before, after)
    assert len(mailer.sent) == 1
    assert execution.sent[0].claim.tone is Tone.FRIENDLY
    pending = list(execution.pending.values())
    assert [c.tone for c in pending] == [Tone.FORMAL]
    body = mailer.sent[0].get_content()
    assert "F-2026-09-ASG-GAMMA" in body
    assert "1.920,60 €" in body
    assert "asistente de IA" in body


def test_approval_sends_once(before: CompanyData, after: CompanyData) -> None:
    analysis, execution, mailer, log = _run(before, after)
    item_id = next(iter(execution.pending))
    assert approve(analysis, item_id, execution, mailer, log) is not None
    assert approve(analysis, item_id, execution, mailer, log) is None
    assert len(mailer.sent) == 2
    again = execute_plan(analysis, OfflineModel(), mailer, log, Settings(), execution=execution)
    assert len(again.sent) == 2  # nothing is sent twice


def _remeasure(before: CompanyData, after: CompanyData):  # type: ignore[no-untyped-def]
    analysis, execution, mailer, log = _run(before, after)
    for item_id in list(execution.pending):
        approve(analysis, item_id, execution, mailer, log)
    for item in analysis.plan.items:
        if item.kind is not Kind.COLLECT and item.horizon is not Horizon.QUARTER:
            mark_done(item.id, execution, log)
    return analysis, execution, log


def test_remeasure_confirms_collections_and_reorders_plan(
    before: CompanyData, after: CompanyData
) -> None:
    analysis, execution, log = _remeasure(before, after)
    _, result = measure_after(analysis, after, execution, OfflineModel(), log)
    effects = {r.item.id: r.effect for r in result.results}
    assert effects["PLAN-COBRO-ASG-GAMMA"] is Effect.CONFIRMED
    assert effects["PLAN-COBRO-ASG-BETA"] is Effect.PARTIAL  # September still unpaid
    assert effects["PLAN-CONTRAOFERTA"] is Effect.CONFIRMED
    assert effects["PLAN-BUSQUEDA"] is Effect.NOT_DONE
    insist = [i for i in result.next_plan if i.title.startswith("Insistir")]
    assert any(i.id == "PLAN-COBRO-ASG-BETA" for i in insist)
    assert all(i.horizon is Horizon.WEEK for i in insist)


def test_one_cent_short_payment_is_not_collected(before: CompanyData, after: CompanyData) -> None:
    analysis, execution, log = _remeasure(before, after)
    reference = first_paid_reference(after, "ASG-GAMMA", before.company.analysis_date)
    assert reference == "F-2026-09-ASG-GAMMA"
    faulty = inject_short_payment(after, reference)
    _, result = measure_after(analysis, faulty, execution, OfflineModel(), log)
    gamma = next(r for r in result.results if r.item.id == "PLAN-COBRO-ASG-GAMMA")
    assert gamma.effect is Effect.NONE
    assert "incompleto" in gamma.note
