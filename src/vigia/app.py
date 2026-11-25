"""Pymbrain demo panel. Run with: uv run streamlit run src/vigia/app.py

The panel only presents; every decision lives in the agents (see vigia.pipeline).
"""

from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from html import escape
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from vigia import ui
from vigia.actions.mailer import build_mailer
from vigia.audit import AuditLog
from vigia.config import Settings
from vigia.connectors.base import Enquiry, register_enquiry
from vigia.connectors.demo_erp import DemoErp
from vigia.coordinator.plan import Kind, PlanItem
from vigia.crm import CustomerCard, build_cards
from vigia.data.intake import TEMPLATES, Interview, build_company_data
from vigia.data.loader import load_company_data
from vigia.data.model import CompanyData
from vigia.data.synthetic import AFTER, BEFORE, DEMO_ROOT
from vigia.domain.findings import AREA_LABELS, Area, Finding, Kpi, SpecialistReport
from vigia.domain.money import MoneyError, eur, fmt_eur, fmt_num
from vigia.domain.priority import HORIZON_LABELS, Horizon
from vigia.finance.reconciliation import PaymentStatus
from vigia.llm.base import LanguageModel, total_cost
from vigia.llm.factory import build_model
from vigia.pipeline import (
    Analysis,
    Execution,
    analyze,
    approve,
    execute_plan,
    mark_done,
    measure_after,
)
from vigia.remeasure import Effect, ItemResult, Remeasurement

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = (
    ("Marketing y clientes", "Responde reseñas y lanza campañas"),
    ("Legal y cumplimiento", "Calendario de obligaciones y documentos; lo complejo, a un abogado"),
    ("Organización y personas", "Cuellos de botella y clima con encuesta anónima"),
    ("Chat del dueño", "Pregunta y aprueba por WhatsApp; los agentes son sus herramientas"),
)
DEMO = "Clínica de ejemplo (datos ficticios)"
OWN = "Tu empresa (sube tus datos)"
MAX_WARNINGS = 8
MAX_CARDS = 25
FIELD_LABELS = {
    "name": "nombre",
    "sector": "sector",
    "city": "ciudad",
    "employees": "empleados",
    "main_service": "servicio principal",
    "main_price": "precio",
    "main_cost": "coste directo",
    "sessions_per_new_client": "compras por cliente nuevo",
    "opening_hour": "hora de apertura",
    "closing_hour": "hora de cierre",
}
BRAND = Path(__file__).resolve().parents[2] / "docs" / "negocio" / "pymbrain"
TABS = (
    "1 · Tu empresa", "2 · Expertos", "3 · Causa y plan", "4 · Actuar",
    "5 · ¿Funcionó?", "6 · Transparencia", "7 · WhatsApp", "8 · Clientes",
)  # fmt: skip
# Owner's key numbers, in this order, when the specialist measured them (never shown as zero).
KEY_KPIS = ("dias_de_caja", "vencido", "perdidas_fuera_horario", "nota_reciente")
NO_ANALYSIS = "Primero pulsa «Analizar con el equipo de agentes» en la pestaña 1 · Tu empresa."


def _state() -> None:
    if "settings" in st.session_state:
        return
    settings = Settings.from_env()
    st.session_state.settings = settings
    st.session_state.model = build_model(settings)
    st.session_state.mailer = build_mailer(settings)
    st.session_state.log = AuditLog()
    st.session_state.before = load_company_data(ROOT / DEMO_ROOT / BEFORE)
    st.session_state.after = load_company_data(ROOT / DEMO_ROOT / AFTER)
    st.session_state.analysis = None
    st.session_state.own_data = None
    st.session_state.erp = DemoErp(ROOT / settings.erp_db)
    st.session_state.executions = {}
    st.session_state.execution = Execution()
    st.session_state.remeasure = None
    st.session_state.after_reports = None


