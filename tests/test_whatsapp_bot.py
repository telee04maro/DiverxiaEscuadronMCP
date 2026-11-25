"""WhatsApp assistant (whatsapp-hack/, PowerShell): its offline suite and the real HTTP join with
the demo ERP. Windows only: the assistant runs on Windows PowerShell 5.1, as on the laptops."""

import json
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from vigia.audit import AuditLog, EventKind
from vigia.connectors.demo_erp import DemoErp
from vigia.connectors.http_api import build_server
from vigia.data.model import CompanyData
from vigia.llm.base import OfflineModel
from vigia.specialists.customers import CustomersSpecialist

BOT = Path(__file__).resolve().parents[1] / "whatsapp-hack"
POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")
TOKEN = "token-de-integracion-largo-123"

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or POWERSHELL is None,
    reason="El asistente de WhatsApp es PowerShell de Windows",
)


def _run(
    script: str, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    assert POWERSHELL is not None
    return subprocess.run(  # noqa: S603 - fixed interpreter and scripts from this repository
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(BOT / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        env=env,
        check=False,
    )


def test_offline_suite_passes() -> None:
    result = _run("HACK-Ciclo-Pruebas.ps1")
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]
    assert ", 0 fallos" in result.stdout


@pytest.fixture
def erp_api(tmp_path: Path) -> Iterator[tuple[DemoErp, str]]:
    erp = DemoErp(tmp_path / "erp.sqlite")
    server = build_server("127.0.0.1", 0, erp, TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield erp, f"http://127.0.0.1:{server.server_address[1]}/api/v1"
    finally:
        server.shutdown()
        server.server_close()


def test_bot_registers_whatsapp_enquiries_in_the_vigia_erp(
    erp_api: tuple[DemoErp, str], tmp_path: Path, before: CompanyData
) -> None:
    erp, url = erp_api
    env = {**os.environ, "VIGIA_ERP_TOKEN": TOKEN}
    result = _run(
        "HACK-Ciclo-Integracion.ps1", "-Url", url, "-Raiz", str(tmp_path / "ciclo"), env=env
    )
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]
    states = json.loads(result.stdout.strip().splitlines()[-1])

    # The effect, read back from the ERP itself: one enquiry per conversation, no duplicates.
    opportunities = erp.list_opportunities()
    assert len(opportunities) == 2  # the test chat and the public chat
    assert {states["prueba"]["opportunity_id"], states["publico"]["opportunity_id"]} == {
        o.id for o in opportunities
    }
    assert all(s["estado"] == "ALTA_CREADA" for s in (states["prueba"], states["publico"]))
    assert states["posts"] == 4  # a question and a closing per chat

    by_contact = {erp.contact(o.contact_id).email: o for o in opportunities}  # type: ignore[union-attr]
    test_chat = by_contact["carla.htest@example.com"]
    public_chat = by_contact["pablo.demo@example.com"]
    assert test_chat.summary.startswith("PRUEBA (HTEST)")
    assert erp.contact(test_chat.contact_id).phone is None  # type: ignore[union-attr]
    assert erp.contact(public_chat.contact_id).phone is not None  # type: ignore[union-attr]
    for opportunity in opportunities:
        assert opportunity.channel == "whatsapp"
        assert opportunity.first_response_at is not None
        assert isinstance(opportunity.created_at, datetime)
        assert opportunity.first_response_at >= opportunity.created_at

    # The join the demo shows: the attention agent counts what came in by WhatsApp today.
    today = before.company.model_copy(update={"analysis_date": datetime.now().date()})
    data = before.model_copy(update={"company": today, "opportunities": opportunities})
    log = AuditLog()
    CustomersSpecialist().analyze(data, OfflineModel(), log)
    seen = [e.message for e in log.events if e.kind == EventKind.SAW]
    assert any(m.startswith("2 consultas") for m in seen), seen
