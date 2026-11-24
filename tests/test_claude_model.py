"""The real-AI path without the network: invalid output, spending cap and cost (fake client)."""

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from vigia.config import Settings
from vigia.llm.base import Tier
from vigia.llm.claude import ClaudeModel


class Verdict(BaseModel):
    impact: int = Field(ge=1, le=5)


class FakeMessages:
    def __init__(self, result: Any) -> None:
        self.result = result
        self.calls = 0

    def parse(self, **_: Any) -> Any:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _model(result: Any, budget: str = "0.50", main: str = "claude-opus-5-5") -> ClaudeModel:
    client = SimpleNamespace(messages=FakeMessages(result))
    settings = Settings(ai_budget_usd=Decimal(budget), main_model=main)
    return ClaudeModel(settings, client=client)  # type: ignore[arg-type]


def _ask(model: ClaudeModel) -> Verdict | None:
    return model.structured(task="t", tier=Tier.MAIN, system="s", prompt="p", schema=Verdict)


def _response(tokens_in: int, tokens_out: int) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=tokens_in, output_tokens=tokens_out),
        stop_reason="end_turn",
        parsed_output=Verdict(impact=3),
    )


def test_output_outside_the_schema_falls_back_to_rules() -> None:
    try:
        Verdict.model_validate({"impact": 9})
    except ValidationError as error:
        broken = error
    model = _model(broken)
    assert _ask(model) is None
    [call] = model.calls
    assert not call.ok and "esquema" in call.note


def test_cost_is_measured_and_the_cap_stops_calls() -> None:
    model = _model(_response(100_000, 20_000), budget="0.50")
    assert _ask(model) == Verdict(impact=3)
    assert model.calls[0].cost_usd == Decimal("0.80")  # 0.1 M x 4 $ + 0.02 M x 20 $
    assert _ask(model) is None  # over the cap: no second paid call
    assert "Tope" in model.calls[-1].note


def test_unknown_model_is_never_free() -> None:
    model = _model(_response(1_000_000, 0), main="claude-modelo-nuevo")
    _ask(model)
    assert model.calls[0].cost_usd > 0
