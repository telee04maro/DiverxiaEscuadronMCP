"""Acceptance tests for the red team's third round: AI grounding, data entry, personal data."""

import io
import re
import tempfile
import time
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import pytest
from openpyxl import Workbook  # type: ignore[import-untyped]

from vigia.actions.collections import EmailDraft, Origin, prepare_claim
from vigia.actions.mailer import ORIGINAL_TO
from vigia.audit import AuditLog, EventKind
from vigia.config import Settings
from vigia.connectors.balter_probe import _NoRedirect
from vigia.connectors.base import Enquiry, register_enquiry
from vigia.connectors.demo_erp import DemoErp
from vigia.coordinator.causes import LlmCause, LlmCrossing
from vigia.coordinator.causes import Origin as CauseOrigin
from vigia.data.intake import Interview, RowError, build_company_data, read_table
from vigia.data.model import (
    BankMovement,
    ClientType,
    CompanyData,
    Invoice,
    MonthlySessions,
    Review,
)
from vigia.domain.findings import Confidence
from vigia.finance.reconciliation import PaymentStatus, reconcile
from vigia.llm.base import LlmCall, OfflineModel, Tier
from vigia.pipeline import analyze, execute_plan
from vigia.specialists.competition import Theme, _rule_themes
from vigia.specialists.finance import overdue_by_client, private_trend


class Recorder:
    """Answers by schema and keeps every prompt, to check what would reach Claude."""

    def __init__(self, answers: dict[type, object] | None = None) -> None:
        self.answers = answers or {}
        self.prompts: list[str] = []

    @property
    def mode(self) -> str:
        return "guion"

    @property
    def calls(self) -> tuple[LlmCall, ...]:
        return ()

    def structured(self, *, task, tier: Tier, system: str, prompt: str, schema):  # type: ignore[no-untyped-def]
        self.prompts.append(f"{system}\n{prompt}")
        return self.answers.get(schema)


class Outbox:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> str:
        self.sent.append(message)
        return "buzón de prueba"


def _gamma(before: CompanyData) -> tuple[list[Any], date]:
    today = before.company.analysis_date
    statuses = reconcile(before.invoices, before.bank, as_of=today)
    return overdue_by_client(statuses, today)["ASG-GAMMA"], today


# R3-01: the AI e-mail may not add a bank account, a link, a phone, a date or a figure.
@pytest.mark.parametrize(
    "extra",
    [
        "Pague en la NUEVA cuenta ES91 2100 0418 4502 0005 1332.",
        "Puede pagar en https://pagos-clinica.example/x",
        "Llámenos al 612 345 678.",
        "Le rogamos el pago antes del 26/11/2026.",
        "Tiene un plazo de 5 días para pagar.",
    ],
)
def test_r3_01_ungrounded_email_falls_back_to_template(before: CompanyData, extra: str) -> None:
    items, today = _gamma(before)
    body = f"La factura F-2026-09-ASG-GAMMA de 1.920,60 € consta pendiente. {extra}"
    model = Recorder({EmailDraft: EmailDraft(subject="Recordatorio", body=body)})
    log = AuditLog()
    claim = prepare_claim(before.company, items, model, log, today=today)
    assert claim.origin is Origin.TEMPLATE
    assert any(e.kind is EventKind.REJECTED for e in log.events)


def test_r3_01_grounded_email_still_passes(before: CompanyData) -> None:
    items, today = _gamma(before)
    body = (
        "Hola: la factura F-2026-09-ASG-GAMMA, vencida el 30/10/2026 (3 días), de 1.920,60 € "
        "consta pendiente. ¡Gracias!"
    )
    model = Recorder({EmailDraft: EmailDraft(subject="Recordatorio de pago", body=body)})
    claim = prepare_claim(before.company, items, model, AuditLog(), today=today)
    assert claim.origin is Origin.AI


