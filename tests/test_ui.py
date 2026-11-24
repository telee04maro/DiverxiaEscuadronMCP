"""The panel never turns third-party text into links, images, HTML or maths, and only calls
"proven" what is proven to the cent."""

import re

from vigia import ui
from vigia.remeasure import Effect

HOSTILE = "[pincha](http://x.example) ![](http://x.example/t.png) <img src=x> $a$ :red[b]"


def _unescaped(text: str, char: str) -> bool:
    return re.search(rf"(?<!\\){re.escape(char)}", text) is not None


def test_markdown_from_data_has_no_active_syntax() -> None:
    safe = ui.md_safe(HOSTILE)
    for char in "[]()!<>$:":
        assert not _unescaped(safe, char), char


def test_markdown_escaping_keeps_the_visible_text() -> None:
    assert ui.md_safe("8.633,50 € (Mutua)").replace("\\", "") == "8.633,50 € (Mutua)"


def test_html_pieces_escape_data() -> None:
    card = ui.cause_card_html("Causa", HOSTILE, "<script>x</script>", [], cross=True)
    pill = ui.pill("<b>x</b>", "#000", "#fff")
    assert "<img" not in card and "<script>" not in card
    assert "&lt;b&gt;" in pill


def test_only_collections_are_called_proven() -> None:
    assert "céntimo" in ui.effect_label(Effect.CONFIRMED, collection=True)
    kpi = ui.effect_label(Effect.CONFIRMED, collection=False)
    assert "coincide" in kpi and "comprobad" not in kpi.lower()


def test_negative_effects_keep_their_meaning() -> None:
    assert ui.effect_label(Effect.NONE, collection=True) == "Sin efecto"
    assert ui.effect_label(Effect.NOT_DONE, collection=False) == "No se ejecutó"
