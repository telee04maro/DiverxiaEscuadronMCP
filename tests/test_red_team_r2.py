"""Acceptance tests for the red team's second round (ERP connector, customers agent, intake)."""

import json
import socket
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from decimal import Decimal
from http.client import HTTPConnection
from pathlib import Path
from typing import Any

import pytest

from vigia.audit import AuditLog
from vigia.connectors.base import Enquiry, normalize_phone, register_enquiry
from vigia.connectors.demo_erp import DemoErp
from vigia.connectors.http_api import build_server
from vigia.coordinator.causes import losing_after_hours
from vigia.data.intake import Interview, build_company_data
from vigia.data.model import CompanyData, OpportunityStatus
from vigia.llm.base import OfflineModel
from vigia.specialists.customers import CustomersSpecialist, is_after_hours

TOKEN = "token-de-prueba-largo-123"
INTERVIEW = Interview(
    name="Taller Ejemplo (ficticio)",
    sector="Taller",
    city="Málaga",
    employees=5,
    main_service="Revisión",
    main_price=Decimal(90),
    main_cost=Decimal(55),
)
FACTURAS_HEADER = (
    "numero;cliente;tipo_cliente;email_cliente;fecha_emision;fecha_vencimiento;importe\n"
)


@pytest.fixture
def erp(tmp_path: Path) -> DemoErp:
    return DemoErp(tmp_path / "erp.sqlite", clock=lambda: datetime(2026, 11, 24, 21, 30))


@pytest.fixture
def api(erp: DemoErp) -> Iterator[int]:
    server = build_server("127.0.0.1", 0, erp, TOKEN)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def _post(port: int, body: object, token: str = TOKEN) -> int:
    connection = HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    connection.request("POST", "/api/v1/enquiries", body=json.dumps(body), headers=headers)
    status = connection.getresponse().status
    connection.close()
    return status


def _raw(port: int, request: bytes) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
        sock.sendall(request)
        return sock.recv(4096)


# R2-01: concurrent messages from the same person never duplicate.
def test_concurrent_enquiries_create_one_contact_and_one_opportunity(
    api: int, erp: DemoErp
) -> None:
    body = {"name": "Paciente", "phone": "600000009", "topic": "Cita", "summary": "Hombro"}
    with ThreadPoolExecutor(max_workers=20) as pool:
        statuses = list(pool.map(lambda _: _post(api, body), range(20)))
    assert statuses == [201] * 20
    opportunities = erp.list_opportunities()
    assert len(opportunities) == 1
    assert len({o.contact_id for o in opportunities}) == 1
    assert len(erp.notes(opportunities[0].id)) == 19


# R2-02: every way WhatsApp or a person writes a Spanish number is the same contact.
@pytest.mark.parametrize(
    "raw", ["600000001", "+34 600 000 001", "0034600000001", "34600000001", "+34 (0) 600000001"]
)
def test_phone_formats_are_one_number(raw: str) -> None:
    assert normalize_phone(raw) == "+34600000001"


def test_non_ascii_digits_are_rejected() -> None:
    with pytest.raises(ValueError, match="Teléfono"):
        normalize_phone("６００００００１")


# R2-03: a timestamp with a time zone does not crash the agent.
def test_time_zone_aware_times_are_compared_safely(erp: DemoErp, before: CompanyData) -> None:
    received = datetime(2026, 11, 24, 21, 0, tzinfo=UTC)
    enquiry = Enquiry(
        name="Paciente", phone="600000003", topic="Cita", received_at=received, answered_at=received
    )
    register_enquiry(erp, enquiry, AuditLog())
    data = before.model_copy(update={"opportunities": erp.list_opportunities()})
    CustomersSpecialist().analyze(data, OfflineModel(), AuditLog())
    assert erp.list_opportunities()[0].created_at.tzinfo is None


def test_answer_before_reception_is_rejected() -> None:
    with pytest.raises(ValueError, match="anterior"):
        Enquiry(
            name="Paciente",
            phone="600000003",
            topic="Cita",
            received_at=datetime(2026, 11, 24, 21),
            answered_at=datetime(2026, 11, 24, 20),
        )


# R2-04: a missing figure reads «sin datos», never «None» or «0 h».
def test_missing_on_time_answers_read_sin_datos(before: CompanyData) -> None:
    company = before.company
    opportunities = tuple(
        o
        if is_after_hours(o.created_at, company)
        else o.model_copy(update={"first_response_at": None})
        for o in before.opportunities
    )
    data = before.model_copy(update={"opportunities": opportunities})
    report = CustomersSpecialist().analyze(data, OfflineModel(), AuditLog())
    text = " ".join(
        f"{f.title} {f.detail} " + " ".join(e.fact for e in f.evidence) for f in report.findings
    )
    assert "None" not in text
    assert "sin datos" in text