# R3-02: a cause with a percentage or a number of days the findings do not hold is rejected.
def _crossing(explanation: str) -> LlmCrossing:
    cause = LlmCause(
        title="Particulares y caja",
        explanation=explanation,
        finding_ids=["FIN-PARTICULARES", "FIN-CAJA"],
        confidence=Confidence.HIGH,
    )
    return LlmCrossing(causes=[cause], discarded=[])


def test_r3_02_invented_percentage_is_rejected(before: CompanyData) -> None:
    text = "Los particulares caen un 45 % y la aseguradora paga a 200 días."
    analysis = analyze(before, Recorder({LlmCrossing: _crossing(text)}), AuditLog())
    assert analysis.crossing.origin is CauseOrigin.RULES


def test_r3_02_grounded_figures_are_accepted(before: CompanyData) -> None:
    text = "Los particulares caen un 15,4 % y la caja solo cubre 9 días."
    analysis = analyze(before, Recorder({LlmCrossing: _crossing(text)}), AuditLog())
    assert analysis.crossing.origin is CauseOrigin.AI


# R3-03: a debt that is 1 % of the cash is not "the cause" of a tight cash position.
def test_r3_03_small_debt_is_not_blamed_for_the_cash(before: CompanyData) -> None:
    today = before.company.analysis_date
    tiny = Invoice(
        id="F-SMALL",
        client_id="ASG-BETA",
        client_name="Mutua Beta (ficticia)",
        client_type=ClientType.INSURER,
        contact_email="pagos@mutuabeta.example",
        issued=today - timedelta(days=145),
        due=today - timedelta(days=115),
        amount=Decimal("50.00"),
    )
    data = before.model_copy(update={"invoices": (tiny,)})
    analysis = analyze(data, OfflineModel(), AuditLog())
    assert not any("caja está al límite" in c.title for c in analysis.crossing.causes)


# R3-04 / R3-05: no reference, or a statement that starts too late, is "unknown".
def _invoice(invoice_id: str, issued: date, due: date) -> Invoice:
    return Invoice(
        id=invoice_id,
        client_id="C1",
        client_name="Cliente (ficticio)",
        client_type=ClientType.COMPANY,
        contact_email="c1@cliente.example",
        issued=issued,
        due=due,
        amount=Decimal("1000.00"),
    )


def _move(concept: str, amount: str, on: date) -> BankMovement:
    return BankMovement(on=on, concept=concept, amount=Decimal(amount), balance=Decimal(0))


def test_r3_04_invoice_without_number_is_never_paid_by_chance() -> None:
    blank = _invoice(" ", date(2026, 9, 1), date(2026, 10, 1))
    [status] = reconcile(
        (blank,), (_move("DEVOLUCION RECIBO  / SEGURO", "1000.00", date(2026, 8, 1)),)
    )
    assert status.status is PaymentStatus.UNKNOWN


def test_r3_05_statement_after_the_invoice_means_unknown_not_unpaid() -> None:
    invoice = _invoice("F-50", date(2026, 11, 1), date(2026, 11, 15))
    bank = (_move("NOMINAS", "-500.00", date(2026, 11, 12)),)
    [status] = reconcile((invoice,), bank, as_of=date(2026, 11, 24))
    assert status.status is PaymentStatus.UNKNOWN
    assert status.outstanding == 0  # nobody is chased for it


# R3-06: without a collection e-mail there is no claim, and it is not reported as sent.
def test_r3_06_no_email_no_claim(before: CompanyData) -> None:
    invoices = tuple(
        i.model_copy(update={"contact_email": ""}) if i.client_id == "ASG-GAMMA" else i
        for i in before.invoices
    )
    data = before.model_copy(update={"invoices": invoices})
    log, outbox = AuditLog(), Outbox()
    analysis = analyze(data, OfflineModel(), log)
    execution = execute_plan(analysis, OfflineModel(), outbox, log, Settings())
    assert all(m["To"] for m in outbox.sent)
    assert not any(s.claim.client_id == "ASG-GAMMA" for s in execution.sent)
    assert any("Sin correo de cobro" in e.message for e in log.events)
    gaps = [g.missing for r in analysis.reports for g in r.gaps]
    assert any("Correo de cobro" in g for g in gaps)