def _fmt_kpi(kpi: Kpi) -> str:
    if kpi.value is None:
        return "—"
    if kpi.unit == "€":
        return fmt_eur(kpi.value.quantize(Decimal(1))).replace(",00 €", " €")
    if kpi.unit == "★":  # a rating keeps its decimal: 3,0 ★, never 3 ★
        return f"{fmt_num(kpi.value.quantize(Decimal('0.1')))} ★"
    if kpi.unit == "h":
        return _fmt_value(kpi.value, "h")
    return f"{_fmt_value(kpi.value, '')} {kpi.unit}".strip()


def _fmt_value(value: Decimal | None, unit_hint: str) -> str:
    if value is None:
        return "—"
    if unit_hint == "€":
        return fmt_eur(value)
    if unit_hint == "★":
        return f"{fmt_num(value.quantize(Decimal('0.1')))} ★"
    if unit_hint == "h":  # 0,0 h reads as "minutes", never as a bare 0
        return f"{fmt_num(value.quantize(Decimal('0.1')))} h"
    number = fmt_num(Decimal(format(value.normalize(), "f")))
    return f"{number} {unit_hint}".strip()


def _sidebar() -> None:
    model: LanguageModel = st.session_state.model
    with st.sidebar:
        st.markdown("**Un equipo de expertos de IA para toda tu pyme, en un solo sitio.**")
        st.caption("IA que impulsa tu pyme")
        st.divider()
        st.markdown("**Controles de la demo**")
        if st.button("Reiniciar la demo", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        with st.expander("Detalles técnicos"):
            st.markdown("**Modo de IA**")
            st.caption(model.mode)
            st.markdown("**Envío de correos**")
            settings: Settings = st.session_state.settings
            st.caption(
                "SMTP al buzón de prueba"
                if settings.smtp and settings.demo_recipient
                else f"Bandeja local ({settings.outbox_dir.as_posix()}/)"
            )
        st.caption(
            "La clínica de ejemplo es 100 % sintética. Con «Tu empresa», sube solo datos de tu "
            "negocio: no hacen falta datos personales de clientes."
        )


def _current_data() -> CompanyData | None:
    if st.session_state.get("dataset", DEMO) == DEMO:
        data: CompanyData = st.session_state.before
    else:
        own: CompanyData | None = st.session_state.own_data
        if own is None:
            return None
        data = own
    if st.session_state.get("with_erp"):
        live = st.session_state.erp.list_opportunities()
        data = data.model_copy(update={"opportunities": (*data.opportunities, *live)})
    return data


def _company_tab() -> None:
    choice = st.radio("¿Qué empresa analizamos?", (DEMO, OWN), key="dataset", horizontal=True)
    if choice == OWN:
        _intake_section()
    data = _current_data()
    if data is None:
        return
    summary_slot = st.container()  # the owner's summary goes first once there is an analysis
    st.divider()
    previous: Analysis | None = st.session_state.analysis
    if previous is not None and previous.data.company.name == data.company.name:
        with st.expander("Datos de la empresa y fuentes conectadas"):
            _company_summary(data)
    else:
        _company_summary(data)
    st.toggle(
        "Incluir también las consultas registradas en el ERP de demo (pestaña 7)",
        key="with_erp",
        value=True,
    )
    if choice == DEMO and st.session_state.get("with_erp"):
        st.caption(
            "La clínica de ejemplo se analiza a fecha de sus datos: las consultas que entren hoy "
            "por WhatsApp cuentan en el análisis de «Tu empresa», no en este."
        )
    if st.button("Analizar con el equipo de agentes", type="primary", use_container_width=True):
        with st.spinner("Los especialistas están analizando y el coordinador cruza lo que ven…"):
            st.session_state.analysis = analyze(data, st.session_state.model, st.session_state.log)
            # One execution per company: what was already sent is never sent again.
            executions: dict[str, Execution] = st.session_state.executions
            st.session_state.execution = executions.setdefault(data.company.name, Execution())
            st.session_state.analysed_demo = choice == DEMO
            st.session_state.remeasure = None
    analysis: Analysis | None = st.session_state.analysis
    if analysis is not None and analysis.data.company.name == data.company.name:
        with summary_slot:
            _owner_summary(analysis)


def _owner_summary(analysis: Analysis) -> None:
    """What the owner needs first: the cause, a few numbers and this week's actions."""
    st.markdown("### Lo más importante")
    causes = analysis.crossing.causes
    if causes:
        cause = causes[0]
        ui.cause_card(
            "Causa cruzada" if cause.is_cross else "Causa principal",
            cause.title,
            f"Lo ven: {_areas_label(cause.areas)}. El detalle, en la pestaña 3.",
            [],
            cross=cause.is_cross,
        )
    else:
        st.info(
            "No hay evidencia suficiente para señalar una causa: mira qué falta en la pestaña 2."
        )
    kpis = {k.key: k for report in analysis.reports for k in report.kpis if k.value is not None}
    numbers = [(_fmt_kpi(kpis[key]), kpis[key].label) for key in KEY_KPIS if key in kpis]
    if numbers:
        ui.tiles(numbers)
    week = analysis.plan.by_horizon(Horizon.WEEK)[:3]
    if week:
        st.markdown("#### Qué hacer esta semana")
        for item in week:
            ui.html(f"{ui.autonomy_pill(item.autonomy)} {escape(item.title)}")
        st.caption("El plan completo, a 7, 30 y 90 días, está en la pestaña 3; para actuar, la 4.")


def _company_summary(data: CompanyData) -> None:
    company = data.company
    st.subheader(company.name)
    st.caption(
        f"{company.sector} · {company.city} · {company.employees} personas · "
        f"análisis a {company.analysis_date:%d/%m/%Y}"
    )
    left, right = st.columns(2)
    with left:
        st.markdown("**Entrevista inicial**")
        if company.goals:
            st.markdown("Objetivos:\n" + "\n".join(f"- {g}" for g in company.goals))
        if company.resources:
            st.markdown(f"Recursos: {ui.md_safe(company.resources)}")
        st.markdown(
            "Servicios: " + ", ".join(f"{s.name} ({fmt_eur(s.price)})" for s in company.services)
        )
    with right:
        st.markdown("**Fuentes conectadas**")
        st.markdown(
            f"- Facturas: {len(data.invoices)}\n- Movimientos del banco: {len(data.bank)}\n"
            f"- Meses de ventas: {len({s.month for s in data.sessions})}\n"
            f"- Consultas del CRM: {len(data.opportunities)}\n"
            f"- Reseñas: {len(data.reviews)}\n- Anuncios de la competencia: "
            f"{len(data.competitor_ads)}\n- Competidores: {len(data.competitors)}"
        )
        if data.missing_sources:
            st.warning("Faltan (se verá como «lo que me falta»): " + ", ".join(data.missing_labels))


def _amount(raw: str) -> Decimal | None:
    """Empty or unreadable is None, never 0: the interview then asks for it again."""
    try:
        return eur(raw) if raw.strip() else None
    except MoneyError:
        return None


def _intake_section() -> None:
    st.markdown("### Así entra una empresa")
    st.caption(
        "1) Entrevista inicial · 2) Sube tus Excel o CSV (descarga las plantillas) · 3) Analiza. "
        "No subas datos personales de clientes: no hacen falta."
    )
    with st.expander("Plantillas (cabeceras en español, formato 1.234,56 y 31/10/2026)"):
        for template in TEMPLATES.values():
            st.download_button(
                f"{template.label}{' (obligatoria)' if template.required else ''}",
                template.csv_text(),
                file_name=f"plantilla_{template.key}.csv",
                mime="text/csv",
                key=f"tpl-{template.key}",
                help=template.help,
            )
    with st.form("intake"):
        a, b, c = st.columns(3)
        name = a.text_input("Nombre de la empresa")
        sector = b.text_input("Sector", placeholder="Clínica, taller, comercio…")
        city = c.text_input("Ciudad", value="Málaga")
        d, e, f = st.columns(3)
        employees = d.number_input("Empleados", min_value=1, max_value=10_000, value=10)
        opening = e.number_input("Abre a las", min_value=0, max_value=23, value=9)
        closing = f.number_input("Cierra a las", min_value=1, max_value=24, value=20)
        g, h, i, j = st.columns(4)
        service = g.text_input("Servicio principal")
        price = h.text_input("Precio (€)")
        cost = i.text_input("Coste directo (€)")
        repeat = j.text_input("Compras por cliente nuevo (media)")
        goals = st.text_area("Objetivos (uno por línea)")
        files = {
            key: st.file_uploader(template.label, type=["csv", "xlsx"], key=f"up-{key}")
            for key, template in TEMPLATES.items()
        }
        submitted = st.form_submit_button("Cargar mis datos")
    if not submitted:
        return
    try:
        interview = Interview.model_validate(
            {
                "name": name,
                "sector": sector,
                "city": city,
                "employees": int(employees),
                "main_service": service,
                "main_price": _amount(price),
                "main_cost": _amount(cost),
                "sessions_per_new_client": _amount(repeat) if repeat.strip() else None,
                "goals": tuple(line.strip() for line in goals.splitlines() if line.strip()),
                "opening_hour": int(opening),
                "closing_hour": int(closing),
            }
        )
    except ValidationError as error:
        fields = ", ".join(
            FIELD_LABELS.get(str(err["loc"][0]) if err["loc"] else "", "horario")
            for err in error.errors()
        )
        st.error(f"Revisa la entrevista: faltan o no son válidos estos campos: {fields}")
        return
    uploads = {k: (u.name, u.getvalue()) for k, u in files.items() if u is not None}
    result = build_company_data(interview, uploads, today=date.today())
    st.session_state.own_data = result.data
    if result.loaded:
        loaded = ", ".join(f"{label} ({rows} filas)" for label, rows in result.loaded.items())
        st.success(f"Cargado: {loaded}")
    for error_text in result.errors[:MAX_WARNINGS]:
        st.warning(error_text)
    if len(result.errors) > MAX_WARNINGS:
        st.warning(f"… y {len(result.errors) - MAX_WARNINGS} avisos más")


def _finding_card(finding: Finding) -> None:
    with st.expander(f"**{ui.md_safe(finding.title)}**  ·  confianza {finding.confidence.value}"):
        st.caption(f"{finding.id} · {ui.md_safe(finding.detail)}")
        for evidence in finding.evidence:
            when = f" ({evidence.on:%d/%m/%Y})" if evidence.on else ""
            st.markdown(
                f"- {ui.md_safe(evidence.fact)}{when}  \n  :gray[{ui.md_safe(evidence.source)}]"
            )
        st.caption(
            f"Impacto {finding.impact}/5 · urgencia {finding.urgency}/5 · "
            f"esfuerzo {finding.effort}/5"
        )


def _report_column(report: SpecialistReport) -> None:
    with st.container(border=True):
        ui.html(f'<div class="vg-head">{ui.area_chip(report.area, report.specialist)}</div>')
        st.caption("Sus fuentes: " + " · ".join(report.sources))
        kpis = [k for k in report.kpis if not k.key.startswith("dias_cobro_")] or list(report.kpis)
        ui.kpi_tiles(
            [
                (_fmt_kpi(k), k.label, k.note or ("No disponible" if k.value is None else ""))
                for k in kpis
            ]
        )
        st.markdown("**Lo que ha visto** (abre cada uno para ver la evidencia)")
        for finding in report.findings:
            _finding_card(finding)
        with st.expander("Lo que me falta para afinar"):
            for gap in report.gaps:
                st.markdown(f"- **{ui.md_safe(gap.missing)}**: {ui.md_safe(gap.why_it_matters)}")


def _specialists_tab(analysis: Analysis) -> None:
    columns = st.columns(len(analysis.reports))
    for column, report in zip(columns, analysis.reports, strict=True):
        with column:
            _report_column(report)
    st.markdown("#### Hoja de ruta: más especialistas")
    columns = st.columns(len(ROADMAP))
    for column, (name, what) in zip(columns, ROADMAP, strict=True):
        with column.container(border=True):
            st.markdown(f":gray[**{name}**]")
            st.caption(what)


def _areas_label(areas: tuple[Area, ...]) -> str:
    return " + ".join(AREA_LABELS[a] for a in areas)


def _coordinator_tab(analysis: Analysis) -> None:
    crossing = analysis.crossing
    st.markdown("### Por qué pasa")
    st.caption(
        f"El coordinador cruza lo que ve cada experto · cómo se ha cruzado: {crossing.origin.value}"
    )
    for cause in crossing.causes:
        support = [
            f"{ui.area_chip(f.area, AREA_LABELS[f.area])} · {escape(f.title)}"
            for f in (analysis.finding(i) for i in cause.finding_ids)
            if f
        ]
        kicker = "Causa cruzada" if cause.is_cross else "Causa de un área"
        ui.cause_card(
            f"{kicker} · {_areas_label(cause.areas)} · confianza {cause.confidence.value}",
            cause.title,
            cause.explanation,
            support,
            cross=cause.is_cross,
        )
    for hypothesis in crossing.discarded:
        st.info(
            f"**Descartado:** {ui.md_safe(hypothesis.hypothesis)}. {ui.md_safe(hypothesis.reason)}"
        )
    for note in crossing.rejected:
        st.warning(f"Rechazado por falta de evidencia: {ui.md_safe(note)}")
    st.divider()
    st.markdown("### Qué hacer y cuándo")
    ui.legend()
    columns = st.columns(3)
    for column, horizon in zip(columns, Horizon, strict=True):
        with column:
            st.markdown(f"#### {HORIZON_LABELS[horizon]}")
            for item in analysis.plan.by_horizon(horizon):
                _plan_card(item)
    if analysis.plan.offer_checks:
        with st.expander("Cómo validó finanzas la contraoferta"):
            for check in analysis.plan.offer_checks:
                mark = "✅" if check.viable else "❌"
                st.markdown(f"{mark} {ui.md_safe(check.reason)}")


def _plan_card(item: PlanItem) -> None:
    with st.container(border=True):
        st.markdown(f"**{ui.md_safe(item.title)}**")
        ui.html(
            f"{ui.autonomy_pill(item.autonomy)} <span class='vg-note'>{escape(item.owner)}</span>"
        )
        st.caption(f"Por qué: {ui.md_safe(item.why)}")
        if item.detail:
            st.caption(ui.md_safe(item.detail))


def _actions_tab(analysis: Analysis) -> None:
    execution: Execution = st.session_state.execution
    log: AuditLog = st.session_state.log
    model = st.session_state.model
    mailer = st.session_state.mailer
    if st.button("Ejecutar lo que los agentes pueden hacer solos", type="primary"):
        with st.spinner("Preparando y enviando…"):
            execute_plan(
                analysis, model, mailer, log, st.session_state.settings, execution=execution
            )
    if execution.pending:
        st.markdown("### Esperan tu aprobación")
        for item_id, claim in list(execution.pending.items()):
            with st.container(border=True):
                st.markdown(
                    f"**{ui.md_safe(claim.subject)}** → {ui.md_safe(claim.to)}  \n"
                    f":orange[Tono {claim.tone.value}] · "
                    f"{claim.origin.value} · total {fmt_eur(claim.total)}"
                )
                st.text(claim.body)
                if st.button("Aprobar y enviar", key=f"approve-{item_id}"):
                    approve(analysis, item_id, execution, mailer, log)
                    st.rerun()
    if execution.sent:
        st.markdown("### Enviado")
        for sent in execution.sent:
            with st.expander(
                f"✉️ {ui.md_safe(sent.claim.subject)} → {ui.md_safe(sent.claim.client_name)}"
            ):
                st.caption(f"{sent.delivery} · {sent.claim.origin.value}")
                st.text(sent.claim.body)
        st.info(
            "Enviar no es cobrar: estas facturas siguen pendientes hasta que el banco lo "
            "confirme (pestaña 5)."
        )
    others = [i for i in analysis.plan.items if i.kind is not Kind.COLLECT]
    if others:
        st.markdown("### Asignadas a personas o pendientes de aprobación")
        st.caption("Marca lo que ya se ha hecho: solo eso se medirá un mes después.")
        for item in others:
            done = item.id in execution.claimed
            label = f"{item.title} · {item.owner} · {item.autonomy.value}"
            if st.checkbox(label, value=done, key=f"done-{item.id}", disabled=done) and not done:
                mark_done(item.id, execution, log)


def _after_data() -> CompanyData:
    after: CompanyData = st.session_state.after
    return after


def _remeasure_tab(analysis: Analysis) -> None:
    if not st.session_state.get("analysed_demo", True):
        st.info(
            "Para tu empresa, la re-medición se hace al subir los datos del mes siguiente. "
            "En la demo usamos un «mes después» simulado de la clínica de ejemplo."
        )
        return
    st.caption(
        "«Un mes después» son datos simulados del 2/12/2026 con lo que habría pasado tras el plan."
    )
    if st.button("Medir un mes después", type="primary"):
        reports, measured = measure_after(
            analysis,
            _after_data(),
            st.session_state.execution,
            st.session_state.model,
            st.session_state.log,
        )
        st.session_state.after_reports = reports
        st.session_state.remeasure = measured
    result: Remeasurement | None = st.session_state.remeasure
    if result is None:
        return
    counts = Counter(
        ui.effect_label(
            r.effect, collection=r.item.kind is Kind.COLLECT, short_payment=_short_payment(r)
        )
        for r in result.results
    )
    ui.tiles([(str(n), label) for label, n in counts.items()])
    units = {k.key: k.unit for report in analysis.reports for k in report.kpis}
    done = [r for r in result.results if r.effect is not Effect.NOT_DONE]
    skipped = [r for r in result.results if r.effect is Effect.NOT_DONE]
    if not done:
        st.info(
            "Aún no se ha hecho nada del plan: marca en la pestaña 4 lo que ya está hecho "
            "y vuelve a medir. Solo se mide lo que se ha hecho."
        )
    for r in done:
        unit = "€" if r.item.kind is Kind.COLLECT else units.get(r.item.target_kpi, "")
        badge = ui.effect_pill(
            r.effect, collection=r.item.kind is Kind.COLLECT, short_payment=_short_payment(r)
        )
        with st.container(border=True):
            ui.html(f"{badge} <b>{escape(r.item.title)}</b>")
            st.markdown(
                f"{ui.md_safe(r.kpi_label)}: "
                f"**{_fmt_value(r.before, unit)} → {_fmt_value(r.after, unit)}**"
            )
            st.caption(r.note)
            for check in r.invoices:
                st.markdown(
                    f"- {check.invoice_id}: {fmt_eur(check.amount)} · cobrado "
                    f"{fmt_eur(check.paid)} → **{check.status.value}**"
                )
    if skipped:
        st.caption(
            "Sin hacer todavía (no se les atribuye ningún cambio): "
            + "; ".join(r.item.title for r in skipped)
        )
    st.markdown("### Plan reordenado")
    for item in result.next_plan:
        st.markdown(f"- **{HORIZON_LABELS[item.horizon]}** · {ui.md_safe(item.title)}")


def _short_payment(result: ItemResult) -> bool:
    return any(c.status is PaymentStatus.PARTIAL for c in result.invoices)


def _erp_tab() -> None:
    erp: DemoErp = st.session_state.erp
    st.markdown("### ERP de demo (con la forma de BALTER)")
    st.caption(
        "Aquí escribe el asistente de WhatsApp (Hermes) a través de la API del ERP de demo, "
        "con las 5 operaciones de su conector. También puedes simular un mensaje aquí."
    )
    with st.form("whatsapp"):
        a, b = st.columns(2)
        name = a.text_input("Nombre (usa uno ficticio)", value="Paciente de prueba")
        phone = b.text_input("Teléfono (ficticio)", value="600000001")
        email = a.text_input(
            "Correo (opcional, ficticio)",
            help="Prueba con pagos@mutuabeta.example: la consulta se une a la ficha de Mutua Beta "
            "en la pestaña 8, junto a lo que le debe a la clínica.",
        )
        topic = a.text_input("Motivo", value="Primera visita")
        urgent = b.checkbox("Urgente")
        summary = st.text_area("Lo que ha contado", value="Dolor de espalda desde hace dos semanas")
        sent = st.form_submit_button("Simular mensaje de WhatsApp")
    if sent:
        try:
            now = datetime.now()
            enquiry = Enquiry(
                name=name,
                phone=phone,
                email=email or None,
                topic=topic,
                summary=summary,
                urgent=urgent,
                received_at=now,
                answered_at=now,  # the assistant answers in the moment
            )
            outcome = register_enquiry(erp, enquiry, st.session_state.log)
        except ValueError as error:
            st.error(f"No se ha registrado: {str(error).splitlines()[0]}")
        else:
            if outcome.new_opportunity:
                st.success(f"Oportunidad nueva {outcome.opportunity_id}, sin responsable asignado")
            else:
                st.info(
                    f"Ya tenía una oportunidad abierta ({outcome.opportunity_id}): va como nota"
                )
            if outcome.escalated:
                st.warning("Urgente: se avisa al responsable en el momento")
    opportunities = erp.list_opportunities()
    st.markdown(f"**Oportunidades en el ERP de demo: {len(opportunities)}**")
    if opportunities:
        st.dataframe(
            [
                {
                    "Id": o.id,
                    "Contacto": o.contact_id,
                    "Canal": o.channel,
                    "Motivo": o.topic,
                    "Urgente": "sí" if o.urgent else "",
                    "Recibida": o.created_at.strftime("%d/%m %H:%M"),
                    "Responsable": o.assigned_to or "— sin asignar",
                    "Estado": o.status.value,
                    "Notas": len(erp.notes(o.id)),
                }
                for o in reversed(opportunities)
            ],
            hide_index=True,
            use_container_width=True,
        )
    if st.button("Borrar todos los datos del ERP de demo"):
        erp.reset()
        st.rerun()
    with st.expander("Cómo se conecta el asistente de WhatsApp (Hermes)"):
        st.markdown(
            "Arranca la API con `uv run python -m vigia.connectors.http_api --port 8765` "
            "(variable `VIGIA_ERP_TOKEN` obligatoria) y apunta el conector de Hermes a "
            "`http://<este-equipo>:8765/api/v1`. Contrato completo en "
            "`docs/integracion-whatsapp-erp.md`."
        )


def _log_tab() -> None:
    model: LanguageModel = st.session_state.model
    log: AuditLog = st.session_state.log
    st.markdown("### Uso de la IA")
    st.caption(model.mode)
    calls = model.calls
    if calls:
        st.metric("Coste de IA de esta sesión", f"{total_cost(calls):.4f} $")
        st.dataframe(
            [
                {
                    "Tarea": c.task,
                    "Modelo": c.model,
                    "Tokens entrada": c.input_tokens,
                    "Tokens salida": c.output_tokens,
                    "Coste ($)": f"{c.cost_usd:.4f}",
                    "Tiempo (s)": f"{c.seconds:.1f}",
                    "OK": "sí" if c.ok else f"no ({c.note})",
                }
                for c in calls
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Sin llamadas a la IA en esta sesión: todo se resolvió con reglas.")
    st.markdown("### Registro de los agentes")
    st.dataframe(
        [
            {"Hora": e.at.astimezone().strftime("%H:%M:%S"), "Agente": e.agent, "Qué": e.kind.value,
             "Detalle": e.message, "Referencias": ", ".join(e.refs)}
            for e in log.events
        ],
        hide_index=True,
        use_container_width=True,
    )  # fmt: skip


def _crm_tab(analysis: Analysis) -> None:
    erp: DemoErp = st.session_state.erp
    execution: Execution = st.session_state.execution
    # Only with the switch on (tab 1): otherwise the cards would not match the agents (R3-13).
    live = erp.list_opportunities() if st.session_state.get("with_erp") else ()
    contacts = {o.contact_id: found for o in live if (found := erp.contact(o.contact_id))}
    cards = build_cards(
        analysis.data,
        contacts=contacts,
        extra_opportunities=live,
        sent=[s.claim for s in execution.sent],
        pending=execution.pending.values(),
    )
    st.markdown("### Una ficha por cliente, con lo que sabe cada agente")
    st.caption(
        "No hay una lista de clientes por agente: finanzas aporta facturas y deudas, atención y "
        "captación las consultas, y las acciones las reclamaciones. Se unen por correo o "
        "teléfono, así que un mismo cliente es una sola ficha. Si el correo o el teléfono "
        "coinciden pero el nombre no, se avisa para revisarlo."
    )
    a, b, c = st.columns(3)
    a.metric("Clientes", len(cards))
    b.metric("Necesitan algo", sum(1 for card in cards if card.alerts))
    c.metric("Los ven varios agentes", sum(1 for card in cards if card.crossed))
    only = st.toggle("Solo los que necesitan algo", value=True, key="crm-only-alerts")
    shown = [card for card in cards if card.alerts or card.conflict] if only else list(cards)
    for card in shown[:MAX_CARDS]:
        _customer_card(card)
    if len(shown) > MAX_CARDS:
        st.caption(f"… y {len(shown) - MAX_CARDS} fichas más")


def _customer_card(card: CustomerCard) -> None:
    with st.container(border=True):
        crossed = " · :blue[la ven varios agentes]" if card.crossed else ""
        st.markdown(f"**{card.name}** · {card.kind}{crossed}")
        reach = " · ".join(x for x in (card.email, card.phone) if x)
        if reach:
            st.caption(reach)
        for alert in card.alerts:
            st.markdown(f":orange[● {alert}]")
        if card.conflict:
            st.warning(card.conflict)
        for agent, fact in card.facts:
            st.markdown(f"- **{agent}:** {fact}")


def main() -> None:
    icon = str(BRAND / "icono.png") if (BRAND / "icono.png").exists() else "🧭"
    st.set_page_config(page_title="pymbrain", page_icon=icon, layout="wide")
    if (BRAND / "logo-simple.png").exists():
        st.logo(str(BRAND / "logo-simple.png"), size="large", icon_image=icon)
    ui.apply_theme()
    _state()
    _sidebar()
    header = st.empty()  # filled at the end, once this run's actions are known
    tabs = st.tabs(list(TABS))
    with tabs[6]:
        _erp_tab()
    with tabs[0]:
        _company_tab()
    # Read after the company tab: its button may have just produced the analysis.
    analysis: Analysis | None = st.session_state.analysis
    for tab, render in zip(
        tabs[1:5], (_specialists_tab, _coordinator_tab, _actions_tab, _remeasure_tab), strict=True
    ):
        with tab:
            if analysis is None:
                st.info(NO_ANALYSIS)
            else:
                render(analysis)
    with tabs[5]:
        _log_tab()
    with tabs[7]:
        if analysis is None:
            st.info(NO_ANALYSIS)
        else:
            _crm_tab(analysis)
    with header.container():
        ui.hero(
            "Tu equipo de expertos de IA",
            "Ve la causa de lo que pasa en tu negocio, actúa y comprueba que ha funcionado.",
            _journey(),
        )


def _journey() -> list[tuple[str, str]]:
    """Where the owner is: analyse → understand → act → measure."""
    execution: Execution = st.session_state.execution
    analysed = st.session_state.analysis is not None
    done = [
        analysed,
        analysed,
        bool(execution.sent or execution.claimed),
        st.session_state.remeasure is not None,
    ]
    labels = ["1 Analizar", "2 Entender la causa", "3 Actuar", "4 Medir"]
    current = next((i for i, d in enumerate(done) if not d), None)
    return [
        (("✓ " if d else "") + label, "done" if d else ("now" if i == current else ""))
        for i, (label, d) in enumerate(zip(labels, done, strict=True))
    ]


main()
