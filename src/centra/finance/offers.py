"""Can the company afford a cheaper first visit? Finance validates what competition proposes."""

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict

from centra.data.model import Company
from centra.domain.money import fmt_eur

# A first-visit discount may cost at most this share of what a new patient normally leaves.
MAX_PATIENT_MARGIN_LOSS = Decimal("0.15")


class OfferCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    price: Decimal
    viable: bool
    reason: str
    first_visit_margin: Decimal | None = None
    patient_margin: Decimal | None = None
    normal_patient_margin: Decimal | None = None


def check_first_visit_offer(company: Company, price: Decimal) -> OfferCheck:
    service = company.service(company.main_service)
    if service is None:
        return OfferCheck(price=price, viable=False, reason="No conozco el coste del servicio")
    sessions = company.avg_sessions_per_new_patient
    if sessions is None or sessions < 1:
        return OfferCheck(
            price=price,
            viable=False,
            reason="Falta cuántas sesiones hace de media un paciente nuevo: no puedo validarlo",
        )
    unit_margin = service.price - service.direct_cost
    first_margin = price - service.direct_cost
    normal = (unit_margin * sessions).quantize(Decimal("0.01"))
    with_offer = (first_margin + unit_margin * (sessions - 1)).quantize(Decimal("0.01"))
    loss = (normal - with_offer) / normal if normal > 0 else Decimal(1)
    viable = loss <= MAX_PATIENT_MARGIN_LOSS
    loss_pct = (loss * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    verdict = "asumible" if viable else "no compensa"
    reason = (
        f"Primera visita a {fmt_eur(price)}: el paciente medio deja {fmt_eur(with_offer)} "
        f"en lugar de {fmt_eur(normal)} ({loss_pct} % menos): {verdict}"
    )
    return OfferCheck(
        price=price,
        viable=viable,
        reason=reason,
        first_visit_margin=first_margin,
        patient_margin=with_offer,
        normal_patient_margin=normal,
    )
