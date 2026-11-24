"""Find the real cause by crossing findings from different specialists.

Claude proposes causes; the coordinator only accepts a cause whose cited findings exist,
and labels it "cross" only when the evidence really comes from more than one area.
Without the model, explicit crossing rules produce the same kind of answer.
"""

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from vigia.audit import AuditLog, EventKind
from vigia.domain.findings import AREA_LABELS, Area, Confidence, Finding, Signal
from vigia.domain.money import fmt_eur, money_mentions
from vigia.domain.vocabulary import GENERAL, Vocabulary
from vigia.llm.base import LanguageModel, Tier

NAME = "Agente coordinador"
MAX_CAUSES = 3


class Origin(StrEnum):
    AI = "IA (verificada)"
    RULES = "reglas"


class RootCause(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    explanation: str
    finding_ids: tuple[str, ...]
    areas: tuple[Area, ...]
    confidence: Confidence
    origin: Origin

    @property
    def is_cross(self) -> bool:
        return len(set(self.areas)) > 1


class DiscardedHypothesis(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis: str
    reason: str
    finding_ids: tuple[str, ...]


class CrossAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    causes: tuple[RootCause, ...]
    discarded: tuple[DiscardedHypothesis, ...]
    origin: Origin
    rejected: tuple[str, ...] = ()


class LlmCause(BaseModel):
    title: str = Field(description="La causa en una frase, en español llano")
    explanation: str = Field(description="Cómo encajan los hallazgos citados, 2-4 frases")
    finding_ids: list[str] = Field(description="IDs exactos de los hallazgos que la sostienen")
    confidence: Confidence


class LlmDiscarded(BaseModel):
    hypothesis: str
    reason: str
    finding_ids: list[str]


class LlmCrossing(BaseModel):
    causes: list[LlmCause]
    discarded: list[LlmDiscarded]


_SYSTEM = (
    "Eres el agente coordinador de un equipo de agentes que asesora a una pyme. Recibes los "
    "hallazgos de varios especialistas. Tu trabajo es encontrar la causa real de los problemas "
    "cruzando hallazgos de áreas distintas, algo que ningún especialista ve por separado. "
    f"Devuelve como mucho {MAX_CAUSES} causas, cada una citando los IDs exactos de los hallazgos "
    "que la sostienen, y las hipótesis que los datos permiten descartar (por ejemplo, la "
    "estacionalidad), también con IDs. Si los hallazgos no bastan para una causa, no la inventes."
)


def cross_findings(
    findings: tuple[Finding, ...],
    model: LanguageModel,
    log: AuditLog,
    words: Vocabulary = GENERAL,
) -> CrossAnalysis:
    by_id = {f.id: f for f in findings}
    answer = model.structured(
        task="Cruzar hallazgos y buscar la causa",
        tier=Tier.MAIN,
        system=_SYSTEM,
        prompt=_prompt(findings),
        schema=LlmCrossing,
    )
    if answer is not None:
        analysis = _validated(answer, by_id, log)
        if analysis.causes:
            return analysis
        log.record(NAME, EventKind.REJECTED, "Ninguna causa de la IA tenía evidencia válida")
    return _rule_crossing(findings, log, words)


def _prompt(findings: tuple[Finding, ...]) -> str:
    blocks = []
    for f in findings:
        facts = "; ".join(e.fact for e in f.evidence)
        blocks.append(
            f"- [{f.id}] ({AREA_LABELS[f.area]}) {f.title}. {f.detail} Evidencia: {facts}"
        )
    return "Hallazgos de los especialistas:\n" + "\n".join(blocks)


def _validated(answer: LlmCrossing, by_id: dict[str, Finding], log: AuditLog) -> CrossAnalysis:
    causes: list[RootCause] = []
    rejected: list[str] = []
    for raw in answer.causes[:MAX_CAUSES]:
        unknown = [i for i in raw.finding_ids if i not in by_id]
        known = tuple(dict.fromkeys(i for i in raw.finding_ids if i in by_id))
        if unknown:
            note = f"«{raw.title}» citaba hallazgos inexistentes: {', '.join(unknown)}"
            rejected.append(note)
            log.record(NAME, EventKind.REJECTED, note)
        if not known:
            continue
        invented = _invented_amounts(f"{raw.title} {raw.explanation}", [by_id[i] for i in known])
        if invented:
            note = f"«{raw.title}» mencionaba importes que no están en sus hallazgos: {invented}"
            rejected.append(note)
            log.record(NAME, EventKind.REJECTED, note)
            continue
        causes.append(
            RootCause(
                id=f"CAUSA-{len(causes) + 1}",
                title=raw.title,
                explanation=raw.explanation,
                finding_ids=known,
                areas=_areas(by_id[i] for i in known),
                confidence=raw.confidence if not unknown else Confidence.LOW,
                origin=Origin.AI,
            )
        )
    discarded = tuple(
        DiscardedHypothesis(
            hypothesis=d.hypothesis,
            reason=d.reason,
            finding_ids=tuple(i for i in d.finding_ids if i in by_id),
        )
        for d in answer.discarded
        if any(i in by_id for i in d.finding_ids)
    )
    for cause in causes:
        log.record(NAME, EventKind.DECIDED, f"Causa: {cause.title}", *cause.finding_ids)
    return CrossAnalysis(
        causes=tuple(causes), discarded=discarded, origin=Origin.AI, rejected=tuple(rejected)
    )


def _invented_amounts(text: str, support: list[Finding]) -> str:
    """Amounts the model wrote that none of the cited findings contains (empty if none)."""
    written = money_mentions(text)
    if written is None:
        return "importe ilegible"
    known: set[Decimal] = set()
    for finding in support:
        facts = " ".join([finding.title, finding.detail, *(e.fact for e in finding.evidence)])
        known |= money_mentions(facts) or set()
        known |= {value.quantize(Decimal("0.01")) for value in finding.metrics.values()}
    return ", ".join(fmt_eur(a) for a in sorted(written - known))


def _areas(findings: Iterable[Finding]) -> tuple[Area, ...]:
    return tuple(dict.fromkeys(f.area for f in findings))


def losing_after_hours(finding: Finding) -> bool:
    """Only claim that late answers lose customers if the data shows more losses after hours."""
    late, on_time = finding.metrics.get("late_lost"), finding.metrics.get("on_time_lost")
    return late is not None and late > 0 and (on_time is None or late > on_time)


def _slow_response_clause(slow: list[Finding]) -> str:
    """Figures from the customer-service finding, never from the template."""
    if not slow or not losing_after_hours(slow[0]):
        return ""
    metrics = slow[0].metrics
    hours, lost = metrics.get("late_hours"), metrics.get("late_lost")
    if hours is None or lost is None:
        return ""
    shown = str(hours).replace(".", ",")
    return (
        f"; además, las consultas que llegan fuera de horario tardan {shown} h en contestarse "
        f"y se pierde el {lost} % de ellas"
    )


def _cash_cause_text(findings: tuple[Finding, ...]) -> tuple[str, str]:
    """Every figure in the sentence comes from the findings' metrics, never from a template."""
    slow = max(_with(findings, Signal.SLOW_PAYER), key=lambda f: f.metrics.get("owed", Decimal(0)))
    cash = _with(findings, Signal.TIGHT_CASH)[0]
    who = slow.subject or "un cliente"
    owed, balance = slow.metrics.get("owed"), cash.metrics.get("balance")
    comparison = ""
    if owed is not None and balance is not None and balance > 0:
        share = (owed / balance * 100).quantize(Decimal("1"))
        comparison = (
            f"Lo que debe {who} ({fmt_eur(owed)}) equivale al {share} % de la caja disponible "
            f"({fmt_eur(balance)}). "
        )
    return (
        f"La caja está al límite porque {who} paga tarde",
        comparison + "Con la caja así, una guerra de precios no es sostenible: primero hay que "
        "cobrar.",
    )


def _with(findings: tuple[Finding, ...], *signals: Signal) -> list[Finding]:
    return [f for f in findings if f.signals & set(signals)]


def _rule_crossing(
    findings: tuple[Finding, ...], log: AuditLog, words: Vocabulary
) -> CrossAnalysis:
    present = {s for f in findings for s in f.signals}
    causes: list[RootCause] = []

    def add(title: str, explanation: str, support: list[Finding], confidence: Confidence) -> None:
        ids = tuple(dict.fromkeys(f.id for f in support))
        causes.append(
            RootCause(
                id=f"CAUSA-{len(causes) + 1}",
                title=title,
                explanation=explanation,
                finding_ids=ids,
                areas=_areas(support),
                confidence=confidence,
                origin=Origin.RULES,
            )
        )

    price_pressure = present & {Signal.COMPETITOR_OFFER, Signal.HIGHER_PRICE}
    if (
        Signal.PRIVATE_PATIENTS_DROP in present
        and price_pressure
        and Signal.WAIT_COMPLAINTS in present
    ):
        attacks_weakness = Signal.COMPETITOR_PROMISES_NO_WAIT in present
        slow = [f for f in _with(findings, Signal.SLOW_RESPONSE) if losing_after_hours(f)]
        add(
            f"Se pierden {words.customers} particulares por precio y por la espera"
            + (", también al escribir fuera de horario" if slow else ""),
            f"Las {words.private_units} caen mientras la competencia lanza una oferta más "
            "barata y nuestras reseñas se quejan de la espera"
            + (", justo lo que la competencia promete resolver" if attacks_weakness else "")
            + _slow_response_clause(slow)
            + ". No es un problema de un área: precio y servicio se suman.",
            _with(
                findings,
                Signal.PRIVATE_PATIENTS_DROP,
                Signal.COMPETITOR_OFFER,
                Signal.HIGHER_PRICE,
                Signal.WAIT_COMPLAINTS,
            )
            + slow,
            Confidence.HIGH,
        )
    elif Signal.PRIVATE_PATIENTS_DROP in present and price_pressure:
        add(
            f"Se pierden {words.customers} particulares por precio",
            "La caída coincide con una oferta más barata de la competencia.",
            _with(
                findings, Signal.PRIVATE_PATIENTS_DROP, Signal.COMPETITOR_OFFER, Signal.HIGHER_PRICE
            ),
            Confidence.MEDIUM,
        )
    elif Signal.PRIVATE_PATIENTS_DROP in present and Signal.WAIT_COMPLAINTS in present:
        add(
            f"Se pierden {words.customers} particulares por la espera",
            "La caída coincide con quejas por la espera en las reseñas.",
            _with(findings, Signal.PRIVATE_PATIENTS_DROP, Signal.WAIT_COMPLAINTS),
            Confidence.MEDIUM,
        )
    if {Signal.TIGHT_CASH, Signal.SLOW_PAYER} <= present:
        title, explanation = _cash_cause_text(findings)
        add(
            title,
            explanation,
            _with(findings, Signal.TIGHT_CASH, Signal.SLOW_PAYER),
            Confidence.HIGH,
        )
    discarded = []
    if Signal.NOT_SEASONAL in present:
        support = _with(findings, Signal.NOT_SEASONAL)
        discarded.append(
            DiscardedHypothesis(
                hypothesis="Es la temporada: en otoño siempre baja",
                reason="Los mismos meses del año pasado no bajaron.",
                finding_ids=tuple(f.id for f in support),
            )
        )
    for cause in causes:
        log.record(NAME, EventKind.DECIDED, f"Causa (reglas): {cause.title}", *cause.finding_ids)
    return CrossAnalysis(causes=tuple(causes), discarded=tuple(discarded), origin=Origin.RULES)
