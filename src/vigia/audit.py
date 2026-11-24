"""Auditable log: what each agent saw, decided, did and checked."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EventKind(StrEnum):
    SAW = "vio"
    DECIDED = "decidió"
    DID = "hizo"
    CHECKED = "comprobó"
    REJECTED = "rechazó"
    ESCALATED = "derivó"


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent: str
    kind: EventKind
    message: str
    refs: tuple[str, ...] = ()


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(self, agent: str, kind: EventKind, message: str, *refs: str) -> None:
        self._events.append(AuditEvent(agent=agent, kind=kind, message=message, refs=refs))

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
