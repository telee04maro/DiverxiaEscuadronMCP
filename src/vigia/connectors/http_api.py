"""Minimal HTTP API of the demo ERP, so the WhatsApp assistant (Hermes) can write to it.

Contract: docs/integracion-whatsapp-erp.md. Every request needs ``Authorization: Bearer <token>``
(``VIGIA_ERP_TOKEN``); by default the server listens only on 127.0.0.1. Errors never return
stack traces.

Run: uv run python -m vigia.connectors.http_api --port 8765
"""

import argparse
import hmac
import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, ValidationError

from vigia.audit import AuditLog
from vigia.connectors.base import Enquiry, NewContact, NewOpportunity, register_enquiry
from vigia.connectors.demo_erp import DemoErp, UnknownRecordError

MAX_BODY = 64 * 1024
REQUEST_TIMEOUT_S = 10
PREFIX = "/api/v1"
_NOTES = re.compile(rf"^{PREFIX}/opportunities/(?P<id>[\w-]{{1,40}})/notes$")
_ORIGIN = re.compile(rf"^{PREFIX}/opportunities/(?P<id>[\w-]{{1,40}})/origin$")


class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class OriginIn(BaseModel):
    origin: str = Field(min_length=1, max_length=30)


class ApiError(Exception):
    def __init__(self, status: HTTPStatus, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def build_server(host: str, port: int, erp: DemoErp, token: str) -> ThreadingHTTPServer:
    if len(token) < 16:  # noqa: PLR2004 - a short token is guessable
        raise ValueError("VIGIA_ERP_TOKEN debe tener al menos 16 caracteres")
    log = AuditLog()

    class Handler(BaseHTTPRequestHandler):
        server_version = "VigiaDemoERP/1.0"
        sys_version = ""
        timeout = REQUEST_TIMEOUT_S  # slow or idle clients cannot hold a thread forever

        def do_GET(self) -> None:
            self._handle(self._get)

        def do_POST(self) -> None:
            self._handle(self._post)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: ANN401
            """Log method and path only: bodies may contain personal data."""

        def _handle(self, route: Any) -> None:  # noqa: ANN401 - bound method
            try:
                self._authorize()
                status, payload = route()
            except ApiError as error:
                status, payload = error.status, {"error": error.message}
            except ValidationError as error:
                fields = [".".join(map(str, e["loc"])) or "cuerpo" for e in error.errors()]
                status, payload = (
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    {
                        "error": "Datos no válidos",
                        "campos": fields,
                    },
                )
            except UnknownRecordError as error:
                status, payload = HTTPStatus.NOT_FOUND, {"error": str(error)}
            except ValueError:
                status, payload = HTTPStatus.BAD_REQUEST, {"error": "Petición no válida"}
            except Exception:  # never leak a stack trace to the client
                status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Error interno"}
            self._send(status, payload)

        def _authorize(self) -> None:
            header = self.headers.get("Authorization", "")
            given = header.removeprefix("Bearer ").strip().encode("utf-8", "surrogateescape")
            expected = token.encode("utf-8")
            if not header.startswith("Bearer ") or not hmac.compare_digest(given, expected):
                raise ApiError(HTTPStatus.UNAUTHORIZED, "Token no válido")

        def _body(self) -> Any:  # noqa: ANN401 - raw JSON, validated by the caller
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ApiError(HTTPStatus.LENGTH_REQUIRED, "Falta Content-Length")
            length = int(raw_length)
            if length < 0:
                raise ApiError(HTTPStatus.BAD_REQUEST, "Content-Length no válido")
            if length > MAX_BODY:
                raise ApiError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Cuerpo demasiado grande")
            raw = self.rfile.read(length)
            try:
                return json.loads(raw or b"{}")
            except json.JSONDecodeError as error:
                raise ApiError(HTTPStatus.BAD_REQUEST, "JSON no válido") from error

        def _get(self) -> tuple[HTTPStatus, Any]:
            url = urlparse(self.path)
            if url.path == f"{PREFIX}/contacts":
                query = parse_qs(url.query)
                contact = erp.find_contact(
                    phone=query.get("phone", [None])[0], email=query.get("email", [None])[0]
                )
                if contact is None:
                    raise ApiError(HTTPStatus.NOT_FOUND, "Contacto no encontrado")
                return HTTPStatus.OK, contact.model_dump()
            if url.path == f"{PREFIX}/opportunities":
                return HTTPStatus.OK, [o.model_dump(mode="json") for o in erp.list_opportunities()]
            raise ApiError(HTTPStatus.NOT_FOUND, "Ruta no encontrada")

        def _post(self) -> tuple[HTTPStatus, Any]:
            path = urlparse(self.path).path
            if path == f"{PREFIX}/contacts":
                contact = erp.create_contact(NewContact.model_validate(self._body()))
                return HTTPStatus.CREATED, contact.model_dump()
            if path == f"{PREFIX}/opportunities":
                created = erp.create_opportunity(NewOpportunity.model_validate(self._body()))
                return HTTPStatus.CREATED, created.model_dump(mode="json")
            if path == f"{PREFIX}/enquiries":
                outcome = register_enquiry(erp, Enquiry.model_validate(self._body()), log)
                return HTTPStatus.CREATED, outcome.model_dump()
            if match := _NOTES.match(path):
                erp.add_note(match["id"], NoteIn.model_validate(self._body()).text)
                return HTTPStatus.CREATED, {"ok": True}
            if match := _ORIGIN.match(path):
                erp.mark_origin(match["id"], OriginIn.model_validate(self._body()).origin)
                return HTTPStatus.OK, {"ok": True}
            raise ApiError(HTTPStatus.NOT_FOUND, "Ruta no encontrada")

        def _send(self, status: HTTPStatus, payload: Any) -> None:  # noqa: ANN401
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="API del ERP de demo de Vigía")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--db", type=Path, default=Path(os.environ.get("VIGIA_ERP_DB", "data/erp-demo.sqlite"))
    )
    args = parser.parse_args()
    token = os.environ.get("VIGIA_ERP_TOKEN", "")
    server = build_server(args.host, args.port, DemoErp(args.db), token)
    print(f"ERP de demo escuchando en http://{args.host}:{args.port}{PREFIX}")
    if args.host not in {"127.0.0.1", "localhost"}:
        print(
            "Aviso: la API es HTTP sin cifrar. Úsala solo en una red de confianza "
            "y apágala al terminar."
        )
    server.serve_forever()


if __name__ == "__main__":
    main()
