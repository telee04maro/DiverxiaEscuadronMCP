"""Demo ERP shaped like BALTER (contacts, opportunities without an owner, notes, origin).

SQLite on a local file: safe for a live demo, and ``reset`` deletes every record afterwards
(people from the audience may type their real phone number).
"""

import sqlite3
import uuid
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from vigia.connectors.base import (
    Contact,
    DuplicateOpenOpportunityError,
    NewContact,
    NewOpportunity,
    normalize_email,
    normalize_phone,
)
from vigia.data.model import Opportunity, OpportunityStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT, email TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY, contact_id TEXT NOT NULL REFERENCES contacts(id), channel TEXT NOT NULL,
    topic TEXT NOT NULL, summary TEXT NOT NULL, urgent INTEGER NOT NULL, created_at TEXT NOT NULL,
    first_response_at TEXT, assigned_to TEXT, status TEXT NOT NULL, origin TEXT
);
-- The ERP itself guarantees the contract, even under concurrent requests.
CREATE UNIQUE INDEX IF NOT EXISTS ux_contacts_phone ON contacts(phone) WHERE phone IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_contacts_email ON contacts(email) WHERE email IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_one_open_opportunity
    ON opportunities(contact_id) WHERE status = 'abierta';
CREATE INDEX IF NOT EXISTS ix_opportunities_created ON opportunities(created_at);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id TEXT NOT NULL REFERENCES opportunities(id),
    text TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class UnknownRecordError(LookupError):
    """The referenced contact or opportunity does not exist."""


class DemoErp:
    def __init__(self, path: Path, clock: Callable[[], datetime] = datetime.now) -> None:
        self._path = path
        self._clock = clock
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(_SCHEMA)

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path, timeout=10)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            with db:
                yield db

    def find_contact(self, *, phone: str | None, email: str | None) -> Contact | None:
        phone, email = normalize_phone(phone), normalize_email(email)
        if phone is None and email is None:
            return None
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM contacts WHERE (phone IS NOT NULL AND phone = ?) "
                "OR (email IS NOT NULL AND email = ?) ORDER BY created_at LIMIT 1",
                (phone, email),
            ).fetchone()
        return _contact(row) if row else None

    def create_contact(self, contact: NewContact) -> Contact:
        new_id = f"CT-{uuid.uuid4().hex[:8].upper()}"
        try:
            with self._db() as db:
                db.execute(
                    "INSERT INTO contacts (id, name, phone, email, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (new_id, contact.name, contact.phone, contact.email, self._clock().isoformat()),
                )
        except sqlite3.IntegrityError:
            existing = self.find_contact(phone=contact.phone, email=contact.email)
            if existing is None:
                raise
            return existing
        return Contact(id=new_id, name=contact.name, phone=contact.phone, email=contact.email)

    def create_opportunity(self, opportunity: NewOpportunity) -> Opportunity:
        new_id = f"OP-{uuid.uuid4().hex[:8].upper()}"
        received = opportunity.received_at or self._clock()
        answered = opportunity.first_response_at
        try:
            with self._db() as db:
                exists = db.execute(
                    "SELECT 1 FROM contacts WHERE id = ?", (opportunity.contact_id,)
                ).fetchone()
                if not exists:
                    raise UnknownRecordError(f"No existe el contacto {opportunity.contact_id}")
                db.execute(
                    "INSERT INTO opportunities (id, contact_id, channel, topic, summary, urgent, "
                    "created_at, first_response_at, assigned_to, status, origin) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL)",
                    (
                        new_id,
                        opportunity.contact_id,
                        opportunity.channel,
                        opportunity.topic,
                        opportunity.summary,
                        int(opportunity.urgent),
                        received.isoformat(),
                        answered.isoformat() if answered and answered >= received else None,
                        OpportunityStatus.OPEN.value,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateOpenOpportunityError(opportunity.contact_id) from error
        return self._opportunity(new_id)

    def add_note(self, opportunity_id: str, text: str) -> None:
        with self._db() as db:
            self._require(db, opportunity_id)
            db.execute(
                "INSERT INTO notes (opportunity_id, text, created_at) VALUES (?, ?, ?)",
                (opportunity_id, text[:2000], self._clock().isoformat()),
            )

    def mark_origin(self, opportunity_id: str, origin: str) -> None:
        with self._db() as db:
            self._require(db, opportunity_id)
            db.execute(
                "UPDATE opportunities SET origin = ? WHERE id = ?", (origin[:30], opportunity_id)
            )

    def list_opportunities(self) -> tuple[Opportunity, ...]:
        with self._db() as db:
            rows = db.execute("SELECT * FROM opportunities ORDER BY created_at").fetchall()
        return tuple(_opportunity(row) for row in rows)

    def open_opportunity(self, contact_id: str) -> Opportunity | None:
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM opportunities WHERE contact_id = ? AND status = ?",
                (contact_id, OpportunityStatus.OPEN.value),
            ).fetchone()
        return _opportunity(row) if row else None

    def notes(self, opportunity_id: str) -> tuple[str, ...]:
        with self._db() as db:
            rows = db.execute(
                "SELECT text FROM notes WHERE opportunity_id = ? ORDER BY id", (opportunity_id,)
            ).fetchall()
        return tuple(row["text"] for row in rows)

    def origin(self, opportunity_id: str) -> str | None:
        with self._db() as db:
            row = self._require(db, opportunity_id)
        value = row["origin"]
        return str(value) if value is not None else None

    def contact(self, contact_id: str) -> Contact | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        return _contact(row) if row else None

    def reset(self) -> None:
        """Delete every record (after a live demo with real people)."""
        with self._db() as db:
            db.execute("DELETE FROM notes")
            db.execute("DELETE FROM opportunities")
            db.execute("DELETE FROM contacts")

    def _opportunity(self, opportunity_id: str) -> Opportunity:
        with self._db() as db:
            return _opportunity(self._require(db, opportunity_id))

    @staticmethod
    def _require(db: sqlite3.Connection, opportunity_id: str) -> sqlite3.Row:
        row: sqlite3.Row | None = db.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        if row is None:
            raise UnknownRecordError(f"No existe la oportunidad {opportunity_id}")
        return row


def _contact(row: sqlite3.Row) -> Contact:
    return Contact(id=row["id"], name=row["name"], phone=row["phone"], email=row["email"])


def _opportunity(row: sqlite3.Row) -> Opportunity:
    return Opportunity(
        id=row["id"],
        contact_id=row["contact_id"],
        channel=row["channel"],
        topic=row["topic"],
        summary=row["summary"],
        urgent=bool(row["urgent"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        first_response_at=(
            datetime.fromisoformat(row["first_response_at"]) if row["first_response_at"] else None
        ),
        assigned_to=row["assigned_to"],
        status=OpportunityStatus(row["status"]),
    )
