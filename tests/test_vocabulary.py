"""The agents speak the company's language: patients in a clinic, customers in a garage."""

import re
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from vigia.audit import AuditLog
from vigia.data.intake import Interview, build_company_data
from vigia.data.model import CompanyData
from vigia.domain.vocabulary import GENERAL, HEALTH, vocabulary_for
from vigia.llm.base import OfflineModel
from vigia.pipeline import Analysis, analyze

CLINIC_WORDS = re.compile(r"pacient|sesion|primeras? visitas?|fisioterapeut", re.IGNORECASE)


@pytest.mark.parametrize(
    ("sector", "service", "customers", "searched_for"),
    [
        ("Clínica de fisioterapia", "Fisioterapia general", "pacientes", "fisioterapeuta"),
        ("Clínica dental", "Limpieza", "pacientes", "dentista"),
        ("Centro médico", "Consulta", "pacientes", "este servicio"),
        ("Taller mecánico", "Revisión completa", "clientes", "este servicio"),
        ("Restaurante", "Menú del día", "clientes", "este servicio"),
        ("Peluquería", "Corte y peinado", "clientes", "este servicio"),
    ],
)
def test_vocabulary_follows_the_sector(
    sector: str, service: str, customers: str, searched_for: str
) -> None:
    words = vocabulary_for(SimpleNamespace(sector=sector, main_service=service))
    assert words.customers == customers
    assert words.searched_for == searched_for
    assert words in (GENERAL, HEALTH) or words.customers == HEALTH.customers


def _months(n: int) -> list[str]:
    year, month, out = 2025, 1, []
    for _ in range(n):
        out.append(f"{year}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def _garage() -> CompanyData:
    sales = "mes;tipo_cliente;unidades;ingresos\n" + "".join(
        f"{m};particular;{210 if m in ('2026-09', '2026-10') else 300};16.500,00\n"
        for m in _months(22)
    )
    reviews = "fecha;nota;texto\n" + "".join(
        f"{d}/10/2026;2;Tres semanas de espera para darme cita.\n" for d in ("02", "10", "20")
    )
    reviews += "12/05/2026;5;Rápidos y serios.\n20/04/2026;5;Muy buen servicio.\n"
    competitors = (
        "nombre;distancia_m;servicio;precio;precio_primera_visita;nota;num_resenas\n"
        "Taller Rápido (ficticio);600;Revisión completa;79,00;;4,6;320\n"
    )
    interview = Interview(
        name="Taller Ejemplo (ficticio)",
        sector="Taller mecánico",
        city="Sevilla",
        employees=8,
        main_service="Revisión completa",
        main_price=Decimal(95),
        main_cost=Decimal(60),
    )
    uploads = {
        "ventas": ("ventas.csv", sales.encode()),
        "resenas": ("resenas.csv", reviews.encode()),
        "competidores": ("competidores.csv", competitors.encode()),
    }
    result = build_company_data(interview, uploads, today=date(2026, 11, 24))
    assert result.errors == [] and result.data is not None
    return result.data


def _texts(analysis: Analysis) -> str:
    parts: list[str] = []
    for report in analysis.reports:
        parts += [k.label for k in report.kpis] + list(report.sources)
        parts += [f"{g.missing} {g.why_it_matters}" for g in report.gaps]
        for f in report.findings:
            parts += [f.title, f.detail] + [f"{e.source} {e.fact}" for e in f.evidence]
    parts += [f"{c.title} {c.explanation}" for c in analysis.crossing.causes]
    parts += [f"{i.title} {i.why}" for i in analysis.plan.items]
    return "\n".join(parts)


def test_a_garage_reads_customers_and_sales_not_patients() -> None:
    analysis = analyze(_garage(), OfflineModel(), AuditLog())
    text = _texts(analysis)
    assert not CLINIC_WORDS.search(text), CLINIC_WORDS.findall(text)
    assert "Las ventas a particulares caen un 30,0 %" in text
    assert any("clientes particulares" in c.title for c in analysis.crossing.causes)


def test_missing_data_is_named_not_shown_as_a_file() -> None:
    analysis = analyze(_garage(), OfflineModel(), AuditLog())
    gaps = [g.missing for r in analysis.reports for g in r.gaps]
    assert not any(re.search(r"\.(csv|json)\b", g) for g in gaps), gaps
    assert "Facturas emitidas" in gaps


def test_the_clinic_still_reads_patients(before: CompanyData) -> None:
    analysis = analyze(before, OfflineModel(), AuditLog())
    assert analysis.crossing.causes[0].title.startswith("Se pierden pacientes particulares")
    assert "Las sesiones de particulares caen" in _texts(analysis)
