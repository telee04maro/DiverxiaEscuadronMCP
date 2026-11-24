"""Turn findings and causes into a 7/30/90-day plan, with who acts and how much autonomy.

The counter-offer is where agents check each other: competition proposes prices,
finance validates them, and only a viable one reaches the plan.
"""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from vigia.coordinator.causes import CrossAnalysis
from vigia.data.model import CompanyData
from vigia.domain.findings import Finding, Signal
from vigia.domain.money import fmt_eur
from vigia.domain.priority import Horizon, horizon_for, score
from vigia.domain.vocabulary import Vocabulary, vocabulary_for
from vigia.finance.offers import OfferCheck, check_first_visit_offer
from vigia.specialists.competition import NAME as COMPETITION
from vigia.specialists.customers import NAME as CUSTOMERS
from vigia.specialists.finance import NAME as FINANCE

OFFER_STEPS = (Decimal(0), Decimal(5), Decimal(10))
MANAGER = "Gerencia"


class Autonomy(StrEnum):
    AUTO = "Actúa solo"
    APPROVAL = "Propone y una persona aprueba"
    PERSON = "Lo hace una persona, con fecha"
    EXPERT = "Deriva a un experto"


class Kind(StrEnum):
    COLLECT = "reclamar_cobro"
    COUNTER_OFFER = "contraoferta"
    REPLY_REVIEWS = "responder_resenas"
    AGENDA = "reorganizar_agenda"
    CASH_FORECAST = "prevision_caja"
    LOCAL_SEARCH = "visibilidad_busqueda"
    WHATSAPP_ASSISTANT = "asistente_whatsapp"
    ASSIGN_LEADS = "asignar_oportunidades"


class Direction(StrEnum):
    UP = "sube"
    DOWN = "baja"


class PlanItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: Kind
    title: str
    why: str
    horizon: Horizon
    owner: str
    autonomy: Autonomy
    finding_ids: tuple[str, ...]
    cause_id: str | None
    target_kpi: str
    expected: Direction
    score: Decimal
    detail: str = ""
    client_id: str | None = None


class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: tuple[PlanItem, ...]
    offer_checks: tuple[OfferCheck, ...] = ()

    def by_horizon(self, horizon: Horizon) -> tuple[PlanItem, ...]:
        return tuple(i for i in self.items if i.horizon is horizon)


def build_plan(data: CompanyData, findings: tuple[Finding, ...], crossing: CrossAnalysis) -> Plan:
    items: list[PlanItem] = []
    items.extend(_collection_items(findings, crossing))
    offer_item, checks = _counter_offer(data, findings, crossing)
    if offer_item is not None:
        items.append(offer_item)
    items.extend(_service_items(findings, crossing, vocabulary_for(data.company)))
    items.extend(_cash_and_search_items(findings, crossing))
    items.extend(_customer_items(findings, crossing))
    ordered = sorted(items, key=lambda i: (i.horizon, -i.score))
    return Plan(items=tuple(ordered), offer_checks=checks)


def _cause_for(finding_ids: tuple[str, ...], crossing: CrossAnalysis) -> str | None:
    return next((c.id for c in crossing.causes if set(finding_ids) & set(c.finding_ids)), None)


def _top_score(findings: list[Finding]) -> Decimal:
    return max((score(f) for f in findings), default=Decimal(0))


def _collection_items(findings: tuple[Finding, ...], crossing: CrossAnalysis) -> list[PlanItem]:
    items = []
    for finding in findings:
        slow = Signal.SLOW_PAYER in finding.signals
        if not slow and Signal.RECENT_OVERDUE not in finding.signals:
            continue
        client_id = finding.id.removeprefix("FIN-COBRO-")
        items.append(
            PlanItem(
                id=f"PLAN-COBRO-{client_id}",
                kind=Kind.COLLECT,
                title=(
                    "Reclamación formal de lo vencido" if slow else "Recordatorio amable de pago"
                )
                + f": {finding.subject or client_id}",
                why=finding.title,
                horizon=Horizon.WEEK,
                owner=FINANCE,
                autonomy=Autonomy.APPROVAL if slow else Autonomy.AUTO,
                finding_ids=(finding.id,),
                cause_id=_cause_for((finding.id,), crossing),
                target_kpi="vencido",
                expected=Direction.DOWN,
                score=score(finding),
                client_id=client_id,
            )
        )
    return items


def _counter_offer(
    data: CompanyData, findings: tuple[Finding, ...], crossing: CrossAnalysis
) -> tuple[PlanItem | None, tuple[OfferCheck, ...]]:
    competitor = min(
        (c.first_visit_price for c in data.competitors if c.first_visit_price is not None),
        default=None,
    )
    offers = [f for f in findings if Signal.COMPETITOR_OFFER in f.signals]
    if competitor is None or not offers:
        return None, ()
    checks = tuple(check_first_visit_offer(data.company, competitor + step) for step in OFFER_STEPS)
    viable = next((c for c in checks if c.viable), None)
    waits = [f for f in findings if Signal.WAIT_COMPLAINTS in f.signals]
    support = offers + waits
    ids = tuple(f.id for f in support)
    promise = " y cita garantizada en 48 horas" if waits else ""
    if viable is not None:
        words = vocabulary_for(data.company)
        title = (
            f"Contraoferta: {words.first_offer} a {fmt_eur(viable.price)}"
            f"{words.offer_audience}{promise}"
        )
        detail = (
            f"{COMPETITION} propone igualar la oferta; {FINANCE} lo comprueba precio a precio. "
            f"Se elige el más bajo que compensa: {viable.reason}."
        )
    else:
        title = f"No entrar en guerra de precios: competir con servicio{promise}"
        detail = f"{FINANCE} no valida ninguna rebaja: " + "; ".join(c.reason for c in checks)
    tight = any(Signal.TIGHT_CASH in f.signals for f in findings)
    if tight:
        detail += " Con la caja al límite, no conviene una rebaja más agresiva."
    item = PlanItem(
        id="PLAN-CONTRAOFERTA",
        kind=Kind.COUNTER_OFFER,
        title=title,
        why=offers[0].title,
        horizon=Horizon.MONTH,
        owner=f"{COMPETITION} + {FINANCE}",
        autonomy=Autonomy.APPROVAL,
        finding_ids=ids,
        cause_id=_cause_for(ids, crossing),
        target_kpi="variacion_particulares",
        expected=Direction.UP,
        score=_top_score(support),
        detail=detail,
    )
    return item, checks


