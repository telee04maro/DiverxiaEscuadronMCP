"""Look and feel of the demo panel: palette, styles and small HTML pieces.

Presentation only. Every text that comes from data (findings, causes, plan items, the model)
is escaped before it goes into HTML: it may contain third-party text (ads, reviews).
"""

import re
from html import escape

import streamlit as st

from vigia.coordinator.plan import Autonomy
from vigia.domain.findings import Area
from vigia.remeasure import Effect

PETROL = "#1D5C7A"
TERRA = "#D9824E"
INK = "#1B2B34"
SAND = "#FAF7F2"
LINE = "#E6E1D8"
MUTED = "#5B6B75"

AREA_COLOR: dict[Area, str] = {
    Area.FINANCE: PETROL,
    Area.COMPETITION: TERRA,
    Area.CUSTOMERS: "#4F8A6B",
    Area.MARKETING: "#8A6FB0",
    Area.LEGAL: "#6B7A86",
    Area.PEOPLE: "#B0718F",
}

# (text colour, background, plain words for the owner)
AUTONOMY_STYLE: dict[Autonomy, tuple[str, str, str]] = {
    Autonomy.AUTO: ("#1F6B43", "#E4F3EA", "Lo hace Vigía solo"),
    Autonomy.APPROVAL: ("#9A4F22", "#FBEADF", "Te lo prepara y tú apruebas"),
    Autonomy.PERSON: (PETROL, "#E2EEF4", "Lo hace una persona"),
    Autonomy.EXPERT: ("#5B3F8C", "#EEE8F7", "Lo revisa un experto"),
}

EFFECT_STYLE: dict[Effect, tuple[str, str]] = {
    Effect.CONFIRMED: ("#1F6B43", "#E4F3EA"),
    Effect.PARTIAL: ("#8A5A00", "#FBF0D9"),
    Effect.NONE: ("#A12A1F", "#FBE6E3"),
    Effect.NOT_DONE: (MUTED, "#EEF0F2"),
    Effect.NOT_MEASURABLE: (MUTED, "#EEF0F2"),
}

CSS = f"""
<style>
:root {{ --vg-petrol: {PETROL}; --vg-terra: {TERRA}; --vg-ink: {INK}; --vg-line: {LINE}; }}
.block-container {{ padding-top: 1.6rem; max-width: 1320px; }}
h1, h2, h3, h4 {{ color: {INK}; letter-spacing: -0.01em; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}
[data-testid="stHeader"] {{ background: transparent; }}
button[data-baseweb="tab"] p {{ font-size: 0.98rem; font-weight: 600; }}
[data-testid="stMetric"] {{ background: #fff; border: 1px solid {LINE};
  border-top: 4px solid {PETROL};
  border-radius: 12px; padding: 10px 14px; }}
[data-testid="stMetricValue"] {{ color: {INK}; font-weight: 700; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; }}
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {{
  border-radius: 10px; font-weight: 600; }}
.vg-hero {{ background: linear-gradient(135deg, {PETROL} 0%, #154760 100%); color: #fff;
  border-radius: 18px; padding: 22px 28px; margin-bottom: 14px; display: flex; gap: 24px;
  align-items: center; justify-content: space-between; flex-wrap: wrap; }}
.vg-hero h1 {{ color: #fff; font-size: 1.75rem; margin: 0; padding: 0; }}
.vg-hero p {{ color: #D6E6EE; margin: 4px 0 0; font-size: 1rem; }}
.vg-steps {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.vg-step {{ border-radius: 999px; padding: 6px 14px; font-size: 0.88rem; font-weight: 600;
  background: rgba(255,255,255,0.12); color: #D6E6EE; border: 1px solid rgba(255,255,255,0.18); }}
.vg-step.done {{ background: #fff; color: {PETROL}; }}
.vg-step.now {{ background: {TERRA}; color: #fff; border-color: {TERRA}; }}
.vg-pill {{ display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: 0.8rem;
  font-weight: 600; line-height: 1.6; margin: 2px 4px 2px 0; }}
.vg-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%;
  margin-right: 6px; }}
.vg-cause {{ background: #FFF8F2; border: 1px solid #F1DCCB; border-left: 6px solid {TERRA};
  border-radius: 14px; padding: 18px 22px; margin: 6px 0 12px; }}
.vg-cause.single {{ background: #fff; border-color: {LINE}; border-left-color: {PETROL}; }}
.vg-kicker {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em;
  text-transform: uppercase;
  color: {TERRA}; }}
.vg-cause.single .vg-kicker {{ color: {PETROL}; }}
.vg-cause h3 {{ margin: 4px 0 8px; font-size: 1.35rem; line-height: 1.3; }}
.vg-cause p {{ margin: 0 0 10px; color: {INK}; }}
.vg-support {{ list-style: none; padding: 0; margin: 0; }}
.vg-support li {{ margin: 6px 0; color: {INK}; }}
.vg-tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;
  margin: 8px 0 4px; }}
.vg-tile {{ background: #fff; border: 1px solid {LINE}; border-radius: 14px; padding: 14px 16px; }}
.vg-tile .v {{ font-size: 1.6rem; font-weight: 700; color: {INK}; line-height: 1.2; }}
.vg-tiles.kpi {{ grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; }}
.vg-tile .v.sm {{ font-size: 1.3rem; }}
.vg-tile .l {{ font-size: 0.88rem; color: {MUTED}; margin-top: 2px; }}
.vg-head {{ display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 1.1rem;
  color: {INK}; margin-bottom: 2px; }}
.vg-legend {{ font-size: 0.85rem; color: {MUTED}; margin: 4px 0 10px; }}
.vg-note {{ font-size: 0.9rem; color: {MUTED}; }}
</style>
"""


