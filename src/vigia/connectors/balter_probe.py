"""Read-only check of a BALTER integration key: authentication and permission, no personal data.

The BALTER API v1 offers contact lookup (returns names), opportunity creation (writes) and the
article catalogue. Only the catalogue is free of personal data, so the check asks for one article
and reports the HTTP status and how many came back, never their content (ADR 006).

It refuses to run without ``--autorizado``: the company that owns the data must agree first.
"""

import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from dotenv import load_dotenv

TIMEOUT_S = 10
ENDPOINT = "articles.php"
MEANING = {
    200: "Clave válida y con permiso de lectura del catálogo (articles.read)",
    401: "Clave ausente, inválida, revocada o caducada",
    403: "La clave es válida, pero no tiene permiso articles.read",
    500: "Error interno de BALTER",
}
Opener = Callable[..., Any]


class _NoRedirect(HTTPRedirectHandler):
    """A redirect would resend the Authorization header to another place (R3-14)."""

    def redirect_request(self, *_: Any) -> None:  # noqa: ANN401
        return None


_OPEN = build_opener(_NoRedirect).open


class ProbeError(ValueError):
    """The configuration does not allow a safe check."""


@dataclass(frozen=True)
class ProbeResult:
    status: int | None
    articles: int | None
    message: str

    @property
    def ok(self) -> bool:
        # A 200 with an unexpected body (e.g. a login page) is not a working integration.
        return self.status == 200 and self.articles is not None  # noqa: PLR2004 - HTTP OK


def check_base_url(raw: str) -> str:
    """Only https with a host: the key travels in a header and must never go in clear text."""
    url = raw.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ProbeError("BALTER_URL tiene que ser una dirección https completa")
    return url if url.endswith("/") else url + "/"


def probe(base_url: str, key: str, opener: Opener = _OPEN) -> ProbeResult:
    if not key.strip():
        raise ProbeError("Falta BALTER_TOKEN en .env")
    request = Request(  # noqa: S310 - https checked in check_base_url
        urljoin(check_base_url(base_url), ENDPOINT),
        data=json.dumps({"action": "search", "limit": 1}).encode(),
        headers={"Authorization": f"Bearer {key.strip()}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener(request, timeout=TIMEOUT_S) as response:
            status, raw = response.status, response.read()
    except HTTPError as error:
        return ProbeResult(error.code, None, MEANING.get(error.code, "Respuesta inesperada"))
    except (URLError, TimeoutError):
        return ProbeResult(None, None, "No se pudo conectar con BALTER (red o tiempo agotado)")
    try:
        payload = json.loads(raw)
        articles = payload["data"]["articles"]
        if payload.get("status") != "success" or not isinstance(articles, list):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        return ProbeResult(status, None, "Respuesta con un formato distinto al documentado")
    return ProbeResult(status, len(articles), MEANING.get(status, "Respuesta inesperada"))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--autorizado" not in args:
        print(
            "No se ejecuta: hace falta el visto bueno de la empresa dueña de BALTER. "
            "Con él, repite con --autorizado (ver docs/integracion-balter.md)."
        )
        return 2
    load_dotenv()
    try:
        result = probe(os.environ.get("BALTER_URL", ""), os.environ.get("BALTER_TOKEN", ""))
    except ProbeError as error:
        print(f"No se ejecuta: {error}")
        return 2
    articles = "—" if result.articles is None else str(result.articles)
    print(f"HTTP {result.status or '—'} · artículos recibidos: {articles} · {result.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
