import shutil
from pathlib import Path

import pytest

from centra.data.loader import DataError, load_company_data
from centra.data.synthetic import AFTER, BEFORE, DEMO_ROOT

DEMO_BEFORE = Path(__file__).resolve().parents[1] / DEMO_ROOT / BEFORE
DEMO_AFTER = Path(__file__).resolve().parents[1] / DEMO_ROOT / AFTER


def test_demo_company_loads_completely() -> None:
    data = load_company_data(DEMO_BEFORE)
    assert data.company.employees == 15
    assert data.invoices and data.bank and data.sessions and data.reviews
    assert data.competitor_ads and data.competitors and data.search_results
    assert data.missing_sources == ()


def test_demo_uses_only_fictitious_parties() -> None:
    data = load_company_data(DEMO_AFTER)
    assert all(invoice.contact_email.endswith(".example") for invoice in data.invoices)
    assert all("ficticia" in competitor.name for competitor in data.competitors)


def test_missing_file_is_a_gap_not_an_error(tmp_path: Path) -> None:
    shutil.copytree(DEMO_BEFORE, tmp_path / "empresa")
    (tmp_path / "empresa" / "banco.csv").unlink()
    data = load_company_data(tmp_path / "empresa")
    assert data.bank == ()
    assert "banco.csv" in data.missing_sources


def test_missing_company_profile_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(DataError):
        load_company_data(tmp_path)