_MARKDOWN_ACTIVE = re.compile(r"([\\`*_{}\[\]()#+\-.!|<>$~:])")


def md_safe(text: str) -> str:
    """Third-party text shown through st.markdown as plain text: no links, images, maths or
    colour directives can come from an ad, a review or an uploaded file."""
    return _MARKDOWN_ACTIVE.sub(r"\\\1", text)


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def html(fragment: str) -> None:
    st.markdown(fragment, unsafe_allow_html=True)


def pill(text: str, color: str, background: str) -> str:
    return (
        f'<span class="vg-pill" style="color:{color};background:{background}">{escape(text)}</span>'
    )


def autonomy_pill(autonomy: Autonomy) -> str:
    color, background, words = AUTONOMY_STYLE[autonomy]
    return pill(words, color, background)


def effect_label(effect: Effect, *, collection: bool, short_payment: bool = False) -> str:
    """A KPI that moved only coincides in time; only a collection is proven (to the cent)."""
    if effect is Effect.NONE and short_payment:
        return "Pago incompleto: no se da por cobrada"
    if effect is Effect.CONFIRMED:
        return "Cobro comprobado al céntimo" if collection else "Mejoró (coincide en el tiempo)"
    return effect.value.capitalize()


def effect_pill(effect: Effect, *, collection: bool, short_payment: bool = False) -> str:
    color, background = EFFECT_STYLE[effect]
    label = effect_label(effect, collection=collection, short_payment=short_payment)
    return pill(label, color, background)


def area_chip(area: Area, label: str) -> str:
    color = AREA_COLOR.get(area, MUTED)
    return f'<span class="vg-dot" style="background:{color}"></span><b>{escape(label)}</b>'


def hero(title: str, subtitle: str, steps: list[tuple[str, str]]) -> None:
    """Brand header with the journey; each step is (label, 'done' | 'now' | '')."""
    chips = "".join(
        f'<span class="vg-step {state}">{escape(label)}</span>' for label, state in steps
    )
    html(
        f'<div class="vg-hero"><div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>'
        f'<div class="vg-steps">{chips}</div></div>'
    )


def tiles(items: list[tuple[str, str]]) -> None:
    """Big numbers for the owner: (value, label)."""
    cells = "".join(
        f'<div class="vg-tile"><div class="v">{escape(v)}</div>'
        f'<div class="l">{escape(lbl)}</div></div>'
        for v, lbl in items
    )
    html(f'<div class="vg-tiles">{cells}</div>')


def kpi_tiles(items: list[tuple[str, str, str]]) -> None:
    """Specialist numbers that wrap instead of being cut: (value, label, note)."""
    cells = "".join(
        f'<div class="vg-tile" title="{escape(note)}"><div class="v sm">{escape(v)}</div>'
        f'<div class="l">{escape(lbl)}</div></div>'
        for v, lbl, note in items
    )
    html(f'<div class="vg-tiles kpi">{cells}</div>')


def cause_card(
    kicker: str, title: str, explanation: str, support: list[str], *, cross: bool
) -> None:
    """support items are already-safe HTML (built with area_chip + escaped text)."""
    html(cause_card_html(kicker, title, explanation, support, cross=cross))


def cause_card_html(
    kicker: str, title: str, explanation: str, support: list[str], *, cross: bool
) -> str:
    rows = "".join(f"<li>{item}</li>" for item in support)
    return (
        f'<div class="vg-cause{"" if cross else " single"}">'
        f'<div class="vg-kicker">{escape(kicker)}</div>'
        f"<h3>{escape(title)}</h3><p>{escape(explanation)}</p>"
        f'<ul class="vg-support">{rows}</ul></div>'
    )


def legend() -> None:
    html(
        '<div class="vg-legend">'
        + " ".join(autonomy_pill(a) for a in Autonomy)
        + "<br>Vigía solo actúa sin preguntar en lo reversible; "
        + "lo serio lo decides tú o un experto.</div>"
    )
