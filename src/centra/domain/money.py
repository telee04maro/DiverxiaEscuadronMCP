"""Money helpers. Money is always Decimal with two decimals; floats never touch it."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")


class MoneyError(ValueError):
    """Raised when a value cannot be read as an amount of money."""


def eur(value: str | int | Decimal) -> Decimal:
    """Parse an amount ("1234.56", "1.234,56", 12, Decimal) into a two-decimal Decimal."""
    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, int):
        amount = Decimal(value)
    else:
        amount = _parse_text(value)
    if not amount.is_finite():
        raise MoneyError(f"Importe no finito: {value!r}")
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _parse_text(text: str) -> Decimal:
    cleaned = text.strip().replace("€", "").replace(" ", "")
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as error:
        raise MoneyError(f"No es un importe: {text!r}") from error


def fmt_eur(amount: Decimal) -> str:
    """Format as Spanish euros: 1.234,56 €."""
    quantized = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    sign = "-" if quantized < 0 else ""
    integer, decimals = f"{abs(quantized):.2f}".split(".")
    grouped = f"{int(integer):,}".replace(",", ".")
    return f"{sign}{grouped},{decimals} €"


def pct_change(before: Decimal, after: Decimal) -> Decimal | None:
    """Percentage change from before to after, or None when before is zero."""
    if before == 0:
        return None
    return ((after - before) / before * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def fmt_num(value: Decimal) -> str:
    """Spanish decimal comma: 15.4 -> "15,4"."""
    return str(value).replace(".", ",")
