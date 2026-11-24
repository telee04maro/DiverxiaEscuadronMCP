"""Settings from the environment (.env). Secrets never have defaults and are never logged."""

import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, SecretStr

# USD per million tokens (input, output). Source: Anthropic model table, 2026-11.
PRICES_PER_MTOK: dict[str, tuple[Decimal, Decimal]] = {
    "claude-opus-5-5": (Decimal("4.00"), Decimal("20.00")),
    "claude-sonnet-5-5": (Decimal("2.00"), Decimal("10.00")),
    "claude-haiku-5-5": (Decimal("0.10"), Decimal("0.50")),
}


class SmtpSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str
    port: int
    user: str
    password: SecretStr
    sender: str


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    main_model: str = "claude-opus-5-5"
    fast_model: str = "claude-haiku-5-5"
    ai_budget_usd: Decimal = Decimal("0.50")
    use_ai: bool = True
    outbox_dir: Path = Path("outbox")
    demo_recipient: str | None = None
    smtp: SmtpSettings | None = None
    late_interest_rate_pct: Decimal | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        env = os.environ
        smtp = None
        if env.get("SMTP_HOST") and env.get("SMTP_USER") and env.get("SMTP_PASSWORD"):
            smtp = SmtpSettings(
                host=env["SMTP_HOST"],
                port=int(env.get("SMTP_PORT", "587")),
                user=env["SMTP_USER"],
                password=SecretStr(env["SMTP_PASSWORD"]),
                sender=env.get("SMTP_FROM", env["SMTP_USER"]),
            )
        rate = env.get("LATE_INTEREST_RATE_PCT")
        return cls(
            main_model=env.get("VIGIA_MAIN_MODEL", "claude-opus-5-5"),
            fast_model=env.get("VIGIA_FAST_MODEL", "claude-haiku-5-5"),
            ai_budget_usd=Decimal(env.get("AI_BUDGET_USD", "0.50")),
            use_ai=env.get("VIGIA_USE_AI", "1") != "0",
            outbox_dir=Path(env.get("VIGIA_OUTBOX", "outbox")),
            demo_recipient=env.get("DEMO_RECIPIENT") or None,
            smtp=smtp,
            late_interest_rate_pct=Decimal(rate) if rate else None,
        )
