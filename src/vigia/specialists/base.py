"""The specialist interface. A new specialist is a new implementation, not an edit."""

from typing import Protocol

from vigia.audit import AuditLog
from vigia.data.model import CompanyData
from vigia.domain.findings import Area, SpecialistReport
from vigia.llm.base import LanguageModel


class Specialist(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def area(self) -> Area: ...

    @property
    def sources(self) -> tuple[str, ...]: ...

    def analyze(self, data: CompanyData, model: LanguageModel, log: AuditLog) -> SpecialistReport:
        """Read the company's data from this specialist's sources and report findings."""
        ...
