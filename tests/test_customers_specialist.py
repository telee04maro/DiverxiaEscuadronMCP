from datetime import datetime

from vigia.audit import AuditLog
from vigia.coordinator.plan import Autonomy, Kind
from vigia.data.model import CompanyData
from vigia.domain.findings import Area, Signal
from vigia.llm.base import OfflineModel
from vigia.pipeline import Execution, analyze, mark_done, measure_after
from vigia.remeasure import Effect
from vigia.specialists.customers import CustomersSpecialist, is_after_hours


def _report(data: CompanyData):  # type: ignore[no-untyped-def]
    return CustomersSpecialist().analyze(data, OfflineModel(), AuditLog())


def test_after_hours_rules(before: CompanyData) -> None:
    company = before.company
    assert is_after_hours(datetime(2026, 10, 14, 21, 0), company)  # Wednesday night
    assert is_after_hours(datetime(2026, 10, 17, 11, 0), company)  # Saturday
    assert not is_after_hours(datetime(2026, 10, 14, 12, 0), company)


def test_detects_slow_after_hours_response_and_unassigned(before: CompanyData) -> None:
    report = _report(before)
    signals = {s for f in report.findings for s in f.signals}
    assert {Signal.SLOW_RESPONSE, Signal.UNASSIGNED_LEADS} <= signals
    slow = next(f for f in report.findings if Signal.SLOW_RESPONSE in f.signals)
    assert slow.metrics["late_hours"] > 4


def test_without_opportunities_nothing_is_invented(before: CompanyData) -> None:
    data = before.model_copy(update={"opportunities": ()})
    report = _report(data)
    assert report.findings == ()
    count = report.kpi("consultas_30d")
    assert count is not None and count.value is None
    assert report.gaps[0].missing == "Oportunidades del ERP/CRM"


def test_cross_cause_now_spans_three_areas(before: CompanyData) -> None:
    analysis = analyze(before, OfflineModel(), AuditLog())
    main = analysis.crossing.causes[0]
    assert {Area.FINANCE, Area.COMPETITION, Area.CUSTOMERS} <= set(main.areas)
    assert "fuera de horario" in main.explanation
    assert "12,2 h" in main.explanation


def test_plan_proposes_whatsapp_assistant_with_approval(before: CompanyData) -> None:
    plan = analyze(before, OfflineModel(), AuditLog()).plan
    item = next(i for i in plan.items if i.kind is Kind.WHATSAPP_ASSISTANT)
    assert item.autonomy is Autonomy.APPROVAL
    assert any(i.kind is Kind.ASSIGN_LEADS for i in plan.items)


def test_assistant_effect_is_measured(before: CompanyData, after: CompanyData) -> None:
    log = AuditLog()
    analysis = analyze(before, OfflineModel(), log)
    execution = Execution()
    mark_done("PLAN-WHATSAPP", execution, log)
    _, result = measure_after(analysis, after, execution, OfflineModel(), log)
    whatsapp = next(r for r in result.results if r.item.id == "PLAN-WHATSAPP")
    assert whatsapp.effect is Effect.CONFIRMED
    assert whatsapp.before is not None and whatsapp.after is not None
    assert whatsapp.after < whatsapp.before
