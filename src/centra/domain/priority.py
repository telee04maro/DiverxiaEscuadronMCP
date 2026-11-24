"""Deterministic prioritisation: impact × urgency ÷ effort, and the 7/30/90-day horizon."""

from decimal import ROUND_HALF_UP, Decimal
from enum import IntEnum

from centra.domain.findings import Finding


class Horizon(IntEnum):
    WEEK = 7
    MONTH = 30
    QUARTER = 90


HORIZON_LABELS: dict[Horizon, str] = {
    Horizon.WEEK: "Esta semana (7 días)",
    Horizon.MONTH: "Este mes (30 días)",
    Horizon.QUARTER: "Este trimestre (90 días)",
}

_URGENT = 4
_QUICK = 2
_HEAVY = 4


def score(finding: Finding) -> Decimal:
    raw = Decimal(finding.impact * finding.urgency) / Decimal(finding.effort)
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def horizon_for(*, urgency: int, effort: int) -> Horizon:
    """Urgent and quick → this week; heavy → this quarter; everything else → this month."""
    if urgency >= _URGENT and effort <= _QUICK:
        return Horizon.WEEK
    if effort >= _HEAVY:
        return Horizon.QUARTER
    return Horizon.MONTH