# R3-07: «Borrar todos los datos» leaves nothing personal in the file.
def test_r3_07_reset_wipes_the_file(tmp_path: Path) -> None:
    path = tmp_path / "erp.sqlite"
    erp = DemoErp(path)
    enquiry = Enquiry(
        name="Persona Secreta",
        phone="611223344",
        email="secreta@x.example",
        topic="Cita",
        summary="embarazada de 20 semanas",
    )
    register_enquiry(erp, enquiry, AuditLog())
    erp.reset()
    raw = path.read_bytes()
    for needle in (b"Persona Secreta", b"611223344", b"secreta@x.example", b"embarazada"):
        assert needle not in raw


# R3-08: reviews keep no names or contact details; Claude never reads a debtor's name.
def test_r3_08_reviews_are_stored_without_personal_data() -> None:
    text = (
        "Me atendió Juan Pérez García, muy bien. Llamadme al 612 345 678 o a ana@correo.example "
        "(Ana López). DNI 12345678Z."
    )
    review = Review(on=date(2026, 10, 1), rating=4, text=text)
    for secret in ("Juan", "Pérez", "612 345 678", "ana@correo.example", "Ana López", "12345678Z"):
        assert secret not in review.text
    assert "muy bien" in review.text


def test_r3_08_claude_reads_pseudonyms_not_debtors(before: CompanyData) -> None:
    model = Recorder()
    analysis = analyze(before, model, AuditLog())
    sent = "\n".join(model.prompts)
    assert "Mutua Beta" not in sent and "Seguros Gamma" not in sent
    assert re.search(r"Aseguradora \d+", sent)  # the kind, never the name
    items, today = _gamma(before)
    prepare_claim(before.company, items, model, AuditLog(), today=today)
    assert "Seguros Gamma" not in model.prompts[-1]
    assert analysis.findings  # the analysis itself still names them, locally


def test_r3_08_real_names_come_back_in_the_cause(before: CompanyData) -> None:
    probe = Recorder()
    analyze(before, probe, AuditLog())
    found = re.search(
        r"\[FIN-COBRO-ASG-BETA\][^\n]*?((?:Aseguradora|Empresa|Particular|Cliente) \d+)",
        "\n".join(probe.prompts),
    )
    assert found is not None  # Mutua Beta reached the model only as a pseudonym
    alias = found.group(1)
    answer = LlmCrossing(
        causes=[
            LlmCause(
                title=f"La caja depende de {alias}",
                explanation=f"{alias} debe 8.633,50 € y la caja solo cubre 9 días.",
                finding_ids=["FIN-COBRO-ASG-BETA", "FIN-CAJA"],
                confidence=Confidence.HIGH,
            )
        ],
        discarded=[],
    )
    analysis = analyze(before, Recorder({LlmCrossing: answer}), AuditLog())
    assert analysis.crossing.origin is CauseOrigin.AI
    assert "Mutua Beta (ficticia)" in analysis.crossing.causes[0].title


# R3-09: a tiny workbook with a huge row is refused at once.
def _bomb(cells: int) -> bytes:
    wb = Workbook()
    wb.active.append(["fecha", "nota", "texto"])
    base = io.BytesIO()
    wb.save(base)
    src = zipfile.ZipFile(io.BytesIO(base.getvalue()))
    row = "".join(f'<c t="n"><v>{i % 10}</v></c>' for i in range(cells))
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?><worksheet '
        'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData><row r="1">{row}</row></sheetData></worksheet>'
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            name = item.filename
            data = sheet.encode() if name == "xl/worksheets/sheet1.xml" else src.read(item)
            dst.writestr(item, data)
    return out.getvalue()


def test_r3_09_xlsx_bomb_is_refused_fast() -> None:
    start = time.perf_counter()
    with pytest.raises(RowError, match="demasiadas celdas"):
        read_table("bomba.xlsx", _bomb(200_000))
    assert time.perf_counter() - start < 2


