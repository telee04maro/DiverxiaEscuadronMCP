"""How a company gets in: the initial interview plus its own files (CSV or Excel).

Spreadsheets use Spanish headers and Spanish formats (1.234,56 € and 31/10/2026). Every row
is validated; a bad row is reported with its line number and never silently dropped or
turned into zero. Whatever the company does not upload becomes a gap in the analysis.
"""

import csv
import io
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, model_validator

from vigia.data.model import (
    BankMovement,
    ClientType,
    Company,
    CompanyData,
    Competitor,
    Invoice,
    MonthlySessions,
    Opportunity,
    OpportunityStatus,
    Review,
    Service,
)
from vigia.domain.money import MoneyError, eur

MAX_ROWS = 20_000
MAX_ERRORS_SHOWN = 8


@dataclass(frozen=True)
class Template:
    key: str
    label: str
    required: bool
    headers: tuple[str, ...]
    example: tuple[str, ...]
    help: str

    def csv_text(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
        writer.writerow(self.headers)
        writer.writerow(self.example)
        return buffer.getvalue()


TEMPLATES: dict[str, Template] = {
    t.key: t
    for t in (
        Template(
            "facturas", "Facturas emitidas", True,
            ("numero", "cliente", "tipo_cliente", "email_cliente", "fecha_emision",
             "fecha_vencimiento", "importe"),
            ("F-2026-001", "Mutua Ejemplo", "aseguradora", "pagos@mutua.example", "31/10/2026",
             "30/11/2026", "1.234,56"),
            "Una fila por factura. tipo_cliente: aseguradora, empresa o particular.",
        ),
        Template(
            "banco", "Extracto bancario", True,
            ("fecha", "concepto", "importe", "saldo"),
            ("15/11/2026", "TRANSFERENCIA MUTUA EJEMPLO REF F-2026-001", "1.234,56", "8.420,10"),
            "Tal como lo exporta el banco. Cobros en positivo, pagos en negativo.",
        ),
        Template(
            "ventas", "Ventas por mes", False,
            ("mes", "tipo_cliente", "unidades", "ingresos"),
            ("2026-10", "particular", "345", "13.800,00"),
            "mes en formato AAAA-MM. unidades: sesiones, servicios o pedidos.",
        ),
        Template(
            "oportunidades", "Consultas y oportunidades (CRM)", False,
            ("id", "contacto", "canal", "motivo", "urgente", "recibida", "respondida",
             "responsable", "estado"),
            ("OP-1", "CT-1", "whatsapp", "Primera visita", "no", "14/10/2026 21:10",
             "15/10/2026 09:40", "", "abierta"),
            "Fechas con hora. estado: abierta, ganada o perdida. Sin nombres de clientes.",
        ),
        Template(
            "resenas", "Reseñas propias", False,
            ("fecha", "nota", "texto"),
            ("20/10/2026", "2", "Tardaron dos semanas en darme cita."),
            "Solo el texto y la nota: sin el nombre de quien la escribe.",
        ),
        Template(
            "competidores", "Competidores", False,
            ("nombre", "distancia_m", "servicio", "precio", "precio_primera_visita", "nota",
             "num_resenas"),
            ("Clínica de enfrente", "350", "Fisioterapia general", "38,00", "20,00", "4,7", "214"),
            "Una fila por competidor y servicio comparable.",
        ),
    )
}  # fmt: skip


class Interview(BaseModel):
    """The initial interview, as the owner fills it in."""

    name: str = Field(min_length=1, max_length=120)
    sector: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=80)
    employees: int = Field(ge=1, le=10_000)
    main_service: str = Field(min_length=1, max_length=120)
    main_price: Decimal = Field(gt=0)
    main_cost: Decimal = Field(ge=0)
    sessions_per_new_client: Decimal | None = Field(default=None, gt=0)
    goals: tuple[str, ...] = ()
    resources: str = ""
    opening_hour: int = Field(default=9, ge=0, le=23)
    closing_hour: int = Field(default=20, ge=1, le=24)

    @model_validator(mode="after")
    def _opens_before_closing(self) -> "Interview":
        if self.closing_hour <= self.opening_hour:
            raise ValueError("La hora de cierre tiene que ser posterior a la de apertura")
        return self


@dataclass
class IntakeResult:
    data: CompanyData | None
    errors: list[str] = field(default_factory=list)
    loaded: dict[str, int] = field(default_factory=dict)


class RowError(ValueError):
    """A row cannot be read."""


