"""Synthetic demo company: a fictitious physiotherapy clinic in Málaga.

The hackathon rules forbid real personal data, so every person, client and competitor
here is invented (e-mail domains use the reserved ``.example`` TLD). The data is
deterministic so the demo is reproducible.

Run ``uv run python -m centra.data.synthetic`` to regenerate ``data/demo/clinica-fisio``.
"""

import csv
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from centra.domain.money import eur

DEMO_ROOT = Path("data/demo/clinica-fisio")
BEFORE = "mes-0"
AFTER = "mes-1"

PRIVATE_PRICE = Decimal("40.00")

# Private sessions per month. Last year there was no autumn drop (only August),
# so this year's September-October drop is not seasonal.
PRIVATE_SESSIONS = {
    "2025-05": 425, "2025-06": 418, "2025-07": 380, "2025-08": 300, "2025-09": 430,
    "2025-10": 428, "2025-11": 420, "2025-12": 380, "2026-01": 430, "2026-02": 425,
    "2026-03": 432, "2026-04": 420, "2026-05": 428, "2026-06": 420, "2026-07": 385,
    "2026-08": 305, "2026-09": 372, "2026-10": 345, "2026-11": 372,
}  # fmt: skip


@dataclass(frozen=True)
class Insurer:
    client_id: str
    name: str
    email: str
    rate: Decimal
    pays_after_days: int
    sessions: dict[str, int]


INSURERS = (
    Insurer(
        "ASG-ALFA", "Aseguradora Alfa (ficticia)", "facturas@alfa-seguros.example",
        Decimal("28.40"), 30,
        {"2026-05": 118, "2026-06": 121, "2026-07": 109, "2026-08": 92, "2026-09": 117,
         "2026-10": 119, "2026-11": 120},
    ),
    Insurer(
        "ASG-BETA", "Mutua Beta (ficticia)", "pagos@mutuabeta.example",
        Decimal("27.85"), 95,
        {"2026-05": 112, "2026-06": 115, "2026-07": 108, "2026-08": 88, "2026-09": 114,
         "2026-10": 116, "2026-11": 113},
    ),
    Insurer(
        "ASG-GAMMA", "Seguros Gamma (ficticia)", "administracion@gamma-seguros.example",
        Decimal("29.10"), 45,
        {"2026-05": 66, "2026-06": 64, "2026-07": 61, "2026-08": 50, "2026-09": 66,
         "2026-10": 68, "2026-11": 65},
    ),
)  # fmt: skip

MONTHLY_COSTS = (
    (1, "ALQUILER LOCAL", Decimal("-2400.00")),
    (5, "GESTORIA Y SOFTWARE", Decimal("-390.00")),
    (5, "PUBLICIDAD LOCAL", Decimal("-250.00")),
    (10, "PROVEEDOR MATERIAL FISIOTERAPIA", Decimal("-860.00")),
    (15, "SUMINISTROS LUZ AGUA INTERNET", Decimal("-540.00")),
    (28, "NOMINAS", Decimal("-15800.00")),
    (30, "SEGUROS SOCIALES", Decimal("-5050.00")),
)

OPENING_BALANCE = Decimal("42780.00")
BANK_START = date(2026, 5, 1)

# Payments that happen after Centra's actions (only in the "after" snapshot).
# Gamma pays September two days earlier than usual after the friendly reminder;
# Beta pays July and August after the formal claim, September is still pending.
AFTER_ACTION_PAYMENTS = {
    "F-2026-09-ASG-GAMMA": date(2026, 11, 12),
    "F-2026-07-ASG-BETA": date(2026, 11, 20),
    "F-2026-08-ASG-BETA": date(2026, 11, 20),
}


