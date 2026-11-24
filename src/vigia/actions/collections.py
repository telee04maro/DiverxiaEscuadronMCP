"""Collections: decide the tone, write the claim, verify it, send it, and never call it collected.

Claude writes the e-mail; the rules check that every invoice, every amount and the total are
in the text and that no other amount was invented. If the check fails, a fixed template is used.
"""

import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from email.message import EmailMessage
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from vigia.actions.mailer import Mailer
from vigia.audit import AuditLog, EventKind
from vigia.data.model import Company
from vigia.domain.money import MoneyError, eur, fmt_eur, money_mentions
from vigia.finance.reconciliation import InvoiceStatus
from vigia.llm.base import LanguageModel, Tier
from vigia.specialists.finance import NAME as FINANCE

DEMO_SENDER = "administracion@vigia-demo.example"
FRIENDLY_MAX_DAYS = 15
FIRM_MAX_DAYS = 60
_BARE_DECIMAL = re.compile(r"\d+(?:[.,]\d{3})*[.,]\d{2}(?!\d)")
# A friendly reminder goes out without approval, so it may not threaten or sound formal.
_NOT_FRIENDLY = re.compile(
    r"requer|formal|judicial|abogad|demanda|asnef|moros|embarg|recargo|intereses|"
    r"procedimiento|reclamaci[oó]n legal|últim[oa] aviso",
    re.IGNORECASE,
)
MAX_SUBJECT = 120
DISCLOSURE = (
    "Este mensaje lo ha redactado Vigía, el asistente de IA de {company}, en su nombre. "
    "Si ya ha realizado el pago, por favor ignórelo y disculpe las molestias."
)


class Tone(StrEnum):
    FRIENDLY = "amable"
    FIRM = "firme"
    FORMAL = "formal"


class Origin(StrEnum):
    AI = "redactado por IA y verificado"
    TEMPLATE = "plantilla"


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    client_id: str
    client_name: str
    to: str
    tone: Tone
    subject: str
    body: str
    invoice_ids: tuple[str, ...]
    total: Decimal
    origin: Origin
    needs_approval: bool


class SentClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim: Claim
    delivery: str


class EmailDraft(BaseModel):
    subject: str = Field(description="Asunto breve")
    body: str = Field(description="Cuerpo del correo en español, sin firma ni aviso final")


def tone_for(days_overdue: int) -> Tone:
    if days_overdue <= FRIENDLY_MAX_DAYS:
        return Tone.FRIENDLY
    if days_overdue <= FIRM_MAX_DAYS:
        return Tone.FIRM
    return Tone.FORMAL


def late_interest(item: InvoiceStatus, today: date, rate_pct: Decimal | None) -> Decimal | None:
    """Simple late-payment interest, only if the legal rate was configured (never guessed)."""
    if rate_pct is None:
        return None
    days = item.days_overdue(today)
    raw = item.outstanding * rate_pct / 100 * days / 365
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def prepare_claim(
    company: Company,
    items: list[InvoiceStatus],
    model: LanguageModel,
    log: AuditLog,
    *,
    today: date,
    interest_rate_pct: Decimal | None = None,
) -> Claim:
    first = items[0].invoice
    worst = max(i.days_overdue(today) for i in items)
    tone = tone_for(worst)
    total = sum((i.outstanding for i in items), Decimal(0))
    interests = {i.invoice.id: late_interest(i, today, interest_rate_pct) for i in items}
    allowed = (
        {i.outstanding for i in items} | {total} | {v for v in interests.values() if v is not None}
    )
    facts = _facts(items, today, interests)
    draft = model.structured(
        task=f"Redactar reclamación ({tone.value}) a {first.client_name}",
        tier=Tier.MAIN,
        system=(
            f"Redactas reclamaciones de cobro para {company.name}, una {company.sector.lower()}. "
            f"Tono {tone.value}: amable si es un despiste reciente, firme si se repite, formal "
            "si hay que dejar constancia. Cita cada factura con su número e importe exacto y el "
            "total pendiente. No añadas importes, fechas ni amenazas que no estén en los datos."
        ),
        prompt=f"Cliente: {first.client_name}\nDatos:\n{facts}\nTotal pendiente: {fmt_eur(total)}",
        schema=EmailDraft,
    )
    origin = Origin.TEMPLATE
    subject, body = _template(
        company, items=items, tone=tone, total=total, today=today, interests=interests
    )
    if draft is not None:
        problem = _check(draft, items=items, total=total, allowed=allowed, tone=tone)
        if problem is None:
            origin, subject, body = Origin.AI, _clean_subject(draft.subject), draft.body
        else:
            log.record(FINANCE, EventKind.REJECTED, f"Borrador de la IA descartado: {problem}")
    body = f"{body.rstrip()}\n\n—\n{DISCLOSURE.format(company=company.name)}"
    log.record(
        FINANCE,
        EventKind.DECIDED,
        f"Tono {tone.value} para {first.client_name} (la factura más antigua lleva {worst} días)",
        *(i.invoice.id for i in items),
    )
    return Claim(
        client_id=first.client_id,
        client_name=first.client_name,
        to=first.contact_email,
        tone=tone,
        subject=subject,
        body=body,
        invoice_ids=tuple(i.invoice.id for i in items),
        total=total,
        origin=origin,
        needs_approval=tone is not Tone.FRIENDLY,
    )