def _key(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", plain.strip().lower()).strip("_")


def read_table(filename: str, content: bytes) -> list[dict[str, str]]:
    """Rows of a CSV (comma or semicolon) or Excel file, with normalized header names."""
    if filename.lower().endswith((".xlsx", ".xlsm")):
        frame = pd.read_excel(io.BytesIO(content), dtype=str, nrows=MAX_ROWS + 1)
        frame = frame.fillna("")
        rows = [{str(k): str(v) for k, v in r.items()} for r in frame.to_dict("records")]
    else:
        text = _decode(content)
        header = text.splitlines()[0] if text.strip() else ""
        delimiter = ";" if header.count(";") >= header.count(",") and ";" in header else ","
        rows = list(csv.DictReader(io.StringIO(text), delimiter=delimiter))
    if len(rows) > MAX_ROWS:
        raise RowError(f"Demasiadas filas (máximo {MAX_ROWS})")
    return [{_key(k): (v or "").strip() for k, v in row.items() if k} for row in rows]


def _decode(content: bytes) -> str:
    """UTF-8 first; Excel in Spanish saves CSV as Windows-1252."""
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1252", errors="strict")


def _date(raw: str) -> date:
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw.strip()[:10], pattern).date()
        except ValueError:
            continue
    raise RowError(f"fecha no válida «{raw}»")


def _datetime(raw: str) -> datetime:
    for pattern in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), pattern)
        except ValueError:
            continue
    raise RowError(f"fecha y hora no válidas «{raw}»")


def _money(raw: str) -> Decimal:
    try:
        return eur(raw)
    except MoneyError as error:
        raise RowError(f"importe no válido «{raw}»") from error


def _client_type(raw: str) -> ClientType:
    try:
        return ClientType(_key(raw))
    except ValueError as error:
        raise RowError(f"tipo de cliente no válido «{raw}»") from error


def _slug(text: str) -> str:
    return _key(text).upper()[:30] or "CLIENTE"


def _invoice(row: dict[str, str]) -> Invoice:
    issued, due, amount = (
        _date(row["fecha_emision"]),
        _date(row["fecha_vencimiento"]),
        _money(row["importe"]),
    )
    if amount <= 0:
        raise RowError("el importe de una factura debe ser positivo")
    if due < issued:
        raise RowError("el vencimiento es anterior a la emisión")
    return Invoice(
        id=row["numero"],
        client_id=_slug(row["cliente"]),
        client_name=row["cliente"],
        client_type=_client_type(row["tipo_cliente"]),
        contact_email=row.get("email_cliente", ""),
        issued=issued,
        due=due,
        amount=amount,
    )


def _movement(row: dict[str, str]) -> BankMovement:
    return BankMovement(
        on=_date(row["fecha"]),
        concept=row["concepto"],
        amount=_money(row["importe"]),
        balance=_money(row["saldo"]),
    )


def _sales(row: dict[str, str]) -> MonthlySessions:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", row["mes"]):
        raise RowError(f"mes no válido «{row['mes']}» (formato AAAA-MM)")
    units, revenue = int(row["unidades"]), _money(row["ingresos"])
    if units < 0 or revenue < 0:
        raise RowError("unidades e ingresos no pueden ser negativos")
    return MonthlySessions(
        month=row["mes"],
        client_type=_client_type(row["tipo_cliente"]),
        sessions=units,
        revenue=revenue,
    )


def _yes(raw: str) -> bool:
    return _key(raw) in {"si", "s", "true", "1", "yes"}


def _opportunity(row: dict[str, str]) -> Opportunity:
    answered = row.get("respondida", "")
    return Opportunity(
        id=row["id"],
        contact_id=row["contacto"],
        channel=row.get("canal") or "whatsapp",
        topic=row.get("motivo") or "Consulta",
        urgent=_yes(row.get("urgente", "")),
        created_at=_datetime(row["recibida"]),
        first_response_at=_datetime(answered) if answered else None,
        assigned_to=row.get("responsable") or None,
        status=OpportunityStatus(_key(row.get("estado") or "abierta")),
    )


def _review(row: dict[str, str]) -> Review:
    return Review(on=_date(row["fecha"]), rating=int(row["nota"]), text=row["texto"])


def _competitor(row: dict[str, str]) -> Competitor:
    first = row.get("precio_primera_visita", "")
    rating = row.get("nota", "")
    count = row.get("num_resenas", "")
    return Competitor(
        name=row["nombre"],
        distance_m=int(row.get("distancia_m") or 0),
        prices={row["servicio"]: _money(row["precio"])},
        first_visit_price=_money(first) if first else None,
        rating=_rating(rating) if rating else None,
        review_count=int(count) if count else None,
    )


