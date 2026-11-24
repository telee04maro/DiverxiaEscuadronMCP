"""Competition and market specialist: competitor ads, prices, reviews and search visibility.

Claude reads ad copy and classifies review themes; rules do everything else. What the model
extracts is checked against the source text (an offer price must literally appear in the ad),
and if the model is unavailable the keyword rules take over.
"""

import re
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from vigia.audit import AuditLog, EventKind
from vigia.data.model import CompanyData, CompetitorAd, Review, SearchResult
from vigia.domain.findings import (
    Area,
    Confidence,
    DataGap,
    Evidence,
    Finding,
    Kpi,
    Signal,
    SpecialistReport,
)
from vigia.domain.money import MoneyError, eur, fmt_eur, fmt_num, pct_change
from vigia.domain.vocabulary import vocabulary_for
from vigia.llm.base import LanguageModel, Tier

NAME = "Agente de competencia y mercado"
SOURCES = (
    "Biblioteca de Anuncios de Meta (instantánea sintética, formato ads_archive)",
    "Precios publicados de la competencia",
    "Reseñas propias y de la competencia (sintéticas)",
    "Resultados de búsqueda y anuncios en Google (instantánea sintética)",
)
ADS_SOURCE = SOURCES[0]

NEW_AD_DAYS = 30
RECENT_REVIEW_DAYS = 60
WAIT_SHARE_THRESHOLD = Decimal("0.30")
RATING_DROP_THRESHOLD = Decimal("0.5")
PRICE_GAP_THRESHOLD_PCT = Decimal("5")
GOOD_POSITION = 3

_PRICE = re.compile(r"(\d+(?:[.,]\d{1,2})?)\s?€")
_NO_WAIT = re.compile(r"sin esperas?|cita en 24|cita hoy|cita en el día", re.IGNORECASE)
# The model may only say an ad promises no waiting if the ad talks about time at all.
_TIME_HINT = re.compile(r"esper|cita|24 ?h|hoy|inmediat|rápid|al momento", re.IGNORECASE)
MAX_THEME_DISAGREEMENT = Decimal("0.3")


class Theme(StrEnum):
    WAIT = "espera"
    TREATMENT = "trato"
    PRICE = "precio"
    RESULT = "resultado"
    FACILITIES = "instalaciones"
    OTHER = "otro"


_THEME_WORDS: dict[Theme, tuple[str, ...]] = {
    Theme.WAIT: ("espera", "esperé", "cita", "semanas", "tard", "hueco", "cambiaron la cita"),
    Theme.TREATMENT: ("trato", "atención", "cercano", "profesional", "explican"),
    Theme.PRICE: ("precio", "caro", "barato", "€"),
    Theme.RESULT: ("recuper", "mejor", "tratamiento", "rodilla", "lumbalgia"),
    Theme.FACILITIES: ("local", "aparcar", "instalaciones", "pequeño"),
}


class AdReading(BaseModel):
    index: int
    offer_price_eur: str | None = Field(
        description="Precio de la oferta tal y como aparece en el texto (p. ej. '20'), o null"
    )
    offer_service: str | None = Field(description="Servicio al que se aplica la oferta, o null")
    promises_no_wait: bool = Field(description="True si promete cita inmediata o sin esperas")


class AdReadings(BaseModel):
    ads: list[AdReading]


class ReviewTag(BaseModel):
    index: int
    themes: list[Theme]


class ReviewTags(BaseModel):
    reviews: list[ReviewTag]


class _AdFacts(BaseModel):
    ad: CompetitorAd
    offer_price: Decimal | None
    offer_service: str | None
    promises_no_wait: bool


