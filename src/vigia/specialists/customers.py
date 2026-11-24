"""Customer service and acquisition specialist: what happens to the enquiries the company receives.

Reads the opportunities registered in the ERP/CRM (for example by the WhatsApp assistant) and
measures how fast they are answered inside and outside opening hours, how many are lost and
how many are left without anyone in charge. Rules only: no language model needed.
"""

from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from statistics import median

from vigia.audit import AuditLog, EventKind
from vigia.data.model import Company, CompanyData, Opportunity, OpportunityStatus
from vigia.domain.findings import (
    Area,
    Confidence,
    DataGap,
    Evidence,
    Finding,
    Kpi,
    Signal,
    SpecialistReport,
)
from vigia.domain.money import fmt_num
from vigia.llm.base import LanguageModel

NAME = "Agente de atención y captación"
SOURCES = ("Oportunidades del ERP/CRM (en la demo, ERP de demo con la forma de BALTER)",)

WINDOW_DAYS = 30
SLOW_RESPONSE_HOURS = Decimal(4)
UNASSIGNED_AFTER = timedelta(hours=48)
MIN_UNASSIGNED = 3
MIN_ENQUIRIES = 10
_HOUR = Decimal(3600)


def is_after_hours(moment: datetime, company: Company) -> bool:
    weekend = moment.weekday() >= 5  # noqa: PLR2004 - Saturday and Sunday
    return weekend or not company.opening_hour <= moment.hour < company.closing_hour


def _hours(opportunity: Opportunity) -> Decimal | None:
    if opportunity.first_response_at is None:
        return None
    seconds = (opportunity.first_response_at - opportunity.created_at).total_seconds()
    return (Decimal(seconds) / _HOUR).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _median(values: list[Decimal]) -> Decimal | None:
    return Decimal(median(values)).quantize(Decimal("0.1")) if values else None


class CustomersSpecialist:
    @property
    def name(self) -> str:
        return NAME

    @property
    def area(self) -> Area:
        return Area.CUSTOMERS

    @property
    def sources(self) -> tuple[str, ...]:
        return SOURCES

    def analyze(self, data: CompanyData, model: LanguageModel, log: AuditLog) -> SpecialistReport:
        today = datetime.combine(data.company.analysis_date, time(0))
        recent = [
            o for o in data.opportunities if today - timedelta(WINDOW_DAYS) <= o.created_at < today
        ]
        log.record(
            NAME, EventKind.SAW, f"{len(recent)} consultas en los últimos {WINDOW_DAYS} días"
        )
        stats = _Stats(recent, data.company, today)
        findings = [*stats.slow_response_findings(), *stats.unassigned_findings()]
        for finding in findings:
            log.record(NAME, EventKind.DECIDED, finding.title, finding.id)
        return SpecialistReport(
            specialist=NAME,
            area=Area.CUSTOMERS,
            sources=SOURCES,
            kpis=stats.kpis(available=bool(data.opportunities)),
            findings=tuple(findings),
            gaps=_gaps(data),
        )