def _service_items(
    findings: tuple[Finding, ...], crossing: CrossAnalysis, words: Vocabulary
) -> list[PlanItem]:
    waits = [f for f in findings if Signal.WAIT_COMPLAINTS in f.signals]
    if not waits:
        return []
    ids = tuple(f.id for f in waits)
    return [
        PlanItem(
            id="PLAN-RESENAS",
            kind=Kind.REPLY_REVIEWS,
            title="Responder las reseñas sobre esperas y contar qué cambia",
            why=waits[0].title,
            horizon=Horizon.WEEK,
            owner=f"{MANAGER} (agente de marketing: hoja de ruta)",
            autonomy=Autonomy.PERSON,
            finding_ids=ids,
            cause_id=_cause_for(ids, crossing),
            target_kpi="nota_reciente",
            expected=Direction.UP,
            score=_top_score(waits),
        ),
        PlanItem(
            id="PLAN-AGENDA",
            kind=Kind.AGENDA,
            title=f"Reservar huecos diarios para {words.new_customer_slots} (cita en 48 horas)",
            why=waits[0].title,
            horizon=horizon_for(urgency=waits[0].urgency, effort=waits[0].effort),
            owner=f"{MANAGER} (agente de organización: hoja de ruta)",
            autonomy=Autonomy.PERSON,
            finding_ids=ids,
            cause_id=_cause_for(ids, crossing),
            target_kpi="resenas_espera",
            expected=Direction.DOWN,
            score=_top_score(waits),
        ),
    ]


def _cash_and_search_items(
    findings: tuple[Finding, ...], crossing: CrossAnalysis
) -> list[PlanItem]:
    items = []
    cash = [f for f in findings if Signal.TIGHT_CASH in f.signals]
    if cash:
        items.append(
            PlanItem(
                id="PLAN-CAJA",
                kind=Kind.CASH_FORECAST,
                title="Previsión de caja semanal con el asesor y aplazar gastos no críticos",
                why=cash[0].title,
                horizon=Horizon.WEEK,
                owner="Asesor financiero (supervisión humana)",
                autonomy=Autonomy.EXPERT,
                finding_ids=(cash[0].id,),
                cause_id=_cause_for((cash[0].id,), crossing),
                target_kpi="dias_de_caja",
                expected=Direction.UP,
                score=score(cash[0]),
            )
        )
    search = [f for f in findings if Signal.LOW_SEARCH_VISIBILITY in f.signals]
    if search:
        ids = tuple(f.id for f in search)
        items.append(
            PlanItem(
                id="PLAN-BUSQUEDA",
                kind=Kind.LOCAL_SEARCH,
                title="Campaña local en Google para quien busca cita rápida",
                why=search[0].title,
                horizon=Horizon.QUARTER,
                owner=COMPETITION,
                autonomy=Autonomy.APPROVAL,
                finding_ids=ids,
                cause_id=_cause_for(ids, crossing),
                target_kpi="posicion_busqueda_1",
                expected=Direction.DOWN,
                score=_top_score(search),
            )
        )
    return items


def _customer_items(findings: tuple[Finding, ...], crossing: CrossAnalysis) -> list[PlanItem]:
    items = []
    slow = [f for f in findings if Signal.SLOW_RESPONSE in f.signals]
    if slow:
        items.append(
            PlanItem(
                id="PLAN-WHATSAPP",
                kind=Kind.WHATSAPP_ASSISTANT,
                title="Activar el asistente de WhatsApp fuera de horario (responde, cualifica y "
                "registra en el ERP)",
                why=slow[0].title,
                horizon=horizon_for(urgency=slow[0].urgency, effort=slow[0].effort),
                owner=CUSTOMERS,
                autonomy=Autonomy.APPROVAL,
                finding_ids=(slow[0].id,),
                cause_id=_cause_for((slow[0].id,), crossing),
                target_kpi="respuesta_fuera_horario_h",
                expected=Direction.DOWN,
                score=score(slow[0]),
                detail="Responde al momento y registra la oportunidad sin duplicados; no da "
                "asesoramiento cerrado y avisa a una persona si es urgente.",
            )
        )
    unassigned = [f for f in findings if Signal.UNASSIGNED_LEADS in f.signals]
    if unassigned:
        items.append(
            PlanItem(
                id="PLAN-ASIGNAR",
                kind=Kind.ASSIGN_LEADS,
                title="Asignar cada mañana las oportunidades pendientes",
                why=unassigned[0].title,
                horizon=Horizon.WEEK,
                owner=f"{MANAGER} (recepción)",
                autonomy=Autonomy.PERSON,
                finding_ids=(unassigned[0].id,),
                cause_id=_cause_for((unassigned[0].id,), crossing),
                target_kpi="sin_asignar_48h",
                expected=Direction.DOWN,
                score=score(unassigned[0]),
            )
        )
    return items
