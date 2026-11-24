from decimal import Decimal

from vigia.audit import AuditLog, EventKind
from vigia.data.model import CompanyData
from vigia.domain.findings import Signal
from vigia.llm.base import LlmCall, OfflineModel, Tier
from vigia.specialists.competition import (
    AdReading,
    AdReadings,
    CompetitionSpecialist,
    ReviewTags,
)


class ScriptedModel:
    """Returns pre-written answers by schema, like a model that always responds."""

    def __init__(self, answers: dict[type, object]) -> None:
        self._answers = answers

    @property
    def mode(self) -> str:
        return "guion de prueba"

    @property
    def calls(self) -> tuple[LlmCall, ...]:
        return ()

    def structured(self, *, task, tier: Tier, system: str, prompt: str, schema):  # type: ignore[no-untyped-def]
        return self._answers.get(schema)


def test_rules_detect_offer_wait_complaints_price_and_visibility(before: CompanyData) -> None:
    report = CompetitionSpecialist().analyze(before, OfflineModel(), AuditLog())
    signals = {s for f in report.findings for s in f.signals}
    assert {
        Signal.COMPETITOR_OFFER,
        Signal.COMPETITOR_PROMISES_NO_WAIT,
        Signal.WAIT_COMPLAINTS,
        Signal.RATING_DROP,
        Signal.HIGHER_PRICE,
        Signal.LOW_SEARCH_VISIBILITY,
    } <= signals
    offer = next(f for f in report.findings if Signal.COMPETITOR_OFFER in f.signals)
    assert "20,00 €" in offer.title


def test_old_stopped_ads_are_ignored(before: CompanyData) -> None:
    report = CompetitionSpecialist().analyze(before, OfflineModel(), AuditLog())
    assert not any("175" in f.title for f in report.findings)


def test_model_price_not_in_ad_text_is_rejected(before: CompanyData) -> None:
    invented = AdReadings(
        ads=[AdReading(index=0, offer_price_eur="9", offer_service=None, promises_no_wait=True)]
    )
    log = AuditLog()
    report = CompetitionSpecialist().analyze(before, ScriptedModel({AdReadings: invented}), log)
    assert not any(Signal.COMPETITOR_OFFER in f.signals for f in report.findings)
    assert any(e.kind is EventKind.REJECTED for e in log.events)


def test_model_reading_of_real_price_is_accepted(before: CompanyData) -> None:
    reading = AdReadings(
        ads=[
            AdReading(
                index=0, offer_price_eur="20", offer_service="primera sesión", promises_no_wait=True
            )
        ]
    )
    report = CompetitionSpecialist().analyze(
        before, ScriptedModel({AdReadings: reading}), AuditLog()
    )
    assert any(Signal.COMPETITOR_OFFER in f.signals for f in report.findings)


def test_wait_share_kpi(before: CompanyData) -> None:
    report = CompetitionSpecialist().analyze(before, ScriptedModel({ReviewTags: None}), AuditLog())
    share = report.kpi("resenas_espera")
    assert share is not None and share.value is not None
    assert share.value >= Decimal(30)
