"""Load a company folder (CSV and JSON, the way pymes keep their data).

A missing file is not an error: it is recorded as a missing source so the specialists
can say what they could not see.
"""

import csv
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from centra.data.model import (
    BankMovement,
    Company,
    CompanyData,
    Competitor,
    CompetitorAd,
    Invoice,
    MonthlySessions,
    Review,
    SearchResult,
)
from centra.domain.money import eur

COMPANY_FILE = "empresa.json"
INVOICES_FILE = "facturas.csv"
BANK_FILE = "banco.csv"
SESSIONS_FILE = "sesiones.csv"
REVIEWS_FILE = "resenas.json"
ADS_FILE = "competencia/anuncios.json"
COMPETITORS_FILE = "competencia/competidores.json"
SEARCH_FILE = "competencia/busqueda.json"


class DataError(ValueError):
    """The company folder exists but a file is malformed."""


def load_company_data(folder: Path) -> CompanyData:
    if not (folder / COMPANY_FILE).is_file():
        raise DataError(f"Falta la ficha de la empresa ({COMPANY_FILE}) en {folder.name}")
    missing: list[str] = []
    company = Company.model_validate(_read_json(folder / COMPANY_FILE))
    return CompanyData(
        company=company,
        invoices=_load(folder, INVOICES_FILE, missing, _invoices),
        bank=_load(folder, BANK_FILE, missing, _bank),
        sessions=_load(folder, SESSIONS_FILE, missing, _sessions),
        reviews=_load(folder, REVIEWS_FILE, missing, _reviews),
        competitor_ads=_load(folder, ADS_FILE, missing, _ads),
        competitors=_load(folder, COMPETITORS_FILE, missing, _competitors),
        search_results=_load(folder, SEARCH_FILE, missing, _search),
        missing_sources=tuple(missing),
    )


def _load[T](
    folder: Path, name: str, missing: list[str], parse: Callable[[Path], tuple[T, ...]]
) -> tuple[T, ...]:
    path = folder / name
    if not path.is_file():
        missing.append(name)
        return ()
    try:
        return parse(path)
    except (KeyError, ValueError) as error:
        raise DataError(f"{name}: {error}") from error


def _read_json(path: Path) -> Any:  # noqa: ANN401 - raw JSON is validated right after
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _invoices(path: Path) -> tuple[Invoice, ...]:
    return tuple(
        Invoice.model_validate({**row, "amount": eur(row["amount"])}) for row in _rows(path)
    )


def _bank(path: Path) -> tuple[BankMovement, ...]:
    return tuple(
        BankMovement.model_validate(
            {**row, "amount": eur(row["amount"]), "balance": eur(row["balance"])}
        )
        for row in _rows(path)
    )


def _sessions(path: Path) -> tuple[MonthlySessions, ...]:
    return tuple(
        MonthlySessions.model_validate({**row, "revenue": eur(row["revenue"])})
        for row in _rows(path)
    )


def _reviews(path: Path) -> tuple[Review, ...]:
    return tuple(Review.model_validate(item) for item in _read_json(path))


def _ads(path: Path) -> tuple[CompetitorAd, ...]:
    return tuple(CompetitorAd.model_validate(item) for item in _read_json(path))


def _competitors(path: Path) -> tuple[Competitor, ...]:
    return tuple(Competitor.model_validate(item) for item in _read_json(path))


def _search(path: Path) -> tuple[SearchResult, ...]:
    return tuple(SearchResult.model_validate(item) for item in _read_json(path))
