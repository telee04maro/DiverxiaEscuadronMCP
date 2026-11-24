"""The finding contract: what every specialist hands to the coordinator.

A finding without evidence cannot exist, and a KPI without data is "not available"
(value None), never zero.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Area(StrEnum):
    FINANCE = "finanzas"
    COMPETITION = "competencia"
    MARKETING = "marketing"
    LEGAL = "legal"
    PEOPLE = "personas"


AREA_LABELS: dict[Area, str] = {
    Area.FINANCE: "Finanzas",
    Area.COMPETITION: "Competencia y mercado",
    Area.MARKETING: "Marketing y clientes",
    Area.LEGAL: "Legal y cumplimiento",
    Area.PEOPLE: "Organización y personas",
}


class Confidence(StrEnum):
    HIGH = "alta"
    MEDIUM = "media"
    LOW = "baja"


class Signal(StrEnum):
    """Machine-readable facts a finding asserts; the coordinator's rules cross them."""

    PRIVATE_PATIENTS_DROP = "particulares_bajan"
    NOT_SEASONAL = "no_estacional"
    SLOW_INSURER_PAYMENT = "aseguradora_paga_tarde"
    RECENT_OVERDUE = "factura_vencida_reciente"
    TIGHT_CASH = "caja_tensa"
    COMPETITOR_OFFER = "oferta_competidor"
    COMPETITOR_PROMISES_NO_WAIT = "competidor_promete_sin_espera"
    HIGHER_PRICE = "precio_superior"
    WAIT_COMPLAINTS = "quejas_espera"
    RATING_DROP = "nota_baja"
    LOW_SEARCH_VISIBILITY = "visibilidad_baja"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    fact: str
    on: date | None = None


class Finding(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    area: Area
    title: str
    detail: str
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    confidence: Confidence
    impact: int = Field(ge=1, le=5)
    effort: int = Field(ge=1, le=5)
    urgency: int = Field(ge=1, le=5)
    signals: frozenset[Signal] = frozenset()


class DataGap(BaseModel):
    """Something the specialist could not see and what it would add."""

    model_config = ConfigDict(frozen=True)

    area: Area
    missing: str
    why_it_matters: str


class Kpi(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    value: Decimal | None
    unit: str
    note: str = ""

    @property
    def available(self) -> bool:
        return self.value is not None


class SpecialistReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    specialist: str
    area: Area
    sources: tuple[str, ...]
    kpis: tuple[Kpi, ...]
    findings: tuple[Finding, ...]
    gaps: tuple[DataGap, ...]

    def kpi(self, key: str) -> Kpi | None:
        return next((k for k in self.kpis if k.key == key), None)
