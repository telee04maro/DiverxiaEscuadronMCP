"""Centra demo panel. Run with: uv run streamlit run src/centra/app.py

The panel only presents; every decision lives in the agents (see centra.pipeline).
"""

from decimal import Decimal
from pathlib import Path

import streamlit as st

from centra.actions.mailer import build_mailer
from centra.audit import AuditLog
from centra.config import Settings
from centra.coordinator.plan import Autonomy, Kind, PlanItem
from centra.data.loader import load_company_data
from centra.data.model import CompanyData
from centra.data.synthetic import AFTER, BEFORE, DEMO_ROOT
from centra.domain.findings import AREA_LABELS, Area, Finding, Kpi, SpecialistReport
from centra.domain.money import fmt_eur, fmt_num
from centra.domain.priority import HORIZON_LABELS, Horizon
from centra.llm.base import LanguageModel, total_cost
from centra.llm.factory import build_model
from centra.pipeline import (
    Analysis,
    Execution,
    analyze,
    approve,
    execute_plan,
    first_paid_reference,
    inject_short_payment,
    mark_done,
    measure_after,
)
from centra.remeasure import Effect, Remeasurement

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = (
    ("Marketing y clientes", "Responde reseñas y lanza campañas"),
    ("Legal y cumplimiento", "Calendario de obligaciones y documentos; lo complejo, a un abogado"),
    ("Organización y personas", "Cuellos de botella y clima con encuesta anónima"),
    ("Atención al cliente", "El canal único por el que el dueño pide y el sistema actúa"),
)
AUTONOMY_COLOR = {
    Autonomy.AUTO: "green",
    Autonomy.APPROVAL: "orange",
    Autonomy.PERSON: "blue",
    Autonomy.EXPERT: "violet",
}
EFFECT_ICON = {
    Effect.CONFIRMED: "✅",
    Effect.PARTIAL: "🟡",
    Effect.NONE: "❌",
    Effect.NOT_DONE: "⏸️",
    Effect.NOT_MEASURABLE: "❔",
}


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
    st.session_state.execution = Execution()
    st.session_state.remeasure = None
    st.session_state.after_reports = None


def _fmt_kpi(kpi: Kpi) -> str:
    if kpi.value is None:
        return "—"
    if kpi.unit == "€":
        return fmt_eur(kpi.value.quantize(Decimal(1))).replace(",00 €", " €")
    return f"{_fmt_value(kpi.value, '')} {kpi.unit}".strip()


def _fmt_value(value: Decimal | None, unit_hint: str) -> str:
    if value is None:
        return "—"
    if unit_hint == "€":
        return fmt_eur(value)
    return fmt_num(Decimal(format(value.normalize(), "f")))


