from decimal import Decimal

import pytest

from vigia.domain.money import MoneyError, eur, fmt_eur, pct_change


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1234.56", Decimal("1234.56")),
        ("1.234,56", Decimal("1234.56")),
        ("1.234,56 €", Decimal("1234.56")),
        ("-0,01", Decimal("-0.01")),
        (12, Decimal("12.00")),
        (Decimal("3.005"), Decimal("3.01")),
    ],
)
def test_eur_parses_spanish_and_plain_amounts(raw: str | int | Decimal, expected: Decimal) -> None:
    assert eur(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "NaN", "Infinity"])
def test_eur_rejects_non_amounts(raw: str) -> None:
    with pytest.raises(MoneyError):
        eur(raw)


def test_fmt_eur_uses_spanish_format() -> None:
    assert fmt_eur(Decimal("9312.4")) == "9.312,40 €"
    assert fmt_eur(Decimal("-0.01")) == "-0,01 €"


def test_pct_change_is_none_without_baseline() -> None:
    assert pct_change(Decimal(0), Decimal(10)) is None
    assert pct_change(Decimal(400), Decimal(328)) == Decimal("-18.0")
