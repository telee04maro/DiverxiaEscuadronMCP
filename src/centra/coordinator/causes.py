"""Find the real cause by crossing findings from different specialists.

Claude proposes causes; the coordinator only accepts a cause whose cited findings exist,
and labels it "cross" only when the evidence really comes from more than one area.
Without the model, explicit crossing rules produce the same kind of answer.
"""

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from centra.audit import AuditLog, EventKind
from centra.domain.findings import AREA_LABELS, Area, Confidence, Finding, Signal
from centra.llm.base import LanguageModel, Tier

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
    findings: tuple[Finding, ...], model: LanguageModel, log: AuditLog
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
    return _rule_crossing(findings, log)


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


def _areas(findings: Iterable[Finding]) -> tuple[Area, ...]:
    return tuple(dict.fromkeys(f.area for f in findings))


def _with(findings: tuple[Finding, ...], *signals: Signal) -> list[Finding]:
    return [f for f in findings if f.signals & set(signals)]


def _rule_crossing(findings: tuple[Finding, ...], log: AuditLog) -> CrossAnalysis:
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
        add(
            "Se pierden pacientes particulares por precio y por la espera",
            "Las sesiones de particulares caen mientras la competencia lanza una oferta más "
            "barata y nuestras reseñas se quejan de la espera"
            + (", justo lo que la competencia promete resolver" if attacks_weakness else "")
            + ". No es un problema de un área: precio y servicio se suman.",
            _with(
                findings,
                Signal.PRIVATE_PATIENTS_DROP,
                Signal.COMPETITOR_OFFER,
                Signal.HIGHER_PRICE,
                Signal.WAIT_COMPLAINTS,
            ),
            Confidence.HIGH,
        )
    elif Signal.PRIVATE_PATIENTS_DROP in present and price_pressure:
        add(
            "Se pierden pacientes particulares por precio",
            "La caída coincide con una oferta más barata de la competencia.",
            _with(
                findings, Signal.PRIVATE_PATIENTS_DROP, Signal.COMPETITOR_OFFER, Signal.HIGHER_PRICE
            ),
            Confidence.MEDIUM,
        )
    elif Signal.PRIVATE_PATIENTS_DROP in present and Signal.WAIT_COMPLAINTS in present:
        add(
            "Se pierden pacientes particulares por la espera",
            "La caída coincide con quejas por la espera en las reseñas.",
            _with(findings, Signal.PRIVATE_PATIENTS_DROP, Signal.WAIT_COMPLAINTS),
            Confidence.MEDIUM,
        )
    if {Signal.TIGHT_CASH, Signal.SLOW_INSURER_PAYMENT} <= present:
        add(
            "La caja está al límite porque una aseguradora paga tarde",
            "Lo vencido de la aseguradora lenta casi duplica la caja disponible. Con la caja así, "
            "una guerra de precios con la competencia no es sostenible: primero hay que cobrar.",
            _with(findings, Signal.TIGHT_CASH, Signal.SLOW_INSURER_PAYMENT),
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
