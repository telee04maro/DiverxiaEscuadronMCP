"""Vigía's CRM: one card per customer, joined by e-mail or phone, consistent with the agents."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from vigia.actions.collections import Claim, Origin, Tone
from vigia.audit import AuditLog
from vigia.connectors.base import Contact, Enquiry, register_enquiry
from vigia.connectors.demo_erp import DemoErp
from vigia.crm import ACTIONS, CUSTOMERS, FINANCE, CustomerCard, build_cards
from vigia.data.model import CompanyData, Opportunity
from vigia.llm.base import OfflineModel
from vigia.pipeline import analyze

MUTUA_EMAIL = "pagos@mutuabeta.example"


def _card(cards: tuple[CustomerCard, ...], name: str) -> CustomerCard:
    return next(c for c in cards if name in c.name)


def _claim(*, client_id: str = "ASG-BETA", to: str = MUTUA_EMAIL) -> Claim:
    return Claim(
        client_id=client_id,
        client_name="Mutua Beta (ficticia)",
        to=to,
        tone=Tone.FORMAL,
        subject="Reclamación",
        body="…",
        invoice_ids=("F-2026-07-ASG-BETA",),
        total=Decimal("3007.80"),
        origin=Origin.TEMPLATE,
        needs_approval=True,
    )


def _with_erp(before: CompanyData, tmp_path: Path, **enquiry: object) -> tuple[CustomerCard, ...]:
    erp = DemoErp(tmp_path / "erp.sqlite", clock=lambda: datetime(2026, 11, 2, 21, 0))
    data = {"topic": "Duda sobre facturas", "received_at": datetime(2026, 11, 1, 21, 0)}
    register_enquiry(erp, Enquiry.model_validate(data | enquiry), AuditLog())
    live = erp.list_opportunities()
    contacts = {o.contact_id: c for o in live if (c := erp.contact(o.contact_id))}
    return build_cards(before, contacts=contacts, extra_opportunities=live)


def test_cards_agree_with_the_agents(before: CompanyData) -> None:
    cards = build_cards(before)
    analysis = analyze(before, OfflineModel(), AuditLog())
    finance, _, customers = analysis.reports
    mutua = _card(cards, "Mutua Beta")
    assert mutua.overdue == Decimal("8633.50")
    days = finance.kpi("dias_cobro_ASG-BETA")
    assert days is not None and days.value == mutua.days_to_pay
    unassigned = customers.kpi("sin_asignar_48h")
    assert unassigned is not None and unassigned.value == sum(c.unattended for c in cards)


def test_unknown_debt_is_none_not_zero(before: CompanyData) -> None:
    contact_only = next(c for c in build_cards(before) if c.agents == (CUSTOMERS,))
    assert contact_only.overdue is None and contact_only.invoices == 0


def test_an_enquiry_with_the_same_email_joins_the_debt(before: CompanyData, tmp_path: Path) -> None:
    cards = _with_erp(before, tmp_path, name="Mutua Beta (ficticia)", email=MUTUA_EMAIL)
    mutuas = [c for c in cards if c.email == MUTUA_EMAIL]
    assert len(mutuas) == 1  # one customer, one card
    [mutua] = mutuas
    assert mutua.crossed and set(mutua.agents) == {FINANCE, CUSTOMERS}
    assert mutua.conflict is None
    assert any("contéstale antes de reclamarle" in a for a in mutua.alerts)
    assert cards[0] is mutua  # crossed alerts first


def test_same_email_different_name_is_flagged(before: CompanyData, tmp_path: Path) -> None:
    cards = _with_erp(before, tmp_path, name="Paciente de prueba", email=MUTUA_EMAIL)
    mutua = next(c for c in cards if c.email == MUTUA_EMAIL)
    assert mutua.conflict is not None and "Paciente de prueba" in mutua.conflict


def test_phone_formats_are_one_customer(before: CompanyData) -> None:
    contacts = {
        "CT-A": Contact(id="CT-A", name="Ana (ficticia)", phone="+34 600 000 001"),
        "CT-B": Contact(id="CT-B", name="Ana (ficticia)", phone="0034600000001"),
    }
    extra = tuple(
        Opportunity(
            id=f"OP-{cid}",
            contact_id=cid,
            channel="whatsapp",
            topic="Cita",
            created_at=datetime(2026, 11, 1, 10, 0),
        )
        for cid in contacts
    )
    cards = build_cards(before, contacts=contacts, extra_opportunities=extra)
    anas = [c for c in cards if c.name == "Ana (ficticia)"]
    assert len(anas) == 1 and anas[0].enquiries == 2


@pytest.mark.parametrize(("sent", "text"), [(False, "espera tu aprobación"), (True, "enviada")])
def test_claims_show_on_the_card(before: CompanyData, sent: bool, text: str) -> None:
    claim = _claim()
    cards = build_cards(before, sent=[claim] if sent else [], pending=[] if sent else [claim])
    mutua = _card(cards, "Mutua Beta")
    assert ACTIONS in mutua.agents
    shown = " ".join(mutua.alerts) + " ".join(f for _, f in mutua.facts)
    assert text in shown
    assert len([c for c in cards if "Mutua Beta" in c.name]) == 1


def test_a_malformed_email_does_not_break_the_card(before: CompanyData) -> None:
    cards = build_cards(before, pending=[_claim(client_id="X-1", to="no-es-un-correo")])
    assert any(c.key == "client:X-1" for c in cards)


def test_a_company_without_problems_has_no_alerts(before: CompanyData) -> None:
    quiet = before.model_copy(update={"invoices": (), "bank": (), "opportunities": ()})
    assert build_cards(quiet) == ()


def test_a_live_message_does_not_move_the_agent_window(before: CompanyData, tmp_path: Path) -> None:
    """Regression: a WhatsApp message dated today made October's enquiries fall out of the CRM."""
    erp = DemoErp(tmp_path / "erp.sqlite", clock=lambda: datetime(2026, 11, 24, 17, 0))
    enquiry = Enquiry(name="Mutua Beta (ficticia)", email=MUTUA_EMAIL, topic="Factura")
    register_enquiry(erp, enquiry, AuditLog())
    live = erp.list_opportunities()
    contacts = {o.contact_id: c for o in live if (c := erp.contact(o.contact_id))}
    cards = build_cards(before, contacts=contacts, extra_opportunities=live)
    assert sum(c.unattended for c in cards) == sum(c.unattended for c in build_cards(before))
    mutua = next(c for c in cards if c.email == MUTUA_EMAIL)
    assert any("contéstale antes de reclamarle" in a for a in mutua.alerts)