class CompetitionSpecialist:
    @property
    def name(self) -> str:
        return NAME

    @property
    def area(self) -> Area:
        return Area.COMPETITION

    @property
    def sources(self) -> tuple[str, ...]:
        return SOURCES

    def analyze(self, data: CompanyData, model: LanguageModel, log: AuditLog) -> SpecialistReport:
        today = data.company.analysis_date
        log.record(
            NAME,
            EventKind.SAW,
            f"{len(data.competitor_ads)} anuncios, {len(data.competitors)} competidores, "
            f"{len(data.reviews)} reseñas y {len(data.search_results)} resultados de búsqueda",
        )
        new_ads = [
            ad
            for ad in data.competitor_ads
            if ad.active_on(today) and ad.ad_delivery_start_time >= today - timedelta(NEW_AD_DAYS)
        ]
        ad_facts = _read_ads(new_ads, model, log)
        themes = _classify_reviews(data.reviews, model, log, data.company.sector)
        findings = [
            *_offer_findings(ad_facts, today),
            *_price_findings(data),
            *_review_findings(data, themes),
            *_search_findings(data),
        ]
        for finding in findings:
            log.record(NAME, EventKind.DECIDED, finding.title, finding.id)
        return SpecialistReport(
            specialist=NAME,
            area=Area.COMPETITION,
            sources=SOURCES,
            kpis=_kpis(data, themes, len(new_ads)),
            findings=tuple(findings),
            gaps=_gaps(data),
        )


def _read_ads(ads: list[CompetitorAd], model: LanguageModel, log: AuditLog) -> list[_AdFacts]:
    if not ads:
        return []
    listing = "\n".join(f"[{i}] {' / '.join(ad.ad_creative_bodies)}" for i, ad in enumerate(ads))
    answer = model.structured(
        task="Leer anuncios de la competencia",
        tier=Tier.FAST,
        system="Eres analista de marketing. Extrae de cada anuncio la oferta de precio, si la hay.",
        prompt=f"Anuncios de la competencia:\n{listing}",
        schema=AdReadings,
    )
    facts = [_rule_reading(ad) for ad in ads]
    if answer is None:
        log.record(NAME, EventKind.DECIDED, "Anuncios leídos con reglas (sin IA)")
        return facts
    for reading in answer.ads:
        if not 0 <= reading.index < len(ads):
            log.record(
                NAME, EventKind.REJECTED, f"La IA citó un anuncio inexistente ({reading.index})"
            )
            continue
        ad = ads[reading.index]
        price = _verified_price(reading.offer_price_eur, ad)
        if reading.offer_price_eur and price is None:
            log.record(
                NAME,
                EventKind.REJECTED,
                f"Precio «{reading.offer_price_eur}» propuesto por la IA no aparece en el anuncio",
            )
        facts[reading.index] = _AdFacts(
            ad=ad,
            offer_price=price,
            offer_service=reading.offer_service,
            promises_no_wait=reading.promises_no_wait
            and bool(_TIME_HINT.search(" ".join(ad.ad_creative_bodies))),
        )
    log.record(NAME, EventKind.DECIDED, "Anuncios leídos con IA y verificados contra el texto")
    return facts


def _rule_reading(ad: CompetitorAd) -> _AdFacts:
    text = " ".join(ad.ad_creative_bodies)
    prices = [_safe_eur(m) for m in _PRICE.findall(text)]
    valid = [p for p in prices if p is not None]
    return _AdFacts(
        ad=ad,
        offer_price=min(valid) if valid else None,
        offer_service=None,
        promises_no_wait=bool(_NO_WAIT.search(text)),
    )


def _verified_price(raw: str | None, ad: CompetitorAd) -> Decimal | None:
    if not raw:
        return None
    price = _safe_eur(raw)
    text = " ".join(ad.ad_creative_bodies)
    found = {p for p in (_safe_eur(m) for m in _PRICE.findall(text)) if p is not None}
    return price if price in found else None


def _safe_eur(raw: str) -> Decimal | None:
    try:
        return eur(raw)
    except MoneyError:
        return None


