"""The BALTER check never runs without authorisation, only reads the catalogue and leaks nothing."""

import json
from email.message import Message
from types import TracebackType
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from vigia.connectors.balter_probe import ProbeError, check_base_url, main, probe

KEY = "clave-de-prueba-123456"
BASE = "https://balter.example/api/v1/"


class FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status, self._body = status, body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: type[BaseException] | BaseException | TracebackType | None) -> None:
        return None


class FakeOpener:
    def __init__(self, outcome: FakeResponse | Exception) -> None:
        self.outcome = outcome
        self.requests: list[Request] = []

    def __call__(self, request: Request, timeout: float) -> FakeResponse:
        assert timeout > 0
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def _catalogue(*names: str) -> FakeResponse:
    articles: list[dict[str, Any]] = [{"id": i, "name": n} for i, n in enumerate(names, 1)]
    return FakeResponse(
        200, json.dumps({"status": "success", "data": {"articles": articles}}).encode()
    )


def test_refuses_to_run_without_authorisation(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "visto bueno" in capsys.readouterr().out


def test_only_reads_one_catalogue_item() -> None:
    opener = FakeOpener(_catalogue("Asesoría fiscal"))
    result = probe(BASE, KEY, opener)
    assert result.ok and result.articles == 1
    [request] = opener.requests
    assert request.full_url == BASE + "articles.php"
    assert request.get_method() == "POST"
    assert json.loads(request.data or b"") == {"action": "search", "limit": 1}  # type: ignore[arg-type]


def test_result_never_carries_content_or_key() -> None:
    result = probe(BASE, KEY, FakeOpener(_catalogue("Servicio secreto")))
    assert "Servicio secreto" not in repr(result)
    assert KEY not in repr(result)


@pytest.mark.parametrize(("code", "text"), [(401, "inválida"), (403, "permiso")])
def test_http_errors_are_explained(code: int, text: str) -> None:
    error = HTTPError(BASE, code, "x", Message(), None)
    result = probe(BASE, KEY, FakeOpener(error))
    assert result.status == code and not result.ok and text in result.message


def test_network_failure_is_not_success() -> None:
    result = probe(BASE, KEY, FakeOpener(URLError("sin red")))
    assert result.status is None and not result.ok


def test_unexpected_format_is_not_success() -> None:
    result = probe(BASE, KEY, FakeOpener(FakeResponse(200, b"<html>login</html>")))
    assert not result.ok and result.articles is None


@pytest.mark.parametrize("url", ["http://balter.example/api/v1/", "balter.example", ""])
def test_only_https_urls(url: str) -> None:
    with pytest.raises(ProbeError):
        check_base_url(url)


def test_missing_key_is_refused() -> None:
    with pytest.raises(ProbeError, match="BALTER_TOKEN"):
        probe(BASE, " ", FakeOpener(_catalogue()))
