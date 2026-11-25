""".env.example is committed: it never carries a secret (credentials go in .env, ignored by git)."""

from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / ".env.example"
SECRETS = (
    "ANTHROPIC_API_KEY",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "VIGIA_ERP_TOKEN",
    "ZERNIO_API_KEY",
    "HACK_NUMERO_DEMO",
    "BALTER_URL",
    "BALTER_USER",
    "BALTER_TOKEN",
)


def _values() -> dict[str, str]:
    pairs = (line.partition("=") for line in TEMPLATE.read_text(encoding="utf-8").splitlines())
    return {name.strip(): value.strip() for name, sep, value in pairs if sep and name[:1] != "#"}


def test_template_lists_every_secret() -> None:
    assert set(SECRETS) <= set(_values())


def test_template_has_no_secret_values() -> None:
    filled = [name for name in SECRETS if _values().get(name)]
    assert not filled, f"Mueve estos valores de .env.example a .env: {', '.join(filled)}"
