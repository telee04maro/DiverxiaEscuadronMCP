"""The ERP/CRM connector contract: the five operations of the WhatsApp assistant plus one read.

Changing ERP (demo ERP, BALTER, Odoo, Holded…) means writing another implementation of
``CrmConnector``; the agents and the WhatsApp flow do not change.
"""

import re
import threading
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from vigia.audit import AuditLog, EventKind
from vigia.data.model import Opportunity, to_local_naive

AGENT = "Agente de atención y captación"
DEFAULT_COUNTRY_CODE = "+34"
_NATIONAL_DIGITS = 9
_PHONE = re.compile(r"^\+?[0-9]{6,15}$")  # ASCII digits only: "\d" accepts any script
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s]{2,}$")
# One enquiry at a time per process: find-then-create must not interleave.
_REGISTER_LOCK = threading.Lock()


def normalize_phone(raw: str | None) -> str | None:
    """International format: "+34 600 000 001", "0034600000001", "34600000001" (as WhatsApp
    sends it), "+34 (0) 600000001" and "600000001" are the same number."""
    if raw is None or not raw.strip():
        return None
    cleaned = raw.replace("(0)", "")
    cleaned = re.sub(r"[\s().-]", "", cleaned)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if not cleaned.startswith("+"):
        country = DEFAULT_COUNTRY_CODE.removeprefix("+")
        if len(cleaned) == _NATIONAL_DIGITS:
            cleaned = DEFAULT_COUNTRY_CODE + cleaned
        elif cleaned.startswith(country) and len(cleaned) == len(country) + _NATIONAL_DIGITS:
            cleaned = "+" + cleaned
    if not _PHONE.match(cleaned):
        raise ValueError("Teléfono no válido")
    return cleaned


def normalize_email(raw: str | None) -> str | None:
    if raw is None or not raw.strip():
        return None
    cleaned = raw.strip().lower()
    if not _EMAIL.match(cleaned):
        raise ValueError("Correo no válido")
    return cleaned


class Contact(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    phone: str | None = None
    email: str | None = None


class NewContact(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = None
    email: str | None = None

    _phone = field_validator("phone")(normalize_phone)
    _email = field_validator("email")(normalize_email)

    @model_validator(mode="after")
    def _reachable(self) -> "NewContact":
        if self.phone is None and self.email is None:
            raise ValueError("Hace falta teléfono o correo para no duplicar contactos")
        return self


class NewOpportunity(BaseModel):
    contact_id: str = Field(min_length=1, max_length=40)
    topic: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=2000)
    urgent: bool = False
    channel: str = Field(default="whatsapp", min_length=1, max_length=30)
    received_at: datetime | None = None
    first_response_at: datetime | None = None

    _times = field_validator("received_at", "first_response_at")(to_local_naive)

    @model_validator(mode="after")
    def _answered_after_received(self) -> "NewOpportunity":
        if (
            self.received_at
            and self.first_response_at
            and self.first_response_at < self.received_at
        ):
            raise ValueError("La respuesta no puede ser anterior a la recepción")
        return self


class Enquiry(BaseModel):
    """What the WhatsApp assistant collected in a conversation."""

    name: str = Field(min_length=1, max_length=120)
    phone: str | None = None
    email: str | None = None
    topic: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=2000)
    urgent: bool = False
    channel: str = Field(default="whatsapp", min_length=1, max_length=30)
    received_at: datetime | None = None
    answered_at: datetime | None = None

    _phone = field_validator("phone")(normalize_phone)
    _email = field_validator("email")(normalize_email)
    _times = field_validator("received_at", "answered_at")(to_local_naive)

    @model_validator(mode="after")
    def _consistent(self) -> "Enquiry":
        if self.phone is None and self.email is None:
            raise ValueError("Hace falta teléfono o correo para no duplicar contactos")
        if self.received_at and self.answered_at and self.answered_at < self.received_at:
            raise ValueError("La respuesta no puede ser anterior a la recepción")
        return self


class EnquiryOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact: Contact
    opportunity_id: str
    new_contact: bool
    new_opportunity: bool
    escalated: bool
    conflict: bool = False


class DuplicateOpenOpportunityError(Exception):
    """The contact already has an open opportunity (enforced by the ERP itself)."""


class CrmConnector(Protocol):
    def find_contact(self, *, phone: str | None, email: str | None) -> Contact | None: ...

    def create_contact(self, contact: NewContact) -> Contact: ...

    def create_opportunity(self, opportunity: NewOpportunity) -> Opportunity: ...

    def add_note(self, opportunity_id: str, text: str) -> None: ...

    def mark_origin(self, opportunity_id: str, origin: str) -> None: ...

    def list_opportunities(self) -> tuple[Opportunity, ...]: ...

    def open_opportunity(self, contact_id: str) -> Opportunity | None: ...


def _resolve_contact(
    crm: CrmConnector, enquiry: Enquiry, log: AuditLog
) -> tuple[Contact | None, bool]:
    """Phone wins; a phone and an e-mail belonging to different contacts is a conflict to review."""
    by_phone = crm.find_contact(phone=enquiry.phone, email=None) if enquiry.phone else None
    by_email = crm.find_contact(phone=None, email=enquiry.email) if enquiry.email else None
    conflict = by_phone is not None and by_email is not None and by_phone.id != by_email.id
    if conflict:
        log.record(
            AGENT,
            EventKind.ESCALATED,
            "El teléfono y el correo pertenecen a contactos distintos: revisar a mano",
            *(c.id for c in (by_phone, by_email) if c),
        )
    return by_phone or by_email, conflict


def _open_opportunity(crm: CrmConnector, contact_id: str) -> Opportunity | None:
    # A direct lookup: scanning every opportunity made each WhatsApp message O(n).
    return crm.open_opportunity(contact_id)


def register_enquiry(crm: CrmConnector, enquiry: Enquiry, log: AuditLog) -> EnquiryOutcome:
    """The assistant's flow: never duplicate a contact, never open a second open opportunity."""
    with _REGISTER_LOCK:
        contact, conflict = _resolve_contact(crm, enquiry, log)
        new_contact = contact is None
        if contact is None:
            contact = crm.create_contact(
                NewContact(name=enquiry.name, phone=enquiry.phone, email=enquiry.email)
            )
            log.record(AGENT, EventKind.DID, "Contacto nuevo en el ERP", contact.id)
        open_one = _open_opportunity(crm, contact.id)
        if open_one is None:
            try:
                created = crm.create_opportunity(
                    NewOpportunity(
                        contact_id=contact.id,
                        topic=enquiry.topic,
                        summary=enquiry.summary,
                        urgent=enquiry.urgent,
                        channel=enquiry.channel,
                        received_at=enquiry.received_at,
                        first_response_at=enquiry.answered_at,
                    )
                )
            except DuplicateOpenOpportunityError:
                open_one = _open_opportunity(crm, contact.id)
            else:
                crm.mark_origin(created.id, enquiry.channel)
                log.record(AGENT, EventKind.DID, "Oportunidad nueva, sin responsable", created.id)
                opportunity_id, new_opportunity = created.id, True
        if open_one is not None:
            crm.add_note(open_one.id, f"{enquiry.topic}: {enquiry.summary}".strip(": "))
            log.record(
                AGENT, EventKind.DID, "Ya tenía una oportunidad abierta: va como nota", open_one.id
            )
            opportunity_id, new_opportunity = open_one.id, False
    if enquiry.urgent:
        log.record(
            AGENT, EventKind.ESCALATED, "Consulta urgente: avisar al responsable", opportunity_id
        )
    return EnquiryOutcome(
        contact=contact,
        opportunity_id=opportunity_id,
        new_contact=new_contact,
        new_opportunity=new_opportunity,
        escalated=enquiry.urgent,
        conflict=conflict,
    )