# R3-10: an e-mail with a line break is a row error, not a crash later.
def test_r3_10_header_injection_in_email_is_a_row_error() -> None:
    header = "numero;cliente;tipo_cliente;email_cliente;fecha_emision;fecha_vencimiento;importe\n"
    row = 'F-1;C;empresa;"pagos@cli.example\r\nBcc: otro@x.example";01/09/2026;01/10/2026;100,00\n'
    interview = Interview(
        name="Empresa (ficticia)",
        sector="Taller",
        city="Málaga",
        employees=5,
        main_service="Revisión",
        main_price=Decimal(90),
        main_cost=Decimal(55),
    )
    result = build_company_data(
        interview, {"facturas": ("f.csv", (header + row).encode())}, today=date(2026, 11, 2)
    )
    assert any("correo" in e for e in result.errors)


# R3-11: a month that has not ended is not a drop.
def test_r3_11_current_month_is_left_out() -> None:
    months = [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 12)]
    sessions = tuple(
        MonthlySessions(
            month=m,
            client_type=ClientType.PRIVATE,
            sessions=300 if m == "2026-11" else 400,
            revenue=Decimal(1),
        )
        for m in months
    )
    trend = private_trend(sessions, date(2026, 11, 24))
    assert trend is not None and trend.change_pct == 0


# R3-12: praise about appointments is not a complaint about waiting.
@pytest.mark.parametrize(
    ("text", "complaint"),
    [
        ("Me dieron cita el mismo día, muy caro eso sí", False),
        ("Muy buena atención y sin esperas.", False),
        ("Me dieron cita en dos días, mejor que la última vez.", False),
        ("Imposible conseguir cita antes de dos semanas.", True),
        ("Buenos fisios, aunque cuesta conseguir cita por la tarde.", True),
        ("Esperé 40 minutos en recepción aunque tenía hora.", True),
    ],
)
def test_r3_12_wait_complaints_need_a_complaint(text: str, complaint: bool) -> None:
    assert (Theme.WAIT in _rule_themes(text)) is complaint


# R3-14: the BALTER key is never sent to wherever a redirect points.
def test_r3_14_probe_does_not_follow_redirects() -> None:
    handler = _NoRedirect()
    result = handler.redirect_request(None, None, 302, "Found", {}, "http://otro.example/")  # type: ignore[func-returns-value]
    assert result is None


# R3-15: an unknown distance is unknown, not 0 m.
def test_r3_15_missing_distance_is_none() -> None:
    header = "nombre;distancia_m;servicio;precio;precio_primera_visita;nota;num_resenas\n"
    rows = read_table("c.csv", (header + "Rival;;Revisión;79,00;;4,6;120\n").encode())
    assert rows[0]["distancia_m"] == ""
    interview = Interview(
        name="Taller (ficticio)",
        sector="Taller",
        city="Sevilla",
        employees=5,
        main_service="Revisión",
        main_price=Decimal(95),
        main_cost=Decimal(60),
    )
    result = build_company_data(
        interview,
        {"competidores": ("c.csv", (header + "Rival;;Revisión;79,00;;4,6;120\n").encode())},
        today=date(2026, 11, 24),
    )
    assert result.data is not None and result.data.competitors[0].distance_m is None


# R3-17: header names are ASCII.
def test_r3_17_header_name_is_ascii() -> None:
    assert ORIGINAL_TO.isascii()


def test_tempdir_cleanup_is_possible() -> None:
    """Guard for Windows: the ERP closes its connections (reset() above relies on it)."""
    with tempfile.TemporaryDirectory() as folder:
        erp = DemoErp(Path(folder) / "erp.sqlite")
        erp.reset()


def test_r3_02_a_real_number_with_the_wrong_unit_is_rejected(before: CompanyData) -> None:
    """Gamma pays at 45 days: that does not back "particulares caen un 45 %"."""
    text = "Los particulares caen un 45 % y la caja solo cubre 9 días."
    analysis = analyze(before, Recorder({LlmCrossing: _crossing(text)}), AuditLog())
    assert analysis.crossing.origin is CauseOrigin.RULES
