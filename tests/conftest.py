from pathlib import Path

import pytest

from vigia.data.loader import load_company_data
from vigia.data.model import CompanyData
from vigia.data.synthetic import AFTER, BEFORE, DEMO_ROOT

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def before() -> CompanyData:
    return load_company_data(ROOT / DEMO_ROOT / BEFORE)


@pytest.fixture
def after() -> CompanyData:
    return load_company_data(ROOT / DEMO_ROOT / AFTER)
