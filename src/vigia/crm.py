"""Vigía's CRM: one card per customer, built from what each agent knows (ADR 007).

Nobody keeps a separate customer list. Finance contributes invoices and debts, the customer
service agent contributes enquiries and the actions contribute the claims. The pieces are
joined by e-mail or phone, so the same company or person is one card, not three. Two pieces
that share an e-mail or phone but carry different names are joined and flagged for review.
"""

import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from vigia.actions.collections import Claim
from vigia.connectors.base import Contact, normalize_email, normalize_phone
from vigia.data.model import CompanyData, Opportunity, OpportunityStatus
from vigia.domain.money import fmt_eur
from vigia.finance.reconciliation import InvoiceStatus, reconcile
from vigia.specialists.customers import UNASSIGNED_AFTER, WINDOW_DAYS

FINANCE = "Finanzas"
CUSTOMERS = "Atención y captación"
ACTIONS = "Acciones"


class CustomerCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    name: str
    kind: str
    email: str | None = None
    phone: str | None = None
    overdue: Decimal | None = None  # None: finance does not bill this customer (unknown, not 0)
    oldest_overdue_days: int | None = None
    days_to_pay: int | None = None
    invoices: int = 0
    enquiries: int = 0
    unattended: int = 0  # same rule as the customer service agent (last 30 days, > 48 h)
    lost: int = 0
    last_enquiry: datetime | None = None
    agents: tuple[str, ...] = ()
    facts: tuple[tuple[str, str], ...] = ()  # (agent, what it knows)
    alerts: tuple[str, ...] = ()
    conflict: str | None = None

    @property
    def crossed(self) -> bool:
        """More than one agent knows this customer: the card shows what no agent sees alone."""
        return len(self.agents) > 1


@dataclass
class _Piece:
    agent: str
    ids: set[str]
    name: str | None
    kind: str
    email: str | None = None
    phone: str | None = None
    statuses: list[InvoiceStatus] = field(default_factory=list)
    opportunities: list[Opportunity] = field(default_factory=list)
    claims: list[tuple[Claim, bool]] = field(default_factory=list)  # (claim, already sent)


def build_cards(
    data: CompanyData,
    *,
    contacts: Mapping[str, Contact] | None = None,
    extra_opportunities: Iterable[Opportunity] = (),
    sent: Iterable[Claim] = (),
    pending: Iterable[Claim] = (),
) -> tuple[CustomerCard, ...]:
    """Cards ordered by what needs attention first: crossed alerts, then debt, then the rest."""
    today = data.company.analysis_date
    statuses = reconcile(data.invoices, data.bank, as_of=today)
    opportunities = _unique(data.opportunities, extra_opportunities)
    pieces = [
        *_finance_pieces(statuses),
        *_customer_pieces(opportunities, contacts or {}),
        *_claim_pieces(sent, sent=True),
        *_claim_pieces(pending, sent=False),
    ]
    # The analysis moment, as the customer service agent uses: a message that arrives later
    # (live, by WhatsApp) is open but not "unattended for 48 h", and does not move the window.
    now = datetime.combine(today + timedelta(days=1), time(0))
    cards = [_card(group, today, now) for group in _merge(pieces)]
    return tuple(
        sorted(
            cards,
            key=lambda c: (
                not (c.crossed and c.alerts),
                not c.alerts,
                -(c.overdue or Decimal(0)),
                c.name.casefold(),
            ),
        )
    )


def _unique(*groups: Iterable[Opportunity]) -> tuple[Opportunity, ...]:
    seen: dict[str, Opportunity] = {}
    for group in groups:
        for opportunity in group:
            seen.setdefault(opportunity.id, opportunity)
    return tuple(seen.values())


def _safe(normalize: object, raw: str | None) -> str | None:
    try:
        return normalize(raw)  # type: ignore[operator, no-any-return]
    except ValueError:
        return None


def _ids(local: str, email: str | None, phone: str | None) -> set[str]:
    ids = {local}
    if email:
        ids.add(f"email:{email}")
    if phone:
        ids.add(f"phone:{phone}")
    return ids