def month_end(month: str) -> date:
    year, number = (int(part) for part in month.split("-"))
    first_next = date(year + number // 12, number % 12 + 1, 1)
    return first_next - timedelta(days=1)


def _invoices(until_month: str) -> list[dict[str, Any]]:
    rows = []
    for insurer in INSURERS:
        for month, sessions in insurer.sessions.items():
            if month > until_month:
                continue
            issued = month_end(month)
            rows.append(
                {
                    "id": f"F-{month}-{insurer.client_id}",
                    "client_id": insurer.client_id,
                    "client_name": insurer.name,
                    "client_type": "aseguradora",
                    "contact_email": insurer.email,
                    "issued": issued.isoformat(),
                    "due": (issued + timedelta(days=30)).isoformat(),
                    "amount": str(eur(insurer.rate * sessions)),
                }
            )
    return rows


def _payment_date(invoice: dict[str, Any], insurer: Insurer, until: date) -> date | None:
    scheduled = date.fromisoformat(invoice["issued"]) + timedelta(days=insurer.pays_after_days)
    if invoice["id"] in AFTER_ACTION_PAYMENTS:
        actual = AFTER_ACTION_PAYMENTS[invoice["id"]]
        return actual if actual <= until else None
    return scheduled if scheduled <= until else None


def _bank(invoices: list[dict[str, Any]], until: date) -> list[dict[str, str]]:
    entries: list[tuple[date, str, Decimal]] = []
    day = BANK_START
    while day <= until:
        month = day.strftime("%Y-%m")
        for cost_day, concept, amount in MONTHLY_COSTS:
            if day.day == cost_day:
                entries.append((day, concept, amount))
        entries.extend(_card_settlement(day, month))
        day += timedelta(days=1)
    by_id = {insurer.client_id: insurer for insurer in INSURERS}
    for invoice in invoices:
        paid_on = _payment_date(invoice, by_id[invoice["client_id"]], until)
        if paid_on is not None:
            concept = f"TRANSFERENCIA {invoice['client_name'].upper()} REF {invoice['id']}"
            entries.append((paid_on, concept, Decimal(invoice["amount"])))
    entries.sort(key=lambda entry: (entry[0], entry[2] < 0))
    balance = OPENING_BALANCE
    rows = []
    for on, concept, amount in entries:
        balance += amount
        rows.append(
            {
                "on": on.isoformat(),
                "concept": concept,
                "amount": str(amount),
                "balance": str(balance),
            }
        )
    return rows


SETTLEMENT_DAYS = (8, 15, 22)


def _card_settlement(day: date, month: str) -> list[tuple[date, str, Decimal]]:
    """Private patients pay by card; the bank settles a quarter of the month each week."""
    if month not in PRIVATE_SESSIONS:
        return []
    revenue = PRIVATE_PRICE * PRIVATE_SESSIONS[month]
    quarter = eur(revenue / 4)
    concept = f"LIQUIDACION TPV PARTICULARES {month}"
    if day.day in SETTLEMENT_DAYS:
        return [(day, concept, quarter)]
    if day == month_end(month):
        return [(day, concept, revenue - quarter * len(SETTLEMENT_DAYS))]
    return []


def _sessions(until_month: str) -> list[dict[str, str]]:
    rows = []
    for month, private in PRIVATE_SESSIONS.items():
        if month > until_month:
            continue
        rows.append(
            {
                "month": month,
                "client_type": "particular",
                "sessions": str(private),
                "revenue": str(PRIVATE_PRICE * private),
            }
        )
        insured = [ins for ins in INSURERS if month in ins.sessions]
        if insured:
            rows.append(
                {
                    "month": month,
                    "client_type": "aseguradora",
                    "sessions": str(sum(ins.sessions[month] for ins in insured)),
                    "revenue": str(sum(eur(ins.rate * ins.sessions[month]) for ins in insured)),
                }
            )
    return rows


REVIEWS_BEFORE = [
    ("2026-05-08", 5, "Muy buenos profesionales, me recuperé de la lumbalgia en pocas sesiones."),
    ("2026-05-21", 5, "Trato cercano y explican todo. Repetiré."),
    ("2026-06-03", 4, "Buen tratamiento, el local es algo pequeño."),
    ("2026-06-19", 5, "La fisio que me atendió fue genial con mi rodilla."),
    ("2026-07-02", 5, "Profesionales y puntuales."),
    ("2026-07-24", 4, "Bien en general, aparcar es complicado."),
    ("2026-08-12", 5, "Me atendieron rápido en pleno agosto."),
    ("2026-09-04", 3, "El tratamiento bien, pero tardaron casi tres semanas en darme cita."),
    ("2026-09-17", 2, "Esperé 40 minutos en recepción aunque tenía hora."),
    ("2026-09-29", 4, "Buenos fisios, aunque cuesta conseguir cita por la tarde."),
    ("2026-10-06", 2, "Imposible conseguir cita antes de dos semanas. Me fui a otra clínica."),
    ("2026-10-14", 5, "Excelente trato, como siempre."),
    ("2026-10-22", 3, "Buen fisio, pero la espera para la primera cita es demasiado larga."),
    ("2026-10-29", 2, "Me cambiaron la cita dos veces y al final esperé media hora."),
]

REVIEWS_AFTER = [
    ("2026-11-07", 4, "Me dieron cita en dos días, mejor que la última vez."),
    ("2026-11-15", 5, "Muy buena atención y sin esperas."),
    ("2026-11-21", 3, "Bien, aunque sigue costando encontrar hueco por la tarde."),
    ("2026-11-27", 5, "Profesionales de verdad. Primera visita muy completa."),
]

COMPETITORS = [
    {
        "name": "FisioSalud Centro (ficticia)",
        "distance_m": 350,
        "prices": {"Fisioterapia general": "38.00", "Punción seca": "42.00"},
        "first_visit_price": "20.00",
        "rating": "4.7",
        "review_count": 214,
    },
    {
        "name": "Fisio Muelle (ficticia)",
        "distance_m": 900,
        "prices": {"Fisioterapia general": "45.00", "Punción seca": "48.00"},
        "first_visit_price": None,
        "rating": "4.4",
        "review_count": 96,
    },
]

ADS = [
    {
        "page_name": "FisioSalud Centro (ficticia)",
        "ad_creative_bodies": [
            "Primera sesión de fisioterapia por solo 20 €. Sin esperas: cita en 24 h. "
            "Reserva online en el centro de Málaga."
        ],
        "ad_delivery_start_time": "2026-10-15",
        "ad_delivery_stop_time": None,
        "publisher_platforms": ["facebook", "instagram"],
        "ad_snapshot_url": "https://anuncios.example/fisiosalud/1",
    },
    {
        "page_name": "FisioSalud Centro (ficticia)",
        "ad_creative_bodies": ["Bono de 5 sesiones por 175 €. Válido hasta junio."],
        "ad_delivery_start_time": "2026-03-01",
        "ad_delivery_stop_time": "2026-06-30",
        "publisher_platforms": ["facebook"],
        "ad_snapshot_url": "https://anuncios.example/fisiosalud/2",
    },
    {
        "page_name": "Fisio Muelle (ficticia)",
        "ad_creative_bodies": ["Fisioterapia deportiva junto al puerto. Pide tu cita."],
        "ad_delivery_start_time": "2026-06-10",
        "ad_delivery_stop_time": None,
        "publisher_platforms": ["instagram"],
        "ad_snapshot_url": "https://anuncios.example/fisiomuelle/1",
    },
]

OWN_NAME = "Clínica Fisio Atarazanas (ficticia)"

SEARCH = [
    {"query": "fisioterapeuta málaga centro", "position": 1,
     "business": "FisioSalud Centro (ficticia)", "sponsored": True},
    {"query": "fisioterapeuta málaga centro", "position": 2,
     "business": "FisioSalud Centro (ficticia)", "sponsored": False},
    {"query": "fisioterapeuta málaga centro", "position": 3,
     "business": "Fisio Muelle (ficticia)", "sponsored": False},
    {"query": "fisioterapeuta málaga centro", "position": 6, "business": OWN_NAME,
     "sponsored": False},
    {"query": "fisio cita hoy málaga", "position": 1,
     "business": "FisioSalud Centro (ficticia)", "sponsored": True},
    {"query": "fisio cita hoy málaga", "position": 4,
     "business": "Fisio Muelle (ficticia)", "sponsored": False},
]  # fmt: skip


def _company(analysis_date: date) -> dict[str, Any]:
    return {
        "name": OWN_NAME,
        "sector": "Clínica de fisioterapia",
        "city": "Málaga",
        "employees": 15,
        "analysis_date": analysis_date.isoformat(),
        "services": [
            {"name": "Fisioterapia general", "price": "40.00", "direct_cost": "24.00"},
            {"name": "Punción seca", "price": "45.00", "direct_cost": "26.00"},
            {"name": "Suelo pélvico", "price": "50.00", "direct_cost": "28.00"},
            {"name": "Primera valoración", "price": "40.00", "direct_cost": "24.00"},
        ],
        "main_service": "Fisioterapia general",
        "avg_sessions_per_new_patient": "6",
        "goals": [
            "Recuperar a los pacientes particulares",
            "No tener que pedir una póliza de crédito",
        ],
        "resources": (
            "15 personas: 11 fisioterapeutas, 2 en recepción, 1 en administración y la "
            "gerente, que es la dueña. Sin CRM: agenda en un programa y cuentas en Excel."
        ),
        "queries_of_interest": ["fisioterapeuta málaga centro", "fisio cita hoy málaga"],
    }


def _write_csv(path: Path, rows: list[dict[str, str]] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: Any) -> None:  # noqa: ANN401 - plain JSON payload
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def write_snapshot(folder: Path, *, analysis_date: date, last_month: str) -> None:
    invoices = _invoices(last_month)
    reviews = REVIEWS_BEFORE + (REVIEWS_AFTER if last_month >= "2026-11" else [])
    _write_json(folder / "empresa.json", _company(analysis_date))
    _write_csv(folder / "facturas.csv", invoices)
    _write_csv(folder / "banco.csv", _bank(invoices, analysis_date))
    _write_csv(folder / "sesiones.csv", _sessions(last_month))
    _write_json(
        folder / "resenas.json",
        [{"on": on, "rating": rating, "text": text} for on, rating, text in reviews],
    )
    _write_json(folder / "competencia/anuncios.json", ADS)
    _write_json(folder / "competencia/competidores.json", COMPETITORS)
    _write_json(folder / "competencia/busqueda.json", SEARCH)


def main() -> None:
    write_snapshot(DEMO_ROOT / BEFORE, analysis_date=date(2026, 11, 2), last_month="2026-10")
    write_snapshot(DEMO_ROOT / AFTER, analysis_date=date(2026, 12, 2), last_month="2026-11")


if __name__ == "__main__":
    main()