def _rating(raw: str) -> Decimal:
    try:
        value = Decimal(raw.replace(",", "."))
    except ArithmeticError as error:
        raise RowError(f"nota no válida «{raw}»") from error
    if not value.is_finite() or not 0 <= value <= 5:  # noqa: PLR2004 - star ratings
        raise RowError(f"nota no válida «{raw}» (de 0 a 5)")
    return value


_UNIQUE_IDS = {"facturas": "numero", "oportunidades": "id"}

_PARSERS: dict[str, Callable[[dict[str, str]], Any]] = {
    "facturas": _invoice,
    "banco": _movement,
    "ventas": _sales,
    "oportunidades": _opportunity,
    "resenas": _review,
    "competidores": _competitor,
}


def _parse(key: str, rows: list[dict[str, str]], errors: list[str]) -> tuple[Any, ...]:
    template = TEMPLATES[key]
    missing = [h for h in template.headers if rows and h not in rows[0]]
    required_missing = [
        h for h in missing if h not in {"email_cliente", "responsable", "respondida"}
    ]
    if required_missing:
        errors.append(f"{template.label}: faltan columnas {', '.join(required_missing)}")
        return ()
    if not rows:
        errors.append(f"{template.label}: el fichero no tiene filas")
        return ()
    parsed = []
    seen: set[str] = set()
    unique = _UNIQUE_IDS.get(key)
    for line, row in enumerate(rows, start=2):
        if not any(row.values()):
            continue
        if unique and row.get(unique) in seen:
            errors.append(
                f"{template.label}, fila {line}: «{row[unique]}» está repetido; no se suma"
            )
            continue
        try:
            parsed.append(_PARSERS[key](row))
            if unique:
                seen.add(row[unique])
        except (RowError, ValidationError, ValueError, KeyError, ArithmeticError) as error:
            reason = (
                str(error).splitlines()[0] if not isinstance(error, KeyError) else f"falta {error}"
            )
            errors.append(f"{template.label}, fila {line}: {reason}")
    return tuple(parsed)


def build_company_data(
    interview: Interview, files: dict[str, tuple[str, bytes]], *, today: date
) -> IntakeResult:
    """``files`` maps a template key to (file name, content)."""
    errors: list[str] = []
    tables: dict[str, tuple[Any, ...]] = {}
    for key, (filename, content) in files.items():
        try:
            tables[key] = _parse(key, read_table(filename, content), errors)
        except RowError as error:
            errors.append(f"{TEMPLATES[key].label}: {error}")
        except Exception:  # corrupt or foreign files: a clear message, never a stack trace
            errors.append(
                f"{TEMPLATES[key].label}: no se puede leer «{filename}». Usa la plantilla "
                "(CSV con ; o ,, o Excel .xlsx)"
            )
    competitors = _merge_competitors(tables.get("competidores", ()))
    company = Company(
        name=interview.name,
        sector=interview.sector,
        city=interview.city,
        employees=interview.employees,
        analysis_date=today,
        services=(
            Service(
                name=interview.main_service,
                price=interview.main_price,
                direct_cost=interview.main_cost,
            ),
        ),
        main_service=interview.main_service,
        avg_sessions_per_new_patient=interview.sessions_per_new_client,
        goals=interview.goals,
        resources=interview.resources,
        opening_hour=interview.opening_hour,
        closing_hour=interview.closing_hour,
    )
    names = {
        "facturas": "facturas.csv",
        "banco": "banco.csv",
        "ventas": "sesiones.csv",
        "oportunidades": "crm/oportunidades.json",
        "resenas": "resenas.json",
        "competidores": "competencia/competidores.json",
    }
    missing = tuple(name for key, name in names.items() if not tables.get(key))
    data = CompanyData(
        company=company,
        invoices=tables.get("facturas", ()),
        bank=tables.get("banco", ()),
        sessions=tables.get("ventas", ()),
        opportunities=tables.get("oportunidades", ()),
        reviews=tables.get("resenas", ()),
        competitors=competitors,
        missing_sources=(*missing, "competencia/anuncios.json", "competencia/busqueda.json"),
    )
    loaded = {TEMPLATES[k].label: len(v) for k, v in tables.items()}
    return IntakeResult(data=data, errors=errors, loaded=loaded)


def _merge_competitors(rows: tuple[Any, ...]) -> tuple[Competitor, ...]:
    """One competitor may come in several rows (one per service)."""
    merged: dict[str, Competitor] = {}
    for competitor in rows:
        known = merged.get(competitor.name)
        if known is None:
            merged[competitor.name] = competitor
        else:
            merged[competitor.name] = known.model_copy(
                update={"prices": {**known.prices, **competitor.prices}}
            )
    return tuple(merged.values())
