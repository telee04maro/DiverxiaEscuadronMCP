"""Is every fact the model wrote backed by our data? (red team R3-01 and R3-02)

The model may phrase, never add: a percentage, a number of days, an amount, a date, an IBAN,
a link or a phone number that is not in the data it was given is a reason to reject its text.
"""

import re
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

# 8.633,50 · 15,4 · 1.920 · 95 · 4.7 — any number a person would read as one.
_NUMBER = re.compile(r"(?<![\w])\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w])\d+(?:[.,]\d+)?")
_UNIT_AFTER = re.compile(r"^\s*(%|€|días|dias|h\b|horas|★|m\b|meses|semanas)", re.IGNORECASE)
_SMALL = Decimal(10)  # "2 de 3 facturas", "tres causas": small counts are not facts to check
_YEARS = range(2000, 2100)

IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b")
LINK = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|es|net|org|io|example)/", re.IGNORECASE)
PHONE = re.compile(r"(?<![\w])(?:\+|00)?\d(?:[ .-]?\d){8,}(?![\w])")
DATE = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b")


def _value(raw: str) -> Decimal | None:
    text = raw
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", text):
        text = text.replace(".", "")
    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def numbers_in(text: str) -> set[Decimal]:
    return {v for raw in _NUMBER.findall(text) if (v := _value(raw)) is not None}


def _unit(after: str) -> str | None:
    found = _UNIT_AFTER.match(after)
    if found is None:
        return None
    unit = found.group(1).lower()
    return {"dias": "días", "horas": "h"}.get(unit, unit)


def _figures(text: str) -> set[tuple[Decimal, str | None]]:
    """(value, unit) pairs: "45 días" is not "45 %"."""
    pairs = set()
    for match in _NUMBER.finditer(text):
        value = _value(match.group())
        if value is not None:
            pairs.add((value, _unit(text[match.end() :])))
    return pairs


def unsupported_numbers(
    text: str, sources: Iterable[str], extra: Iterable[Decimal] = ()
) -> list[str]:
    """Figures in ``text`` that the data does not hold, as written.

    A figure with a unit must appear with that unit (or bare) in ``sources``; ``extra`` are
    raw values (metrics) that back a figure in any unit.
    """
    clean = DATE.sub(" ", text)  # dates are checked on their own
    known = {pair for source in sources for pair in _figures(DATE.sub(" ", source))}
    bare = {value for value, unit in known if unit is None}
    raw = {Decimal(v).quantize(Decimal("0.01")) for v in extra}
    missing: list[str] = []
    for match in _NUMBER.finditer(clean):
        value = _value(match.group())
        if value is None:
            continue
        unit = _unit(clean[match.end() :])
        if (value, unit) in known or value in bare or value in raw:
            continue
        if unit is None and (value <= _SMALL or int(value) in _YEARS):
            continue
        missing.append(match.group())
    return missing


def unsupported_dates(text: str, allowed: Iterable[str]) -> list[str]:
    """Dates in ``text`` (dd/mm or dd/mm/yyyy) that are not among ``allowed``."""
    ok = set(allowed)
    return [d for d in DATE.findall(text) if d not in ok]
