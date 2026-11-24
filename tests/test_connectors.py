"""Demo ERP, the enquiry flow (no duplicates) and the HTTP API used by the WhatsApp assistant."""

import json
import threading
from collections.abc import Iterator
from datetime import datetime
from http.client import HTTPConnection
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from vigia.audit import AuditLog, EventKind
from vigia.connectors.base import Enquiry, NewContact, register_enquiry
from vigia.connectors.demo_erp import DemoErp, UnknownRecordError
from vigia.connectors.http_api import build_server

TOKEN = "token-de-prueba-largo-123"


@pytest.fixture
def erp(tmp_path: Path) -> DemoErp:
    return DemoErp(tmp_path / "erp.sqlite", clock=lambda: datetime(2026, 11, 24, 21, 30))


def _enquiry(**changes: Any) -> Enquiry:
    data: dict[str, Any] = {
        "name": "Paciente de prueba",
        "phone": "+34 600 000 001",
        "topic": "Primera visita",
        "summary": "Dolor lumbar desde hace dos semanas",
    }
    data.update(changes)
    return Enquiry.model_validate(data)


def test_first_enquiry_creates_contact_and_opportunity(erp: DemoErp) -> None:
    outcome = register_enquiry(erp, _enquiry(), AuditLog())
    assert outcome.new_contact and outcome.new_opportunity
    [opportunity] = erp.list_opportunities()
    assert opportunity.assigned_to is None  # a person assigns it
    assert erp.origin(opportunity.id) == "whatsapp"


def test_second_message_is_a_note_not_a_duplicate(erp: DemoErp) -> None:
    register_enquiry(erp, _enquiry(), AuditLog())
    outcome = register_enquiry(
        erp, _enquiry(phone="600000001", summary="¿Tenéis hueco el jueves?"), AuditLog()
    )
    assert not outcome.new_contact and not outcome.new_opportunity
    assert len(erp.list_opportunities()) == 1
    assert "jueves" in erp.notes(outcome.opportunity_id)[0]


def test_urgent_enquiry_is_escalated(erp: DemoErp) -> None:
    log = AuditLog()
    register_enquiry(erp, _enquiry(urgent=True), log)
    assert any(e.kind is EventKind.ESCALATED for e in log.events)


def test_contact_needs_phone_or_email() -> None:
    with pytest.raises(ValidationError):
        NewContact(name="Sin datos")
    with pytest.raises(ValidationError):
        _enquiry(phone="no es un teléfono")


def test_reset_deletes_everything(erp: DemoErp) -> None:
    register_enquiry(erp, _enquiry(), AuditLog())
    erp.reset()
    assert erp.list_opportunities() == ()
    assert erp.find_contact(phone="600000001", email=None) is None


def test_note_on_unknown_opportunity_fails(erp: DemoErp) -> None:
    with pytest.raises(UnknownRecordError):
        erp.add_note("OP-NOEXISTE", "x")


@pytest.fixture
def api(erp: DemoErp) -> Iterator[int]:
    server = build_server("127.0.0.1", 0, erp, TOKEN)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def _call(
    port: int, method: str, path: str, body: object = None, token: str = TOKEN
) -> tuple[int, Any]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    connection.request(method, path, body=payload, headers=headers)
    response = connection.getresponse()
    data = json.loads(response.read() or b"null")
    connection.close()
    return response.status, data


def test_api_requires_token(api: int) -> None:
    status, _ = _call(api, "GET", "/api/v1/opportunities", token="otro-token-cualquiera")
    assert status == 401


def test_api_enquiry_flow(api: int) -> None:
    body = {"name": "Paciente", "phone": "600000002", "topic": "Cita", "summary": "Rodilla"}
    status, outcome = _call(api, "POST", "/api/v1/enquiries", body)
    assert status == 201 and outcome["new_opportunity"]
    status, again = _call(api, "POST", "/api/v1/enquiries", body)
    assert status == 201 and not again["new_opportunity"]
    status, listed = _call(api, "GET", "/api/v1/opportunities")
    assert status == 200 and len(listed) == 1


def test_api_validates_and_hides_internals(api: int) -> None:
    status, error = _call(api, "POST", "/api/v1/enquiries", {"name": "x"})
    assert status == 422
    assert "Traceback" not in json.dumps(error)
    status, _ = _call(api, "POST", "/api/v1/opportunities/OP-X/notes", {"text": "hola"})
    assert status == 404


def test_short_token_is_refused(erp: DemoErp) -> None:
    with pytest.raises(ValueError, match="16"):
        build_server("127.0.0.1", 0, erp, "corto")
