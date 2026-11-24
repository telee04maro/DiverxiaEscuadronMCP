"""Sending e-mail. In the demo, mail goes to a local outbox, or by SMTP only to a test inbox."""

import re
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol

from vigia.config import Settings, SmtpSettings

ORIGINAL_TO = "X-Vigia-Destinatario-Original"


class Mailer(Protocol):
    def send(self, message: EmailMessage) -> str:
        """Send the message and describe where it went."""
        ...


class OutboxMailer:
    """Writes each message as an .eml file the demo panel can show."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def send(self, message: EmailMessage) -> str:
        self._folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        recipient = re.sub(r"[^\w.-]", "_", str(message["To"]))
        path = self._folder / f"{stamp}-{recipient}.eml"
        path.write_bytes(message.as_bytes())
        return f"Bandeja local: {path.as_posix()}"


class SmtpMailer:
    """Real delivery, but always to the configured test inbox: never to the real client."""

    def __init__(self, smtp: SmtpSettings, test_inbox: str) -> None:
        self._smtp = smtp
        self._test_inbox = test_inbox

    def send(self, message: EmailMessage) -> str:
        original = str(message["To"])
        del message["To"]
        message["To"] = self._test_inbox
        message[ORIGINAL_TO] = original
        if message["From"] is None:
            message["From"] = self._smtp.sender
        with smtplib.SMTP(self._smtp.host, self._smtp.port, timeout=30) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(self._smtp.user, self._smtp.password.get_secret_value())
            server.send_message(message)
        return f"Enviado por SMTP al buzón de prueba (destinatario real: {original})"


def build_mailer(settings: Settings) -> Mailer:
    if settings.smtp is not None and settings.demo_recipient:
        return SmtpMailer(settings.smtp, settings.demo_recipient)
    return OutboxMailer(settings.outbox_dir)