def send_claim(claim: Claim, company: Company, mailer: Mailer, log: AuditLog) -> SentClaim:
    message = EmailMessage()
    message["Subject"] = claim.subject
    message["To"] = claim.to
    message["From"] = f"{company.name} <{DEMO_SENDER}>"
    message.set_content(claim.body)
    delivery = mailer.send(message)
    log.record(
        FINANCE,
        EventKind.DID,
        f"Reclamación {claim.tone.value} enviada a {claim.client_name}. {delivery}",
        *claim.invoice_ids,
    )
    log.record(
        FINANCE,
        EventKind.CHECKED,
        "Enviar no es cobrar: las facturas siguen pendientes hasta que el banco lo confirme",
        *claim.invoice_ids,
    )
    return SentClaim(claim=claim, delivery=delivery)


def _facts(items: list[InvoiceStatus], today: date, interests: dict[str, Decimal | None]) -> str:
    lines = []
    for item in items:
        line = (
            f"- Factura {item.invoice.id}, emitida el {item.invoice.issued:%d/%m/%Y}, vencida el "
            f"{item.invoice.due:%d/%m/%Y} ({item.days_overdue(today)} días): pendiente "
            f"{fmt_eur(item.outstanding)}"
        )
        interest = interests.get(item.invoice.id)
        if interest is not None:
            line += f"; intereses de demora: {fmt_eur(interest)}"
        lines.append(line)
    return "\n".join(lines)


def _clean_subject(subject: str) -> str:
    """One line, bounded length: a header with a line break would break the e-mail."""
    return " ".join(subject.split())[:MAX_SUBJECT]


def _check(
    draft: EmailDraft,
    *,
    items: list[InvoiceStatus],
    total: Decimal,
    allowed: set[Decimal],
    tone: Tone,
) -> str | None:
    """Why the model's e-mail cannot be sent as written, or None if it passes every check."""
    return (
        _missing_facts(draft.body, items, total)
        or _invented_amounts(draft.subject, allowed)
        or _invented_amounts(draft.body, allowed)
        or _wrong_tone(f"{draft.subject} {draft.body}", tone)
    )


def _missing_facts(body: str, items: list[InvoiceStatus], total: Decimal) -> str | None:
    for item in items:
        if item.invoice.id not in body:
            return f"falta la factura {item.invoice.id}"
        if fmt_eur(item.outstanding) not in body:
            return f"falta el importe {fmt_eur(item.outstanding)}"
    if len(items) > 1 and fmt_eur(total) not in body:
        return f"falta el total {fmt_eur(total)}"
    return None


def _invented_amounts(text: str, allowed: set[Decimal]) -> str | None:
    mentioned = money_mentions(text)
    if mentioned is None:
        return "incluye un importe ilegible"
    for raw in _BARE_DECIMAL.findall(text):
        try:
            mentioned.add(eur(raw))
        except MoneyError:
            return f"importe ilegible «{raw}»"
    invented = mentioned - allowed
    if invented:
        return f"incluye importes que no están en los datos ({', '.join(map(fmt_eur, invented))})"
    return None


def _wrong_tone(text: str, tone: Tone) -> str | None:
    if tone is Tone.FRIENDLY and _NOT_FRIENDLY.search(text):
        return "un recordatorio amable no puede sonar formal ni amenazar"
    return None


def _template(
    company: Company,
    *,
    items: list[InvoiceStatus],
    tone: Tone,
    total: Decimal,
    today: date,
    interests: dict[str, Decimal | None],
) -> tuple[str, str]:
    name = items[0].invoice.client_name
    opening = {
        Tone.FRIENDLY: "Le escribimos por si se ha pasado por alto el siguiente pago:",
        Tone.FIRM: "Seguimos sin recibir el pago de las siguientes facturas, ya vencidas:",
        Tone.FORMAL: (
            "Por la presente les requerimos formalmente el pago de las siguientes facturas, "
            "vencidas y no abonadas:"
        ),
    }[tone]
    closing = {
        Tone.FRIENDLY: "¿Podrían confirmarnos la fecha prevista de pago? Muchas gracias.",
        Tone.FIRM: "Les rogamos que paguen en los próximos 7 días o nos indiquen la fecha.",
        Tone.FORMAL: (
            "Les rogamos el abono en un plazo de 10 días. Nos reservamos el derecho a reclamar los "
            "intereses de demora previstos en la Ley 3/2004 de lucha contra la morosidad."
        ),
    }[tone]
    subject = {
        Tone.FRIENDLY: "Recordatorio de pago",
        Tone.FIRM: "Facturas vencidas pendientes de pago",
        Tone.FORMAL: "Requerimiento de pago de facturas vencidas",
    }[tone]
    body = (
        f"Estimados señores de {name}:\n\n{opening}\n\n"
        f"{_facts(items, today, interests)}\n\nTotal pendiente: {fmt_eur(total)}\n\n"
        f"{closing}\n\nAtentamente,\nAdministración de {company.name}"
    )
    return f"{subject} — {company.name}", body