def _classify_reviews(
    reviews: tuple[Review, ...], model: LanguageModel, log: AuditLog, sector: str
) -> list[frozenset[Theme]]:
    rules = [_rule_themes(r.text) for r in reviews]
    if not reviews:
        return rules
    listing = "\n".join(f"[{i}] {r.text}" for i, r in enumerate(reviews))
    answer = model.structured(
        task="Clasificar reseñas por tema",
        tier=Tier.FAST,
        system=(
            f"Clasifica cada reseña de una empresa del sector «{sector}» en sus temas: espera "
            "(citas, retrasos), trato, precio, resultado, instalaciones u otro."
        ),
        prompt=f"Reseñas:\n{listing}",
        schema=ReviewTags,
    )
    if answer is None:
        log.record(NAME, EventKind.DECIDED, "Reseñas clasificadas con palabras clave (sin IA)")
        return rules
    themes = list(rules)
    covered = set()
    for tag in answer.reviews:
        if 0 <= tag.index < len(reviews) and tag.themes:
            themes[tag.index] = frozenset(tag.themes)
            covered.add(tag.index)
    ai_waits = sum(1 for t in themes if Theme.WAIT in t)
    rule_waits = sum(1 for t in rules if Theme.WAIT in t)
    tolerance = max(Decimal(2), MAX_THEME_DISAGREEMENT * len(reviews))
    if abs(ai_waits - rule_waits) > tolerance:
        log.record(
            NAME,
            EventKind.REJECTED,
            f"La IA marcó {ai_waits} reseñas de espera y las palabras clave {rule_waits}: "
            "discrepan demasiado, se usan las reglas",
        )
        return rules
    log.record(
        NAME,
        EventKind.DECIDED,
        f"Reseñas clasificadas con IA ({len(covered)}/{len(reviews)}; el resto, con reglas)",
    )
    return themes


def _rule_themes(text: str) -> frozenset[Theme]:
    lowered = text.lower()
    found = {theme for theme, words in _THEME_WORDS.items() if any(w in lowered for w in words)}
    return frozenset(found or {Theme.OTHER})


def _offer_findings(facts: list[_AdFacts], today: date) -> list[Finding]:
    findings = []
    for index, fact in enumerate(f for f in facts if f.offer_price is not None):
        ad = fact.ad
        days = (today - ad.ad_delivery_start_time).days
        platforms = " e ".join(p.capitalize() for p in ad.publisher_platforms) or "redes"
        signals = {Signal.COMPETITOR_OFFER}
        if fact.promises_no_wait:
            signals.add(Signal.COMPETITOR_PROMISES_NO_WAIT)
        promise = " y promete cita sin esperas" if fact.promises_no_wait else ""
        assert fact.offer_price is not None  # noqa: S101 - filtered above; narrows the type
        findings.append(
            Finding(
                id=f"COMP-OFERTA-{index + 1}",
                area=Area.COMPETITION,
                title=(
                    f"{ad.page_name} lanzó hace {days} días una oferta a "
                    f"{fmt_eur(fact.offer_price)}{promise}"
                ),
                detail=f"Anuncio activo en {platforms} desde el {ad.ad_delivery_start_time:%d/%m}.",
                evidence=(
                    Evidence(
                        source=ADS_SOURCE,
                        fact=f"«{' '.join(ad.ad_creative_bodies)}»",
                        on=ad.ad_delivery_start_time,
                    ),
                ),
                confidence=Confidence.HIGH,
                impact=4,
                urgency=4,
                effort=2,
                signals=frozenset(signals),
            )
        )
    return findings


def _price_findings(data: CompanyData) -> list[Finding]:
    own = data.company.service(data.company.main_service)
    if own is None:
        return []
    cheaper = [
        (c, c.prices[own.name])
        for c in data.competitors
        if own.name in c.prices and c.prices[own.name] < own.price
    ]
    if not cheaper:
        return []
    rival, price = min(cheaper, key=lambda pair: pair[1])
    gap = pct_change(price, own.price)
    if gap is None or gap < PRICE_GAP_THRESHOLD_PCT:
        return []
    evidence = [
        Evidence(source="Precios publicados", fact=f"{own.name}: {fmt_eur(own.price)} (nosotros)"),
        Evidence(source="Precios publicados", fact=f"{own.name}: {fmt_eur(price)} ({rival.name})"),
    ]
    if rival.first_visit_price is not None:
        evidence.append(
            Evidence(
                source="Precios publicados",
                fact=f"Primera visita en {rival.name}: {fmt_eur(rival.first_visit_price)}",
            )
        )
    return [
        Finding(
            id="COMP-PRECIO",
            area=Area.COMPETITION,
            title=f"Somos un {fmt_num(gap)} % más caros que {rival.name} en {own.name.lower()}",
            detail=f"{rival.name} está a {rival.distance_m} m.",
            evidence=tuple(evidence),
            confidence=Confidence.HIGH,
            impact=3,
            urgency=3,
            effort=2,
            signals=frozenset({Signal.HIGHER_PRICE}),
        )
    ]


