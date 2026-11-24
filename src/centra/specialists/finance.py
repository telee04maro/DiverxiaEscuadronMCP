"""Finance specialist: cash, collections, private-patient revenue and margins. Rules only."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from centra.audit import AuditLog, EventKind
from centra.data.model import BankMovement, ClientType, CompanyData, MonthlySessions
from centra.domain.findings import (
    Area,
    Confidence,
    DataGap,
    Evidence,
    Finding,
    Kpi,
    Signal,
    SpecialistReport,
)
from centra.domain.money import fmt_eur, pct_change
from centra.finance.reconciliation import InvoiceStatus, PaymentStatus, reconcile
from centra.llm.base import LanguageModel

NAME = "Agente de finanzas"
SOURCES = ("Facturas emitidas (CSV)", "Extracto bancario (CSV)", "Sesiones por mes (CSV)")

SLOW_PAYER_DAYS = 60
RECENT_OVERDUE_DAYS = 15
TIGHT_CASH_DAYS = 30
CRITICAL_CASH_DAYS = 15
DROP_THRESHOLD_PCT = Decimal("-10")
SEASONAL_TOLERANCE_PCT = Decimal("-5")
EXPENSE_MONTHS = 3
_DAYS_PER_MONTH = Decimal(30)


@dataclass(frozen=True)
class _Cash:
    balance: Decimal | None
    monthly_expenses: Decimal | None

    @property
    def days(self) -> Decimal | None:
        if self.balance is None or not self.monthly_expenses:
            return None
        daily = self.monthly_expenses / _DAYS_PER_MONTH
        return (self.balance / daily).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


class FinanceSpecialist:
    @property
    def name(self) -> str:
        return NAME

    @property
    def area(self) -> Area:
        return Area.FINANCE

    @property
    def sources(self) -> tuple[str, ...]:
        return SOURCES

    def analyze(self, data: CompanyData, model: LanguageModel, log: AuditLog) -> SpecialistReport:
        today = data.company.analysis_date
        statuses = reconcile(data.invoices, data.bank)
        cash = _cash(data.bank, today)
        log.record(
            NAME,
            EventKind.SAW,
            f"{len(data.invoices)} facturas, {len(data.bank)} movimientos del banco y "
            f"{len(data.sessions)} registros de sesiones",
        )
        findings: list[Finding] = []
        findings.extend(_collection_findings(statuses, today, cash))
        findings.extend(_cash_findings(cash, statuses, today))
        findings.extend(_private_revenue_findings(data.sessions))
        for finding in findings:
            log.record(NAME, EventKind.DECIDED, finding.title, finding.id)
        return SpecialistReport(
            specialist=NAME,
            area=Area.FINANCE,
            sources=SOURCES,
            kpis=_kpis(data, statuses, cash, today),
            findings=tuple(findings),
            gaps=_gaps(data),
        )


def _cash(bank: tuple[BankMovement, ...], today: date) -> _Cash:
    if not bank:
        return _Cash(balance=None, monthly_expenses=None)
    balance = max(bank, key=lambda m: m.on).balance
    current = today.strftime("%Y-%m")
    spent: dict[str, Decimal] = defaultdict(Decimal)
    for movement in bank:
        month = movement.on.strftime("%Y-%m")
        if movement.amount < 0 and month < current:
            spent[month] += -movement.amount
    months = sorted(spent)[-EXPENSE_MONTHS:]
    if not months:
        return _Cash(balance=balance, monthly_expenses=None)
    average = sum((spent[m] for m in months), Decimal(0)) / len(months)
    return _Cash(balance=balance, monthly_expenses=average.quantize(Decimal("0.01")))


def overdue_by_client(
    statuses: tuple[InvoiceStatus, ...], today: date
) -> dict[str, list[InvoiceStatus]]:
    overdue: dict[str, list[InvoiceStatus]] = defaultdict(list)
    for status in statuses:
        if status.status is not PaymentStatus.PAID and status.days_overdue(today) > 0:
            overdue[status.invoice.client_id].append(status)
    return dict(overdue)


def average_days_to_pay(statuses: tuple[InvoiceStatus, ...], client_id: str) -> int | None:
    days = [
        d
        for s in statuses
        if s.invoice.client_id == client_id and (d := s.days_to_pay()) is not None
    ]
    return round(sum(days) / len(days)) if days else None


def _collection_findings(
    statuses: tuple[InvoiceStatus, ...], today: date, cash: _Cash
) -> list[Finding]:
    findings = []
    for client_id, items in sorted(overdue_by_client(statuses, today).items()):
        owed = sum((s.outstanding for s in items), Decimal(0))
        worst = max(s.days_overdue(today) for s in items)
        history = average_days_to_pay(statuses, client_id)
        name = items[0].invoice.client_name
        slow = worst > SLOW_PAYER_DAYS or (history is not None and history > SLOW_PAYER_DAYS)
        evidence = [
            Evidence(
                source="Facturas + extracto bancario",
                fact=(
                    f"{s.invoice.id}: {fmt_eur(s.invoice.amount)}, vencida hace "
                    f"{s.days_overdue(today)} días, sin cobro con su referencia en el banco"
                    if s.status is PaymentStatus.PENDING
                    else f"{s.invoice.id}: cobrados {fmt_eur(s.paid)} de "
                    f"{fmt_eur(s.invoice.amount)} ({s.status.value})"
                ),
                on=s.invoice.due,
            )
            for s in items
        ]
        if history is not None:
            evidence.append(
                Evidence(
                    source="Historial de cobros conciliado",
                    fact=f"Sus facturas cobradas tardaron de media {history} días en pagarse",
                )
            )
        share = owed / cash.monthly_expenses if cash.monthly_expenses else Decimal(0)
        findings.append(
            Finding(
                id=f"FIN-COBRO-{client_id}",
                area=Area.FINANCE,
                title=(
                    f"{name} paga a {history} días y debe {fmt_eur(owed)} vencidos"
                    if slow and history is not None
                    else f"{name} debe {fmt_eur(owed)} vencidos desde hace {worst} días"
                ),
                detail=(
                    f"{len(items)} factura(s) vencida(s); la más antigua, hace {worst} días. "
                    "No hay ningún ingreso en el banco con su referencia."
                ),
                evidence=tuple(evidence),
                confidence=Confidence.HIGH,
                impact=5 if share >= Decimal("0.3") else 3 if share >= Decimal("0.1") else 2,
                urgency=5 if worst > SLOW_PAYER_DAYS else 4 if worst > RECENT_OVERDUE_DAYS else 3,
                effort=1,
                signals=frozenset({Signal.SLOW_INSURER_PAYMENT if slow else Signal.RECENT_OVERDUE}),
            )
        )
    return findings


def _cash_findings(cash: _Cash, statuses: tuple[InvoiceStatus, ...], today: date) -> list[Finding]:
    days = cash.days
    if days is None or cash.balance is None or cash.monthly_expenses is None:
        return []
    if days >= TIGHT_CASH_DAYS:
        return []
    owed = sum(
        (s.outstanding for s in statuses if s.days_overdue(today) > 0),
        Decimal(0),
    )
    with_collections = cash.balance + owed
    days_after = (with_collections / (cash.monthly_expenses / _DAYS_PER_MONTH)).quantize(
        Decimal("1")
    )
    return [
        Finding(
            id="FIN-CAJA",
            area=Area.FINANCE,
            title=f"La caja solo cubre {days} días de gastos",
            detail=(
                f"Saldo de {fmt_eur(cash.balance)} frente a {fmt_eur(cash.monthly_expenses)} de "
                f"gasto medio al mes. Cobrar lo vencido ({fmt_eur(owed)}) la llevaría a "
                f"{days_after} días."
            ),
            evidence=(
                Evidence(source="Extracto bancario", fact=f"Saldo: {fmt_eur(cash.balance)}"),
                Evidence(
                    source="Extracto bancario",
                    fact=(
                        f"Gasto medio de los últimos {EXPENSE_MONTHS} meses: "
                        f"{fmt_eur(cash.monthly_expenses)} al mes"
                    ),
                ),
            ),
            confidence=Confidence.HIGH,
            impact=5,
            urgency=5 if days < CRITICAL_CASH_DAYS else 4,
            effort=3,
            signals=frozenset({Signal.TIGHT_CASH}),
        )
    ]


@dataclass(frozen=True)
class SessionTrend:
    recent_months: tuple[str, ...]
    base_months: tuple[str, ...]
    change_pct: Decimal | None
    last_year_change_pct: Decimal | None


def private_trend(sessions: tuple[MonthlySessions, ...]) -> SessionTrend | None:
    """Last two months against the two months four and five months earlier, and a year before."""
    by_month = {s.month: s.sessions for s in sessions if s.client_type is ClientType.PRIVATE}
    months = sorted(by_month)
    if len(months) < 6:  # noqa: PLR2004 - two recent months plus two base months and a gap
        return None
    recent = tuple(months[-2:])
    base = tuple(months[-6:-4])
    last_year_recent = tuple(_minus_year(m) for m in recent)
    last_year_base = tuple(_minus_year(m) for m in base)

    def change(after: tuple[str, ...], before: tuple[str, ...]) -> Decimal | None:
        if not all(m in by_month for m in after + before):
            return None
        return pct_change(
            Decimal(sum(by_month[m] for m in before)), Decimal(sum(by_month[m] for m in after))
        )

    return SessionTrend(
        recent_months=recent,
        base_months=base,
        change_pct=change(recent, base),
        last_year_change_pct=change(last_year_recent, last_year_base),
    )


def _minus_year(month: str) -> str:
    year, number = month.split("-")
    return f"{int(year) - 1}-{number}"


def _private_revenue_findings(sessions: tuple[MonthlySessions, ...]) -> list[Finding]:
    trend = private_trend(sessions)
    if trend is None or trend.change_pct is None or trend.change_pct > DROP_THRESHOLD_PCT:
        return []
    seasonal_known = trend.last_year_change_pct is not None
    not_seasonal = seasonal_known and trend.last_year_change_pct > SEASONAL_TOLERANCE_PCT  # type: ignore[operator]
    evidence = [
        Evidence(
            source="Sesiones por mes",
            fact=(
                f"Sesiones de particulares en {' y '.join(trend.recent_months)}: "
                f"{trend.change_pct} % frente a {' y '.join(trend.base_months)}"
            ),
        )
    ]
    if seasonal_known:
        evidence.append(
            Evidence(
                source="Sesiones por mes (año anterior)",
                fact=f"Los mismos meses del año pasado: {trend.last_year_change_pct} %",
            )
        )
    signals = {Signal.PRIVATE_PATIENTS_DROP}
    if not_seasonal:
        signals.add(Signal.NOT_SEASONAL)
    return [
        Finding(
            id="FIN-PARTICULARES",
            area=Area.FINANCE,
            title=f"Las sesiones de particulares caen un {abs(trend.change_pct)} %",
            detail=(
                "El año pasado esos meses no bajaron: no parece estacional."
                if not_seasonal
                else "Sin datos suficientes del año pasado para descartar estacionalidad."
            ),
            evidence=tuple(evidence),
            confidence=Confidence.HIGH if seasonal_known else Confidence.MEDIUM,
            impact=4,
            urgency=4,
            effort=3,
            signals=frozenset(signals),
        )
    ]


def _kpis(
    data: CompanyData, statuses: tuple[InvoiceStatus, ...], cash: _Cash, today: date
) -> tuple[Kpi, ...]:
    overdue = [s for s in statuses if s.days_overdue(today) > 0]
    trend = private_trend(data.sessions)
    main = data.company.service(data.company.main_service)
    kpis = [
        Kpi(key="caja", label="Caja disponible", value=cash.balance, unit="€"),
        Kpi(
            key="gasto_mensual", label="Gasto medio mensual", value=cash.monthly_expenses, unit="€"
        ),
        Kpi(key="dias_de_caja", label="Días de gastos cubiertos", value=cash.days, unit="días"),
        Kpi(
            key="vencido",
            label="Cobros vencidos",
            value=sum((s.outstanding for s in overdue), Decimal(0)) if data.invoices else None,
            unit="€",
            note=f"{len(overdue)} factura(s)",
        ),
        Kpi(
            key="variacion_particulares",
            label="Sesiones de particulares (últimos 2 meses)",
            value=trend.change_pct if trend else None,
            unit="%",
        ),
        Kpi(
            key="margen_servicio_principal",
            label=f"Margen por sesión ({data.company.main_service})",
            value=main.price - main.direct_cost if main else None,
            unit="€",
        ),
    ]
    for client_id in sorted({s.invoice.client_id for s in statuses}):
        days = average_days_to_pay(statuses, client_id)
        kpis.append(
            Kpi(
                key=f"dias_cobro_{client_id}",
                label=f"Días de cobro: {_client_name(statuses, client_id)}",
                value=Decimal(days) if days is not None else None,
                unit="días",
            )
        )
    return tuple(kpis)


def _client_name(statuses: tuple[InvoiceStatus, ...], client_id: str) -> str:
    return next(s.invoice.client_name for s in statuses if s.invoice.client_id == client_id)


def _gaps(data: CompanyData) -> tuple[DataGap, ...]:
    gaps = [
        DataGap(
            area=Area.FINANCE,
            missing="Calendario de impuestos y pagos futuros",
            why_it_matters="La previsión de caja no incluye pagos trimestrales que aún no se ven",
        ),
        DataGap(
            area=Area.FINANCE,
            missing="Coste de captación por canal",
            why_it_matters="Con él sabría qué campañas y ofertas atraen pacientes rentables",
        ),
    ]
    for name, why in (
        ("banco.csv", "Sin extracto no puedo calcular la caja ni confirmar cobros"),
        ("facturas.csv", "Sin facturas no puedo detectar cobros vencidos"),
        ("sesiones.csv", "Sin sesiones por mes no puedo ver la evolución de pacientes"),
    ):
        if name in data.missing_sources:
            gaps.append(DataGap(area=Area.FINANCE, missing=name, why_it_matters=why))
    if data.company.avg_sessions_per_new_patient is None:
        gaps.append(
            DataGap(
                area=Area.FINANCE,
                missing="Sesiones medias por paciente nuevo",
                why_it_matters="Sin ellas no puedo validar si una oferta de primera visita compensa",  # noqa: E501
            )
        )
    return tuple(gaps)
