"""Personal data minimisation (red team R3-08).

Reviews are third-party text: they are kept without names, phones, e-mails or ID numbers, so
those never reach the panel, the log or Claude. Debtors' names never reach Claude either: the
model sees a pseudonym ("Cliente 1") and Vigía puts the real name back locally.
"""

import re
from collections.abc import Iterable, Mapping

from vigia.domain.grounding import PHONE

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
ID_NUMBER = re.compile(r"\b(?:\d{8}|[XYZ]\d{7})[A-Z]\b", re.IGNORECASE)
_WORD = r"[A-ZÁÉÍÓÚÑ][a-záéíóúüñ]+"
# Two or more capitalised words in a row ("Juan Pérez García", "Ana de la Torre").
FULL_NAME = re.compile(rf"\b{_WORD}(?:\s+(?:de\s+(?:la\s+|los\s+)?)?{_WORD})+\b")
# One name after a cue ("me atendió Laura", "preguntad por Marta").
CUED_NAME = re.compile(
    rf"\b(atendi[óo]|atendieron|soy|llamadme|llamad a|preguntad por|pregunten por|"
    rf"de parte de)\s+{_WORD}\b",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    """The same review, without anything that identifies a person."""
    text = EMAIL.sub("[correo]", text)
    text = ID_NUMBER.sub("[documento]", text)
    text = PHONE.sub("[teléfono]", text)
    text = CUED_NAME.sub(lambda m: f"{m.group(1)} [nombre]", text)
    return FULL_NAME.sub("[nombre]", text)


def pseudonyms(names: Iterable[str], kinds: Mapping[str, str] | None = None) -> dict[str, str]:
    """Real name -> "Aseguradora 1", "Empresa 2"… (the kind, never the name), or "Cliente N".

    Longest names first, so no name is a prefix of another when they are swapped.
    """
    unique = sorted({n for n in names if n.strip()}, key=len, reverse=True)
    labels = kinds or {}
    return {
        name: f"{labels.get(name, 'cliente').capitalize()} {index}"
        for index, name in enumerate(unique, start=1)
    }


def swap(text: str, mapping: Mapping[str, str]) -> str:
    for old, new in sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True):
        text = text.replace(old, new)
    return text
