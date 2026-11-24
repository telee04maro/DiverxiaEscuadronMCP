"""The ERP/CRM connector contract: the five operations of the WhatsApp assistant plus one read.

Changing ERP (demo ERP, BALTER, Odoo, Holded…) means writing another implementation of
``CrmConnector``; the agents and the WhatsApp flow do not change.
"""

import re
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from vigia.audit import AuditLog, EventKind
from vigia.data.model import Opportunity, OpportunityStatus

AGENT = "Agente de atención y captación"
_PHONE = re.compile(r"^\+?\d{6,15}$")
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s]{2,}$")


DEFAULT_COUNTRY_CODE = "+34"
_NATIONAL_DIGITS = 9


def normalize_phone(raw: str | None) -> str | None:
    """International format, so "+34 600 000 001", "0034600000001" and "600000001" match."""
    if raw is None or not raw.strip():
        return None
    cleaned = re.sub(r"[\s().-]", "", raw)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if not cleaned.startswith("+") and len(cleaned) == _NATIONAL_DIGITS:
        cleaned = DEFAULT_COUNTRY_CODE + cleaned
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
    first_response_at: datetime | None = None


class Enquiry(BaseModel):
    """What the WhatsApp assistant collected in a conversation."""

    name: str = Field(min_length=1, max_length=120)
    phone: str | None = None
    email: str | None = None
    topic: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=2000)
    urgent: bool = False
    channel: str = Field(default="whatsapp", min_length=1, max_length=30)
    answered_at: datetime | None = None

    _phone = field_validator("phone")(normalize_phone)
    _email = field_validator("email")(normalize_email)

    @model_validator(mode="after")
    def _reachable(self) -> "Enquiry":
        if self.phone is None and self.email is None:
            raise ValueError("Hace falta teléfono o correo para no duplicar contactos")
        return self


class EnquiryOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact: Contact
    opportunity_id: str
    new_contact: bool
    new_opportunity: bool
    escalated: bool


class CrmConnector(Protocol):
    def find_contact(self, *, phone: str | None, email: str | None) -> Contact | None: ...

    def create_contact(self, contact: NewContact) -> Contact: ...

    def create_opportunity(self, opportunity: NewOpportunity) -> Opportunity: ...

    def add_note(self, opportunity_id: str, text: str) -> None: ...

    def mark_origin(self, opportunity_id: str, origin: str) -> None: ...

    def list_opportunities(self) -> tuple[Opportunity, ...]: ...


def register_enquiry(crm: CrmConnector, enquiry: Enquiry, log: AuditLog) -> EnquiryOutcome:
    """The assistant's flow: never duplicate a contact, never open a second open opportunity."""
    contact = crm.find_contact(phone=enquiry.phone, email=enquiry.email)
    new_contact = contact is None
    if contact is None:
        contact = crm.create_contact(
            NewContact(name=enquiry.name, phone=enquiry.phone, email=enquiry.email)
        )
        log.record(AGENT, EventKind.DID, "Contacto nuevo en el ERP", contact.id)
    open_one = next(
        (
            o
            for o in crm.list_opportunities()
            if o.contact_id == contact.id and o.status is OpportunityStatus.OPEN
        ),
        None,
    )
    if open_one is not None:
        crm.add_note(open_one.id, f"{enquiry.topic}: {enquiry.summary}".strip(": "))
        log.record(
            AGENT,
            EventKind.DID,
            "Ya tenía una oportunidad abierta: se añade como nota",
            open_one.id,
        )
        opportunity_id, new_opportunity = open_one.id, False
    else:
        created = crm.create_opportunity(
            NewOpportunity(
                contact_id=contact.id,
                topic=enquiry.topic,
                summary=enquiry.summary,
                urgent=enquiry.urgent,
                channel=enquiry.channel,
                first_response_at=enquiry.answered_at,
            )
        )
        crm.mark_origin(created.id, enquiry.channel)
        log.record(AGENT, EventKind.DID, "Oportunidad nueva, sin responsable asignado", created.id)
        opportunity_id, new_opportunity = created.id, True
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
    )