def _finance_pieces(statuses: tuple[InvoiceStatus, ...]) -> list[_Piece]:
    by_client: dict[str, list[InvoiceStatus]] = defaultdict(list)
    for status in statuses:
        by_client[status.invoice.client_id].append(status)
    pieces = []
    for client_id, group in by_client.items():
        invoice = group[0].invoice
        email = _safe(normalize_email, invoice.contact_email)
        pieces.append(
            _Piece(
                agent=FINANCE,
                ids=_ids(f"client:{client_id}", email, None),
                name=invoice.client_name,
                kind=invoice.client_type.value,
                email=email,
                statuses=group,
            )
        )
    return pieces


def _customer_pieces(
    opportunities: tuple[Opportunity, ...], contacts: Mapping[str, Contact]
) -> list[_Piece]:
    by_contact: dict[str, list[Opportunity]] = defaultdict(list)
    for opportunity in opportunities:
        by_contact[opportunity.contact_id].append(opportunity)
    pieces = []
    for contact_id, group in by_contact.items():
        contact = contacts.get(contact_id)
        email = _safe(normalize_email, contact.email) if contact else None
        phone = _safe(normalize_phone, contact.phone) if contact else None
        pieces.append(
            _Piece(
                agent=CUSTOMERS,
                ids=_ids(f"contact:{contact_id}", email, phone),
                name=contact.name if contact else None,
                kind="contacto",
                email=email,
                phone=phone,
                opportunities=group,
            )
        )
    return pieces


def _claim_pieces(claims: Iterable[Claim], *, sent: bool) -> list[_Piece]:
    pieces = []
    for claim in claims:
        email = _safe(normalize_email, claim.to)
        pieces.append(
            _Piece(
                agent=ACTIONS,
                ids=_ids(f"client:{claim.client_id}", email, None),
                name=claim.client_name,
                kind="cliente",
                email=email,
                claims=[(claim, sent)],
            )
        )
    return pieces