class _Stats:
    def __init__(self, recent: list[Opportunity], company: Company, today: datetime) -> None:
        self.recent = recent
        self.today = today
        self.late = [o for o in recent if is_after_hours(o.created_at, company)]
        self.on_time = [o for o in recent if not is_after_hours(o.created_at, company)]
        self.late_hours = _median([h for o in self.late if (h := _hours(o)) is not None])
        self.on_time_hours = _median([h for o in self.on_time if (h := _hours(o)) is not None])
        self.unassigned = [
            o
            for o in recent
            if o.assigned_to is None
            and o.status is OpportunityStatus.OPEN
            and today - o.created_at > UNASSIGNED_AFTER
        ]

    def _share(self, part: list[Opportunity], whole: list[Opportunity]) -> Decimal | None:
        if not whole:
            return None
        return (Decimal(len(part)) / len(whole) * 100).quantize(Decimal("1"))

    def _lost(self, group: list[Opportunity]) -> list[Opportunity]:
        return [o for o in group if o.status is OpportunityStatus.LOST]

    def kpis(self, *, available: bool) -> tuple[Kpi, ...]:
        count = Decimal(len(self.recent)) if available else None
        return (
            Kpi(key="consultas_30d", label=f"Consultas ({WINDOW_DAYS} días)", value=count, unit=""),
            Kpi(
                key="fuera_de_horario",
                label="Consultas fuera de horario",
                value=self._share(self.late, self.recent) if available else None,
                unit="%",
            ),
            Kpi(
                key="respuesta_fuera_horario_h",
                label="Respuesta fuera de horario (mediana)",
                value=self.late_hours,
                unit="h",
            ),
            Kpi(
                key="respuesta_en_horario_h",
                label="Respuesta en horario (mediana)",
                value=self.on_time_hours,
                unit="h",
            ),
            Kpi(
                key="perdidas_fuera_horario",
                label="Perdidas, de las de fuera de horario",
                value=self._share(self._lost(self.late), self.late),
                unit="%",
            ),
            Kpi(
                key="sin_asignar_48h",
                label="Sin responsable desde hace más de 48 h",
                value=Decimal(len(self.unassigned)) if available else None,
                unit="",
            ),
        )

    def slow_response_findings(self) -> list[Finding]:
        if len(self.recent) < MIN_ENQUIRIES or self.late_hours is None:
            return []
        if self.late_hours < SLOW_RESPONSE_HOURS:
            return []
        share = self._share(self.late, self.recent)
        lost = self._share(self._lost(self.late), self.late)
        lost_on_time = self._share(self._lost(self.on_time), self.on_time)
        return [
            Finding(
                id="CLI-RESPUESTA",
                area=Area.CUSTOMERS,
                title=(
                    f"Las consultas fuera de horario ({share} % del total) tardan "
                    f"{fmt_num(self.late_hours)} h en contestarse"
                ),
                detail=(
                    f"Dentro del horario se contestan en "
                    f"{fmt_num(self.on_time_hours or Decimal(0))} h. "
                    f"Fuera de horario se pierde el {lost} % de las consultas, frente al "
                    f"{lost_on_time} % dentro."
                ),
                evidence=(
                    Evidence(
                        source=SOURCES[0],
                        fact=(
                            f"{len(self.late)} de {len(self.recent)} consultas de los últimos "
                            f"{WINDOW_DAYS} días llegaron fuera de horario o en fin de semana"
                        ),
                    ),
                    Evidence(
                        source=SOURCES[0],
                        fact=(
                            f"Mediana de primera respuesta: {fmt_num(self.late_hours)} h fuera de "
                            f"horario y {fmt_num(self.on_time_hours or Decimal(0))} h dentro"
                        ),
                    ),
                    Evidence(
                        source=SOURCES[0],
                        fact=f"Perdidas: {lost} % fuera de horario y {lost_on_time} % dentro",
                    ),
                ),
                confidence=Confidence.HIGH,
                impact=4,
                urgency=4,
                effort=2,
                signals=frozenset({Signal.SLOW_RESPONSE}),
                metrics={
                    "late_hours": self.late_hours,
                    "late_share": share or Decimal(0),
                    "late_lost": lost or Decimal(0),
                },
            )
        ]

    def unassigned_findings(self) -> list[Finding]:
        if len(self.unassigned) < MIN_UNASSIGNED:
            return []
        oldest = max(self.today - o.created_at for o in self.unassigned)
        return [
            Finding(
                id="CLI-SIN-ASIGNAR",
                area=Area.CUSTOMERS,
                title=f"{len(self.unassigned)} oportunidades abiertas siguen sin responsable",
                detail="Nadie se ha hecho cargo de ellas en más de 48 horas.",
                evidence=(
                    Evidence(
                        source=SOURCES[0],
                        fact=(
                            f"{len(self.unassigned)} oportunidades abiertas sin responsable; "
                            f"la más antigua, de hace {oldest.days} días"
                        ),
                    ),
                ),
                confidence=Confidence.HIGH,
                impact=3,
                urgency=3,
                effort=1,
                signals=frozenset({Signal.UNASSIGNED_LEADS}),
                metrics={"unassigned": Decimal(len(self.unassigned))},
            )
        ]


def _gaps(data: CompanyData) -> tuple[DataGap, ...]:
    gaps = [
        DataGap(
            area=Area.CUSTOMERS,
            missing="Conexión al ERP/CRM real",
            why_it_matters="Hoy se leen las oportunidades del ERP de demo (ver ADR 005)",
        ),
        DataGap(
            area=Area.CUSTOMERS,
            missing="Motivo de cada oportunidad perdida",
            why_it_matters="Con él sabría si se pierden por precio, por espera o por no contestar",
        ),
    ]
    if not data.opportunities:
        gaps.insert(
            0,
            DataGap(
                area=Area.CUSTOMERS,
                missing="Oportunidades del ERP/CRM",
                why_it_matters="Sin ellas no sé cuántas consultas llegan ni cuántas se pierden",
            ),
        )
    return tuple(gaps)