# R2-05: no "late answers lose customers" claim when the data does not show it.
def test_no_after_hours_loss_claim_without_more_losses(before: CompanyData) -> None:
    slow = next(
        f
        for f in CustomersSpecialist().analyze(before, OfflineModel(), AuditLog()).findings
        if f.id == "CLI-RESPUESTA"
    )
    assert losing_after_hours(slow)
    even = {**slow.metrics, "late_lost": Decimal(20), "on_time_lost": Decimal(20)}
    assert not losing_after_hours(slow.model_copy(update={"metrics": even}))
    none_lost = {**slow.metrics, "late_lost": Decimal(0)}
    assert not losing_after_hours(slow.model_copy(update={"metrics": none_lost}))


def test_window_includes_the_analysis_day(before: CompanyData) -> None:
    day = before.company.analysis_date
    last = before.opportunities[-1].model_copy(
        update={
            "id": "OP-HOY",
            "created_at": datetime.combine(day, datetime.min.time()).replace(hour=22),
            "status": OpportunityStatus.OPEN,
        }
    )
    data = before.model_copy(update={"opportunities": (*before.opportunities, last)})
    analyst = CustomersSpecialist()
    count = analyst.analyze(data, OfflineModel(), AuditLog()).kpi("consultas_30d")
    base = analyst.analyze(before, OfflineModel(), AuditLog()).kpi("consultas_30d")
    assert count is not None and base is not None
    assert count.value is not None and base.value is not None
    assert count.value == base.value + 1


# R2-08 / R2-09 / R2-10: malformed requests get a clear status, never a stack trace.
def test_missing_content_length_is_411(api: int) -> None:
    request = (
        f"POST /api/v1/enquiries HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {TOKEN}\r\n"
        "Connection: close\r\n\r\n"
    ).encode()
    assert b" 411 " in _raw(api, request)


def test_negative_content_length_is_400(api: int) -> None:
    request = (
        f"POST /api/v1/enquiries HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {TOKEN}\r\n"
        "Content-Length: -1\r\nConnection: close\r\n\r\n"
    ).encode()
    assert b" 400 " in _raw(api, request)


def test_non_ascii_token_is_401(api: int) -> None:
    request = (
        b"GET /api/v1/opportunities HTTP/1.1\r\nHost: x\r\n"
        + "Authorization: Bearer contraseña-larga-de-prueba\r\n".encode()
        + b"Connection: close\r\n\r\n"
    )
    assert b" 401 " in _raw(api, request)


def test_deeply_nested_json_is_a_clean_error(api: int) -> None:
    body = "[" * 30_000 + "]" * 30_000  # under the 64 KB limit, deeper than the JSON parser allows
    connection = HTTPConnection("127.0.0.1", api, timeout=10)
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    connection.request("POST", "/api/v1/enquiries", body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read().decode()
    connection.close()
    assert response.status in {400, 422, 500}
    assert "Traceback" not in payload


# R2-06 / R2-07 / R2-14 / R2-16: garbage in the intake is a message, not an exception.
def _intake(filename: str, content: bytes) -> list[str]:
    result = build_company_data(
        INTERVIEW, {"facturas": (filename, content)}, today=date(2026, 11, 2)
    )
    return result.errors


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("facturas.xlsx", b"esto no es un excel"),
        ("facturas.csv", b"\x00\x01\x02"),
        ("facturas.csv", FACTURAS_HEADER.encode() + b"F-1;C;empresa;;01/09/2026;01/10/2026;NaN\n"),
        (
            "facturas.csv",
            FACTURAS_HEADER.encode() + b"F-1;C;empresa;;01/09/2026;01/10/2026;1e999\n",
        ),
        ("facturas.csv", b""),
    ],
)
def test_garbage_files_become_errors(filename: str, content: bytes) -> None:
    errors = _intake(filename, content)
    assert errors
    assert all("Traceback" not in e for e in errors)


def test_duplicate_invoice_is_not_counted_twice() -> None:
    rows = "F-1;C;empresa;;01/09/2026;01/10/2026;100,00\n" * 2
    errors = _intake("facturas.csv", (FACTURAS_HEADER + rows).encode())
    assert any("repetido" in e for e in errors)


def test_excel_spanish_encoding_is_read() -> None:
    rows = "F-1;Clínica Peña;empresa;;01/09/2026;01/10/2026;100,00\n"
    result = build_company_data(
        INTERVIEW,
        {"facturas": ("facturas.csv", (FACTURAS_HEADER + rows).encode("cp1252"))},
        today=date(2026, 11, 2),
    )
    assert not result.errors
    assert list(result.loaded.values()) == [1]


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("F-1;C;empresa;;01/09/2026;01/10/2026;-100,00", "positivo"),
        ("F-1;C;empresa;;01/10/2026;01/09/2026;100,00", "anterior"),
    ],
)
def test_impossible_invoices_are_rejected(row: str, message: str) -> None:
    errors = _intake("facturas.csv", (FACTURAS_HEADER + row + "\n").encode())
    assert any(message in e for e in errors)


def test_interview_rejects_closing_before_opening() -> None:
    data: dict[str, Any] = {**INTERVIEW.model_dump(), "opening_hour": 20, "closing_hour": 9}
    with pytest.raises(ValueError, match="cierre"):
        Interview.model_validate(data)