def _review_split(reviews: tuple[Review, ...], today: date) -> tuple[list[int], list[int]]:
    cutoff = today - timedelta(RECENT_REVIEW_DAYS)
    recent = [i for i, r in enumerate(reviews) if r.on >= cutoff]
    older = [i for i, r in enumerate(reviews) if r.on < cutoff]
    return recent, older


def _average(reviews: tuple[Review, ...], indexes: list[int]) -> Decimal | None:
    if not indexes:
        return None
    total = sum(reviews[i].rating for i in indexes)
    return (Decimal(total) / len(indexes)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _wait_share(themes: list[frozenset[Theme]], indexes: list[int]) -> Decimal | None:
    if not indexes:
        return None
    waits = sum(1 for i in indexes if Theme.WAIT in themes[i])
    return (Decimal(waits) / len(indexes)).quantize(Decimal("0.01"))


def _review_findings(data: CompanyData, themes: list[frozenset[Theme]]) -> list[Finding]:
    reviews = data.reviews
    recent, older = _review_split(reviews, data.company.analysis_date)
    recent_avg, older_avg = _average(reviews, recent), _average(reviews, older)
    share = _wait_share(themes, recent)
    if recent_avg is None or share is None:
        return []
    signals: set[Signal] = set()
    if share >= WAIT_SHARE_THRESHOLD:
        signals.add(Signal.WAIT_COMPLAINTS)
    if older_avg is not None and older_avg - recent_avg >= RATING_DROP_THRESHOLD:
        signals.add(Signal.RATING_DROP)
    if not signals:
        return []
    examples = [reviews[i] for i in recent if Theme.WAIT in themes[i]][:3]
    evidence = [
        Evidence(
            source="Reseñas propias",
            fact=f"Nota media de los últimos {RECENT_REVIEW_DAYS} días: {fmt_num(recent_avg)} "
            f"(antes {fmt_num(older_avg) if older_avg is not None else 'sin datos'})",
        ),
        *(
            Evidence(source="Reseña propia", fact=f"«{r.text}» ({r.rating}★)", on=r.on)
            for r in examples
        ),
    ]
    best = max(
        (c for c in data.competitors if c.rating is not None),
        key=lambda c: c.rating or 0,
        default=None,
    )
    if best is not None:
        evidence.append(
            Evidence(
                source="Reseñas de la competencia",
                fact=f"{best.name}: {fmt_num(best.rating or Decimal(0))}★",
            )
        )
    percent = int(share * 100)
    return [
        Finding(
            id="COMP-RESENAS",
            area=Area.COMPETITION,
            title=_review_title(recent_avg, percent, signals),
            detail="Las quejas hablan de tardar en dar cita y de esperas en recepción.",
            evidence=tuple(evidence),
            confidence=Confidence.HIGH if len(recent) >= 5 else Confidence.MEDIUM,  # noqa: PLR2004
            impact=4,
            urgency=4,
            effort=3,
            signals=frozenset(signals),
        )
    ]


def _review_title(recent_avg: Decimal, percent: int, signals: set[Signal]) -> str:
    parts = []
    if Signal.RATING_DROP in signals:
        parts.append(f"La nota cae a {fmt_num(recent_avg)}★")
    if Signal.WAIT_COMPLAINTS in signals:
        parts.append(f"el {percent} % de las reseñas recientes se quejan de la espera")
    title = " y ".join(parts)
    return title[0].upper() + title[1:]


def _search_findings(data: CompanyData) -> list[Finding]:
    searched_for = vocabulary_for(data.company).searched_for
    own_name = data.company.name
    findings = []
    for index, query in enumerate(data.company.queries_of_interest):
        results = [r for r in data.search_results if r.query == query]
        if not results:
            continue
        own = min((r.position for r in results if r.business == own_name), default=None)
        if own is not None and own <= GOOD_POSITION:
            continue
        sponsored = [r for r in results if r.sponsored and r.business != own_name]
        evidence = [_search_evidence(r) for r in sorted(results, key=lambda r: r.position)[:4]]
        place = f"en la posición {own}" if own else "fuera de los resultados recogidos"
        signals = frozenset({Signal.LOW_SEARCH_VISIBILITY})
        findings.append(
            Finding(
                id=f"COMP-BUSQUEDA-{index + 1}",
                area=Area.COMPETITION,
                title=f"En «{query}» aparecemos {place}"
                + (f"; {sponsored[0].business} paga anuncios" if sponsored else ""),
                detail=f"Quien busca {searched_for} en Google encuentra antes a la competencia.",
                evidence=tuple(evidence),
                confidence=Confidence.MEDIUM,
                impact=3,
                urgency=2,
                effort=4,
                signals=signals,
            )
        )
    return findings


def _search_evidence(result: SearchResult) -> Evidence:
    kind = "anuncio" if result.sponsored else "orgánico"
    return Evidence(
        source="Resultados de búsqueda (instantánea sintética)",
        fact=f"«{result.query}» n.º {result.position} ({kind}): {result.business}",
    )


def _kpis(data: CompanyData, themes: list[frozenset[Theme]], new_ads: int) -> tuple[Kpi, ...]:
    reviews = data.reviews
    recent, older = _review_split(reviews, data.company.analysis_date)
    share = _wait_share(themes, recent)
    own = data.company.service(data.company.main_service)
    rivals = [c.prices[own.name] for c in data.competitors if own and own.name in c.prices]
    cheapest = min(rivals, default=None)
    kpis = [
        Kpi(
            key="nota_reciente",
            label="Nota media reciente",
            value=_average(reviews, recent),
            unit="★",
        ),
        Kpi(
            key="nota_anterior",
            label="Nota media anterior",
            value=_average(reviews, older),
            unit="★",
        ),
        Kpi(
            key="resenas_espera",
            label="Reseñas recientes que se quejan de la espera",
            value=share * 100 if share is not None else None,
            unit="%",
        ),
        Kpi(
            key="anuncios_nuevos",
            label=f"Anuncios nuevos de la competencia ({NEW_AD_DAYS} días)",
            value=Decimal(new_ads) if data.competitor_ads else None,
            unit="",
        ),
        Kpi(
            key="diferencia_precio",
            label="Diferencia con el competidor más barato",
            value=pct_change(cheapest, own.price) if own and cheapest else None,
            unit="%",
        ),
    ]
    for index, query in enumerate(data.company.queries_of_interest):
        position = min(
            (
                r.position
                for r in data.search_results
                if r.query == query and r.business == data.company.name
            ),
            default=None,
        )
        kpis.append(
            Kpi(
                key=f"posicion_busqueda_{index + 1}",
                label=f"Posición en «{query}»",
                value=Decimal(position) if position else None,
                unit="",
                note="" if position else "No aparece en los resultados recogidos",
            )
        )
    return tuple(kpis)


def _gaps(data: CompanyData) -> tuple[DataGap, ...]:
    gaps = [
        DataGap(
            area=Area.COMPETITION,
            missing="Visitas a la web y reservas online",
            why_it_matters="Con ellas sabría si la gente nos busca y no reserva o ni nos ve",
        ),
        DataGap(
            area=Area.COMPETITION,
            missing="Datos en vivo de Meta, Google Ads y Google Maps",
            why_it_matters=(
                "Hoy se analiza una instantánea; en producción, las APIs oficiales (ver fuentes)"
            ),
        ),
    ]
    for name, what, why in (
        ("resenas.json", "Reseñas propias", "Sin ellas no veo de qué se quejan los clientes"),
        (
            "competencia/competidores.json",
            "Precios de la competencia",
            "Sin ellos no comparo precios",
        ),
        ("competencia/busqueda.json", "Resultados de búsqueda", "Sin ellos no mido la visibilidad"),
    ):
        if name in data.missing_sources:
            gaps.append(DataGap(area=Area.COMPETITION, missing=what, why_it_matters=why))
    if not data.competitor_ads:
        gaps.append(
            DataGap(
                area=Area.COMPETITION,
                missing="Anuncios de la competencia",
                why_it_matters="Sin ellos no veo ofertas que expliquen fugas de clientes",
            )
        )
    return tuple(gaps)
