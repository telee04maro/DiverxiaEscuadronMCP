"""The interface agents use to ask a language model for structured output.

A ``None`` answer means "no answer you can trust": no key, budget spent, refusal or
an error. Every caller has a rule-based alternative for that case.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict


class Tier(StrEnum):
    """Which model a task needs: reasoning and writing, or bulk classification."""

    MAIN = "principal"
    FAST = "rápido"


class LlmCall(BaseModel):
    model_config = ConfigDict(frozen=True)

    task: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    ok: bool
    note: str = ""


class LanguageModel(Protocol):
    @property
    def mode(self) -> str:
        """Human-readable description of how the model is being used."""
        ...

    @property
    def calls(self) -> tuple[LlmCall, ...]: ...

    def structured[T: BaseModel](
        self, *, task: str, tier: Tier, system: str, prompt: str, schema: type[T]
    ) -> T | None: ...


class OfflineModel:
    """No language model: every caller falls back to its rules."""

    @property
    def mode(self) -> str:
        return "Sin IA: solo reglas (no hay clave de API o la IA está desactivada)"

    @property
    def calls(self) -> tuple[LlmCall, ...]:
        return ()

    def structured[T: BaseModel](
        self, *, task: str, tier: Tier, system: str, prompt: str, schema: type[T]
    ) -> T | None:
        return None


def total_cost(calls: tuple[LlmCall, ...]) -> Decimal:
    return sum((call.cost_usd for call in calls), Decimal(0))
