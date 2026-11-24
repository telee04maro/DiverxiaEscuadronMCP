"""What Vigía knows about a company. Every collection may be empty: missing data is a gap."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vigia.domain.privacy import redact


def to_local_naive(value: datetime | None) -> datetime | None:
    """All times are local wall-clock times without zone, so they can be compared safely."""
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


class ClientType(StrEnum):
    INSURER = "aseguradora"
    COMPANY = "empresa"
    PRIVATE = "particular"


class Service(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    price: Decimal
    direct_cost: Decimal


SOURCE_LABELS = {
    "facturas.csv": "Facturas emitidas",
    "banco.csv": "Extracto bancario",
    "sesiones.csv": "Ventas o sesiones por mes",
    "resenas.json": "Reseñas propias",
    "competencia/anuncios.json": "Anuncios de la competencia",
    "competencia/competidores.json": "Precios de la competencia",
    "competencia/busqueda.json": "Resultados de búsqueda",
    "crm/oportunidades.json": "Consultas y oportunidades (CRM)",
}


class Company(BaseModel):
    """Profile collected in the initial interview."""

    model_config = ConfigDict(frozen=True)

    name: str
    sector: str
    city: str
    employees: int = Field(ge=1)
    analysis_date: date
    services: tuple[Service, ...]
    main_service: str
    avg_sessions_per_new_patient: Decimal | None = None
    goals: tuple[str, ...] = ()
    resources: str = ""
    queries_of_interest: tuple[str, ...] = ()
    opening_hour: int = Field(default=9, ge=0, le=23)
    closing_hour: int = Field(default=20, ge=1, le=24)

    def service(self, name: str) -> Service | None:
        return next((s for s in self.services if s.name == name), None)


class Invoice(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    client_id: str
    client_name: str
    client_type: ClientType
    contact_email: str
    issued: date
    due: date
    amount: Decimal


class BankMovement(BaseModel):
    model_config = ConfigDict(frozen=True)

    on: date
    concept: str
    amount: Decimal
    balance: Decimal


class MonthlySessions(BaseModel):
    model_config = ConfigDict(frozen=True)

    month: str
    client_type: ClientType
    sessions: int
    revenue: Decimal


class Review(BaseModel):
    """Public review, stored without the author's identity nor anyone else's (R3-08)."""

    model_config = ConfigDict(frozen=True)

    on: date
    rating: int = Field(ge=1, le=5)
    text: str

    @field_validator("text")
    @classmethod
    def _without_personal_data(cls, value: str) -> str:
        return redact(value)


class CompetitorAd(BaseModel):
    """One ad in the shape of the main fields of the Meta Ad Library."""

    model_config = ConfigDict(frozen=True)

    page_name: str
    ad_creative_bodies: tuple[str, ...]
    ad_delivery_start_time: date
    ad_delivery_stop_time: date | None = None
    publisher_platforms: tuple[str, ...] = ()
    ad_snapshot_url: str = ""

    def active_on(self, day: date) -> bool:
        started = self.ad_delivery_start_time <= day
        return started and (self.ad_delivery_stop_time is None or self.ad_delivery_stop_time >= day)


class Competitor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    distance_m: int | None = None  # unknown is not 0 m
    prices: dict[str, Decimal]
    first_visit_price: Decimal | None = None
    rating: Decimal | None = None
    review_count: int | None = None


class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    position: int = Field(ge=1)
    business: str
    sponsored: bool = False


class OpportunityStatus(StrEnum):
    OPEN = "abierta"
    WON = "ganada"
    LOST = "perdida"


class Opportunity(BaseModel):
    """An enquiry registered in the ERP/CRM (e.g. by the WhatsApp assistant)."""

    model_config = ConfigDict(frozen=True)

    id: str
    contact_id: str
    channel: str
    topic: str
    urgent: bool = False
    created_at: datetime
    first_response_at: datetime | None = None
    assigned_to: str | None = None
    status: OpportunityStatus = OpportunityStatus.OPEN
    summary: str = ""

    _times = field_validator("created_at", "first_response_at")(to_local_naive)


class CompanyData(BaseModel):
    model_config = ConfigDict(frozen=True)

    company: Company
    invoices: tuple[Invoice, ...] = ()
    bank: tuple[BankMovement, ...] = ()
    sessions: tuple[MonthlySessions, ...] = ()
    reviews: tuple[Review, ...] = ()
    competitor_ads: tuple[CompetitorAd, ...] = ()
    competitors: tuple[Competitor, ...] = ()
    search_results: tuple[SearchResult, ...] = ()
    opportunities: tuple[Opportunity, ...] = ()
    missing_sources: tuple[str, ...] = ()

    @property
    def missing_labels(self) -> tuple[str, ...]:
        return tuple(SOURCE_LABELS.get(name, name) for name in self.missing_sources)