def _sidebar() -> None:
    model: LanguageModel = st.session_state.model
    with st.sidebar:
        st.markdown("## Centra")
        st.caption("Un equipo de expertos de IA para toda tu pyme, en un solo sitio.")
        st.markdown("> **Cada proveedor ve su parte. Centra ve la causa.**")
        st.divider()
        st.markdown("**Modo de IA**")
        st.caption(model.mode)
        st.markdown("**Envío de correos**")
        settings: Settings = st.session_state.settings
        st.caption(
            "SMTP al buzón de prueba"
            if settings.smtp and settings.demo_recipient
            else f"Bandeja local ({settings.outbox_dir.as_posix()}/)"
        )
        st.divider()
        st.toggle(
            "Fallo inyectado: un pago llega con 1 céntimo de menos",
            key="inject_fault",
            help="Para demostrar que Centra no da por cobrada una factura que no cuadra.",
        )
        if st.button("Reiniciar la demo", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.caption("Datos 100 % sintéticos: empresa, clientes y competidores ficticios.")


def _company_tab(data: CompanyData) -> None:
    company = data.company
    st.subheader(company.name)
    st.caption(
        f"{company.sector} · {company.city} · {company.employees} personas · "
        f"análisis a {company.analysis_date:%d/%m/%Y}"
    )
    left, right = st.columns(2)
    with left:
        st.markdown("**Entrevista inicial**")
        st.markdown("Objetivos:\n" + "\n".join(f"- {g}" for g in company.goals))
        st.markdown(f"Recursos: {company.resources}")
        st.markdown(
            "Servicios: " + ", ".join(f"{s.name} ({fmt_eur(s.price)})" for s in company.services)
        )
    with right:
        st.markdown("**Fuentes conectadas**")
        st.markdown(
            f"- Facturas: {len(data.invoices)}\n- Movimientos del banco: {len(data.bank)}\n"
            f"- Meses de sesiones: {len({s.month for s in data.sessions})}\n"
            f"- Reseñas: {len(data.reviews)}\n- Anuncios de la competencia: "
            f"{len(data.competitor_ads)}\n- Competidores: {len(data.competitors)}"
        )
        if data.missing_sources:
            st.warning("Faltan: " + ", ".join(data.missing_sources))
    st.divider()
    if st.button("Analizar con el equipo de agentes", type="primary", use_container_width=True):
        with st.spinner("Los especialistas están analizando y el coordinador cruza lo que ven…"):
            st.session_state.analysis = analyze(data, st.session_state.model, st.session_state.log)
            st.session_state.execution = Execution()
            st.session_state.remeasure = None
        st.success("Análisis listo: revisa las pestañas 2 y 3.")


def _finding_card(finding: Finding) -> None:
    with st.expander(f"**{finding.title}**  ·  confianza {finding.confidence.value}"):
        st.caption(f"{finding.id} · {finding.detail}")
        for evidence in finding.evidence:
            when = f" ({evidence.on:%d/%m/%Y})" if evidence.on else ""
            st.markdown(f"- {evidence.fact}{when}  \n  :gray[{evidence.source}]")
        st.caption(
            f"Impacto {finding.impact}/5 · urgencia {finding.urgency}/5 · "
            f"esfuerzo {finding.effort}/5"
        )


def _report_column(report: SpecialistReport) -> None:
    with st.container(border=True):
        st.markdown(f"### {report.specialist}")
        st.caption("Fuentes: " + " · ".join(report.sources))
        kpis = [k for k in report.kpis if not k.key.startswith("dias_cobro_")] or list(report.kpis)
        for row in range(0, len(kpis), 2):
            columns = st.columns(2)
            for column, kpi in zip(columns, kpis[row : row + 2], strict=False):
                column.metric(
                    kpi.label,
                    _fmt_kpi(kpi),
                    help=kpi.note or ("No disponible" if kpi.value is None else None),
                )
        st.markdown("**Hallazgos**")
        for finding in report.findings:
            _finding_card(finding)
        with st.expander("Lo que me falta para afinar"):
            for gap in report.gaps:
                st.markdown(f"- **{gap.missing}**: {gap.why_it_matters}")


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
    st.caption(f"Cómo se ha cruzado: {crossing.origin.value}")
    for cause in crossing.causes:
        with st.container(border=True):
            badge = ":red[**Causa cruzada**]" if cause.is_cross else ":gray[Causa de un área]"
            st.markdown(
                f"{badge} · {_areas_label(cause.areas)} · confianza {cause.confidence.value}"
            )
            st.markdown(f"### {cause.title}")
            st.markdown(cause.explanation)
            st.markdown("**Lo sostienen:**")
            for finding_id in cause.finding_ids:
                finding = analysis.finding(finding_id)
                if finding:
                    st.markdown(f"- :gray[{AREA_LABELS[finding.area]}] {finding.title}")
    for hypothesis in crossing.discarded:
        st.info(f"**Descartado:** {hypothesis.hypothesis}. {hypothesis.reason}")
    for note in crossing.rejected:
        st.warning(f"Rechazado por falta de evidencia: {note}")
    st.divider()
    st.markdown("## Plan")
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
                st.markdown(f"{mark} {check.reason}")


def _plan_card(item: PlanItem) -> None:
    with st.container(border=True):
        color = AUTONOMY_COLOR[item.autonomy]
        st.markdown(f"**{item.title}**")
        st.markdown(f":{color}[{item.autonomy.value}] · {item.owner}")
        st.caption(f"Por qué: {item.why}")
        if item.detail:
            st.caption(item.detail)


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
                    f"**{claim.subject}** → {claim.to}  \n:orange[Tono {claim.tone.value}] · "
                    f"{claim.origin.value} · total {fmt_eur(claim.total)}"
                )
                st.text(claim.body)
                if st.button("Aprobar y enviar", key=f"approve-{item_id}"):
                    approve(analysis, item_id, execution, mailer, log)
                    st.rerun()
    if execution.sent:
        st.markdown("### Enviado")
        for sent in execution.sent:
            with st.expander(f"✉️ {sent.claim.subject} → {sent.claim.client_name}"):
                st.caption(f"{sent.delivery} · {sent.claim.origin.value}")
                st.text(sent.claim.body)
        st.info(
            "Enviar no es cobrar: estas facturas siguen pendientes hasta que el banco lo "
            "confirme al céntimo (pestaña 5)."
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
    if not st.session_state.get("inject_fault"):
        return after
    since = st.session_state.before.company.analysis_date
    reference = first_paid_reference(after, "ASG-GAMMA", since) or first_paid_reference(
        after, "ASG-BETA", since
    )
    return inject_short_payment(after, reference) if reference else after


def _remeasure_tab(analysis: Analysis) -> None:
    st.caption(
        "«Un mes después» son datos simulados del 2/12/2026 con lo que habría pasado tras el plan."
    )
    if st.session_state.get("inject_fault"):
        st.warning("Fallo inyectado activo: un pago llega con 1 céntimo de menos.")
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
    for r in result.results:
        unit = "€" if r.item.kind is Kind.COLLECT else ""
        with st.container(border=True):
            st.markdown(
                f"{EFFECT_ICON[r.effect]} **{r.effect.value.capitalize()}** · {r.item.title}"
            )
            st.markdown(
                f"{r.kpi_label}: **{_fmt_value(r.before, unit)} → {_fmt_value(r.after, unit)}**"
            )
            st.caption(r.note)
            for check in r.invoices:
                st.markdown(
                    f"- {check.invoice_id}: {fmt_eur(check.amount)} · cobrado "
                    f"{fmt_eur(check.paid)} → **{check.status.value}**"
                )
    st.markdown("### Plan reordenado")
    for item in result.next_plan:
        st.markdown(f"- **{HORIZON_LABELS[item.horizon]}** · {item.title}")


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
            {"Hora": e.at.strftime("%H:%M:%S"), "Agente": e.agent, "Qué": e.kind.value,
             "Detalle": e.message, "Referencias": ", ".join(e.refs)}
            for e in log.events
        ],
        hide_index=True,
        use_container_width=True,
    )  # fmt: skip


def main() -> None:
    st.set_page_config(page_title="Centra", page_icon="🧭", layout="wide")
    _state()
    _sidebar()
    st.title("Centra")
    st.caption(
        "Especialistas de IA que detectan, un coordinador que cruza la información, actúa y mide."
    )
    tabs = st.tabs(
        ["1 · Empresa", "2 · Especialistas", "3 · Coordinador", "4 · Acciones",
         "5 · Un mes después", "6 · Registro y uso de IA"]
    )  # fmt: skip
    with tabs[0]:
        _company_tab(st.session_state.before)
    # Read after the company tab: its button may have just produced the analysis.
    analysis: Analysis | None = st.session_state.analysis
    for tab, render in zip(
        tabs[1:5], (_specialists_tab, _coordinator_tab, _actions_tab, _remeasure_tab), strict=True
    ):
        with tab:
            if analysis is None:
                st.info("Primero pulsa «Analizar con el equipo de agentes» en la pestaña 1.")
            else:
                render(analysis)
    with tabs[5]:
        _log_tab()


main()
