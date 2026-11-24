"""A new company enters with its own spreadsheets; bad rows are reported, never invented."""

import io
from datetime import date
from decimal import Decimal

import pandas as pd

from vigia.audit import AuditLog
from vigia.data.intake import TEMPLATES, Interview, build_company_data
from vigia.llm.base import OfflineModel
from vigia.pipeline import analyze

INTERVIEW = Interview(
    name="Taller Ejemplo (ficticio)",
    sector="Taller mecánico",
    city="Málaga",
    employees=8,
    main_service="Revisión",
    main_price=Decimal("90"),
    main_cost=Decimal("55"),
)

FACTURAS = (
    "numero;cliente;tipo_cliente;email_cliente;fecha_emision;fecha_vencimiento;importe\n"
    "F-1;Flota Ejemplo;empresa;pagos@flota.example;01/09/2026;01/10/2026;2.400,00\n"
    "F-2;Flota Ejemplo;empresa;pagos@flota.example;01/10/2026;31/10/2026;1.800,50\n"
)
BANCO = (
    "fecha;concepto;importe;saldo\n"
    "01/09/2026;SALDO INICIAL;5.000,00;5.000,00\n"
    "15/10/2026;TRANSFERENCIA FLOTA REF F-1;2.400,00;7.400,00\n"
    "28/10/2026;NOMINAS;-6.000,00;1.400,00\n"
)


def test_templates_are_valid_csv_with_spanish_headers() -> None:
    text = TEMPLATES["facturas"].csv_text()
    assert text.startswith("numero;cliente;tipo_cliente")
    assert "1.234,56" in text


def test_company_enters_with_csv_and_gets_analysed() -> None:
    result = build_company_data(
        INTERVIEW,
        {"facturas": ("facturas.csv", FACTURAS.encode()), "banco": ("banco.csv", BANCO.encode())},
        today=date(2026, 11, 20),
    )
    assert result.errors == []
    assert result.data is not None
    assert result.loaded == {"Facturas emitidas": 2, "Extracto bancario": 3}
    analysis = analyze(result.data, OfflineModel(), AuditLog())
    titles = [f.title for f in analysis.findings]
    assert any("Flota Ejemplo" in t and "1.800,50 €" in t for t in titles)
    gaps = [g.missing for r in analysis.reports for g in r.gaps]
    assert "sesiones.csv" in gaps or any("Oportunidades" in g for g in gaps)


def test_bad_rows_are_reported_with_line_numbers() -> None:
    bad = FACTURAS + "F-3;X;cliente_raro;;32/13/2026;01/01/2027;mil\n"
    result = build_company_data(
        INTERVIEW, {"facturas": ("f.csv", bad.encode())}, today=date(2026, 11, 20)
    )
    assert result.data is not None
    assert len(result.data.invoices) == 2
    assert any("fila 4" in e for e in result.errors)


def test_missing_columns_are_reported() -> None:
    result = build_company_data(
        INTERVIEW, {"banco": ("b.csv", b"fecha,importe\n01/10/2026,10\n")}, today=date(2026, 11, 20)
    )
    assert any("faltan columnas" in e for e in result.errors)
    assert result.data is not None and result.data.bank == ()


def test_excel_files_are_accepted() -> None:
    frame = pd.DataFrame(
        [{"fecha": "20/10/2026", "nota": "2", "texto": "Tardaron semanas en darme cita."}]
    )
    buffer = io.BytesIO()
    frame.to_excel(buffer, index=False)
    result = build_company_data(
        INTERVIEW, {"resenas": ("resenas.xlsx", buffer.getvalue())}, today=date(2026, 11, 20)
    )
    assert result.errors == []
    assert result.data is not None and len(result.data.reviews) == 1
