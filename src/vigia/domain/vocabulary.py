"""Words that depend on the sector: a physio clinic has patients and sessions, a garage has
customers and sales. The rules are the same; only what the owner reads changes."""

import re
from dataclasses import dataclass, replace
from typing import Protocol


class _Profile(Protocol):
    @property
    def sector(self) -> str: ...

    @property
    def main_service(self) -> str: ...


@dataclass(frozen=True)
class Vocabulary:
    customers: str  # "pacientes"
    customer: str  # "paciente"
    units_title: str  # "Sesiones" (as in "Sesiones por mes")
    private_units: str  # "sesiones de particulares"
    repeat_units: str  # what a new customer comes back for: "sesiones"
    first_offer: str  # "primera visita"
    offer_audience: str  # who the counter-offer is for, when the noun does not say it
    new_customer_slots: str  # "primeras visitas" (agenda slots)
    searched_for: str  # what people type in Google: "fisioterapeuta"


HEALTH = Vocabulary(
    customers="pacientes",
    customer="paciente",
    units_title="Sesiones",
    private_units="sesiones de particulares",
    repeat_units="sesiones",
    first_offer="primera visita",
    offer_audience="",
    new_customer_slots="primeras visitas",
    searched_for="este servicio",
)
GENERAL = Vocabulary(
    customers="clientes",
    customer="cliente",
    units_title="Ventas",
    private_units="ventas a particulares",
    repeat_units="compras",
    first_offer="primer servicio",
    offer_audience=" para clientes nuevos",
    new_customer_slots="clientes nuevos",
    searched_for="este servicio",
)

_HEALTH = re.compile(
    r"cl[ií]nic|fisio|dental|dentist|odont|m[eé]dic|salud|sanitari|psic[oó]log|podolog|"
    r"osteop|nutricion|logoped|enfermer|[oó]ptic",
    re.IGNORECASE,
)
_PROFESSIONALS = (
    (re.compile(r"fisio", re.IGNORECASE), "fisioterapeuta"),
    (re.compile(r"dental|dentist|odont", re.IGNORECASE), "dentista"),
    (re.compile(r"psic[oó]log", re.IGNORECASE), "psicólogo"),
    (re.compile(r"podolog", re.IGNORECASE), "podólogo"),
)


def vocabulary_for(company: _Profile) -> Vocabulary:
    text = f"{company.sector} {company.main_service}"
    if not _HEALTH.search(text):
        return GENERAL
    professional = next((name for rx, name in _PROFESSIONALS if rx.search(text)), None)
    return replace(HEALTH, searched_for=professional) if professional else HEALTH