def _merge(pieces: list[_Piece]) -> list[list[_Piece]]:
    """Union-find over identifiers: pieces sharing an e-mail, phone or id are one customer."""
    parent = list(range(len(pieces)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict[str, int] = {}
    for index, piece in enumerate(pieces):
        for identifier in piece.ids:
            if identifier in owner:
                parent[root(index)] = root(owner[identifier])
            else:
                owner[identifier] = index
    groups: dict[int, list[_Piece]] = defaultdict(list)
    for index, piece in enumerate(pieces):
        groups[root(index)].append(piece)
    return list(groups.values())


def _plain(name: str) -> str:
    text = re.sub(r"\(fictici[ao]\)", "", name, flags=re.IGNORECASE)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _card(group: list[_Piece], today: date, now: datetime) -> CustomerCard:
    agents = tuple(dict.fromkeys(p.agent for p in group))
    names = [p.name for p in group if p.name]
    distinct = list(dict.fromkeys(names, None))
    conflict = None
    if len({_plain(n) for n in distinct}) > 1:
        conflict = (
            f"El mismo correo o teléfono aparece con nombres distintos: {' / '.join(distinct)}"
        )
    first = next((p for p in group if p.agent == FINANCE), group[0])
    statuses = [s for p in group for s in p.statuses]
    opportunities = [o for p in group for o in p.opportunities]
    claims = [c for p in group for c in p.claims]
    key = sorted(i for p in group for i in p.ids)[0]
    contact_ids = sorted({o.contact_id for o in opportunities})
    name = first.name or (f"Contacto {contact_ids[0]}" if contact_ids else key)
    finance = _finance_view(statuses, today) if statuses else None
    attended = _enquiry_view(opportunities, now)
    facts = [*(_finance_fact(statuses, finance) if finance else []), *attended.facts]
    facts += [(ACTIONS, _claim_fact(claim, sent)) for claim, sent in claims]
    alerts = _alerts(finance, attended, claims)
    return CustomerCard(
        key=key,
        name=name,
        kind=first.kind,
        email=next((p.email for p in group if p.email), None),
        phone=next((p.phone for p in group if p.phone), None),
        overdue=finance.overdue if finance else None,
        oldest_overdue_days=finance.oldest if finance else None,
        days_to_pay=finance.days_to_pay if finance else None,
        invoices=len(statuses),
        enquiries=len(opportunities),
        unattended=attended.unattended,
        lost=attended.lost,
        last_enquiry=attended.last,
        agents=agents,
        facts=tuple(facts),
        alerts=alerts,
        conflict=conflict,
    )


@dataclass(frozen=True)
class _FinanceView:
    billed: Decimal
    overdue: Decimal
    oldest: int | None
    days_to_pay: int | None


def _finance_view(statuses: list[InvoiceStatus], today: date) -> _FinanceView:
    late = [s for s in statuses if s.outstanding > 0 and s.days_overdue(today) > 0]
    days = [d for s in statuses if (d := s.days_to_pay()) is not None]
    return _FinanceView(
        billed=sum((s.invoice.amount for s in statuses), Decimal(0)),
        overdue=sum((s.outstanding for s in late), Decimal(0)),
        oldest=max((s.days_overdue(today) for s in late), default=None),
        days_to_pay=round(sum(days) / len(days)) if days else None,
    )


def _finance_fact(statuses: list[InvoiceStatus], view: _FinanceView) -> list[tuple[str, str]]:
    pays = f"; paga de media a {view.days_to_pay} días" if view.days_to_pay is not None else ""
    text = f"{_n(len(statuses), 'factura')} por {fmt_eur(view.billed)}{pays}"
    if view.overdue > 0:
        text += f"; {fmt_eur(view.overdue)} vencidos"
    return [(FINANCE, text)]


@dataclass(frozen=True)
class _EnquiryView:
    unattended: int
    open_unassigned: int
    lost: int
    last: datetime | None
    facts: list[tuple[str, str]]


def _enquiry_view(opportunities: list[Opportunity], now: datetime) -> _EnquiryView:
    if not opportunities:
        return _EnquiryView(0, 0, 0, None, [])
    # The customer service agent's own rule, so the CRM and its KPI never disagree.
    unattended = [
        o
        for o in opportunities
        if o.status is OpportunityStatus.OPEN
        and o.assigned_to is None
        and now - timedelta(days=WINDOW_DAYS) <= o.created_at
        and now - o.created_at > UNASSIGNED_AFTER
    ]
    open_now = [
        o for o in opportunities if o.status is OpportunityStatus.OPEN and o.assigned_to is None
    ]
    lost = [o for o in opportunities if o.status is OpportunityStatus.LOST]
    last = max(o.created_at for o in opportunities)
    channels = ", ".join(sorted({o.channel for o in opportunities}))
    text = f"{_n(len(opportunities), 'consulta')} ({channels}); la última, el {last:%d/%m}"
    if open_now:
        text += f"; {_n(len(open_now), 'abierta')} sin responsable"
    if lost:
        text += f"; {_n(len(lost), 'perdida')}"
    return _EnquiryView(len(unattended), len(open_now), len(lost), last, [(CUSTOMERS, text)])


def _claim_fact(claim: Claim, sent: bool) -> str:
    state = "enviada" if sent else "preparada, espera aprobación"
    return f"Reclamación {claim.tone.value} {state}: {fmt_eur(claim.total)}"


def _alerts(
    finance: _FinanceView | None, enquiries: _EnquiryView, claims: list[tuple[Claim, bool]]
) -> tuple[str, ...]:
    alerts: list[str] = []
    owes = finance is not None and finance.overdue > 0
    if owes and enquiries.open_unassigned:
        alerts.append(
            "Debe dinero y tiene una consulta sin responsable: contéstale antes de reclamarle"
        )
    if finance is not None and owes:
        alerts.append(
            f"Debe {fmt_eur(finance.overdue)} vencidos; la factura más antigua, hace "
            f"{finance.oldest} días"
        )
    if any(not sent for _, sent in claims):
        alerts.append("Hay una reclamación preparada que espera tu aprobación")
    if enquiries.unattended:
        alerts.append(
            f"{_n(enquiries.unattended, 'consulta')} sin responsable desde hace más de 48 h"
        )
    return tuple(alerts)


def _n(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"
