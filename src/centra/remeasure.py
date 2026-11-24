"""One month later: did the indicators move? An action counts as done only if its effect shows.

Collections are checked invoice by invoice against the bank (to the cent). Other actions are
checked through their target indicator; a move in the expected direction is reported as
"coincides", because timing alone does not prove the action caused it.
"""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from centra.audit import AuditLog, EventKind
from centra.coordinator.plan import Direction, Kind, Plan, PlanItem
from centra.data.model import CompanyData
from centra.domain.findings import SpecialistReport
from centra.domain.priority import Horizon
from centra.finance.reconciliation import InvoiceStatus, PaymentStatus, reconcile

NAME = "Agente coordinador"


class Effect(StrEnum):
    CONFIRMED = "efecto comprobado"
    PARTIAL = "efecto parcial"
    NONE = "sin efecto"
    NOT_DONE = "no se ejecutó"
    NOT_MEASURABLE = "aún no medible"


class InvoiceCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_id: str
    amount: Decimal
    paid: Decimal
    status: PaymentStatus


class ItemResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    item: PlanItem
    effect: Effect
    kpi_label: str
    before: Decimal | None
    after: Decimal | None
    note: str
    invoices: tuple[InvoiceCheck, ...] = ()


class Remeasurement(BaseModel):
    model_config = ConfigDict(frozen=True)

    results: tuple[ItemResult, ...]
    next_plan: tuple[PlanItem, ...]


def _kpi(reports: tuple[SpecialistReport, ...], key: str) -> tuple[str, Decimal | None]:
    for report in reports:
        kpi = report.kpi(key)
        if kpi is not None:
            return kpi.label, kpi.value
    return key, None


def remeasure(
    plan: Plan,
    *,
    before: tuple[SpecialistReport, ...],
    after: tuple[SpecialistReport, ...],
    after_data: CompanyData,
    claimed: dict[str, tuple[str, ...]],
    log: AuditLog,
) -> Remeasurement:
    """``claimed`` maps each executed plan item to the invoices it claimed (empty if none)."""
    statuses = {s.invoice.id: s for s in reconcile(after_data.invoices, after_data.bank)}
    results = []
    for item in plan.items:
        if item.id not in claimed:
            label, value = _kpi(after, item.target_kpi)
            results.append(
                ItemResult(
                    item=item,
                    effect=Effect.NOT_DONE,
                    kpi_label=label,
                    before=_kpi(before, item.target_kpi)[1],
                    after=value,
                    note="No se ejecutó o no se aprobó: no se puede atribuir ningún cambio",
                )
            )
        elif item.kind is Kind.COLLECT:
            results.append(_collection_result(item, claimed[item.id], statuses))
        else:
            results.append(_kpi_result(item, before, after))
    for result in results:
        log.record(
            NAME, EventKind.CHECKED, f"{result.item.title}: {result.effect.value}", result.item.id
        )
    return Remeasurement(results=tuple(results), next_plan=_reorder(results))


def _collection_result(
    item: PlanItem, invoice_ids: tuple[str, ...], statuses: dict[str, InvoiceStatus]
) -> ItemResult:
    checks = tuple(
        InvoiceCheck(
            invoice_id=invoice_id,
            amount=statuses[invoice_id].invoice.amount,
            paid=statuses[invoice_id].paid,
            status=statuses[invoice_id].status,
        )
        for invoice_id in invoice_ids
        if invoice_id in statuses
    )
    paid = sum(1 for c in checks if c.status is PaymentStatus.PAID)
    if checks and paid == len(checks):
        effect, note = Effect.CONFIRMED, "Todas las facturas reclamadas cuadran con el banco"
    elif paid:
        effect, note = Effect.PARTIAL, f"Cobradas al céntimo {paid} de {len(checks)} facturas"
    else:
        effect, note = Effect.NONE, "Ninguna factura reclamada aparece cobrada en el banco"
    short = [c for c in checks if c.status is PaymentStatus.PARTIAL]
    if short:
        note += f". {len(short)} pago(s) incompleto(s): no se dan por cobrados"
    outstanding = sum(
        (c.amount - c.paid for c in checks if c.status is not PaymentStatus.PAID), Decimal(0)
    )
    return ItemResult(
        item=item,
        effect=effect,
        kpi_label="Pendiente de lo reclamado",
        before=sum((c.amount for c in checks), Decimal(0)),
        after=outstanding,
        note=note,
        invoices=checks,
    )


def _kpi_result(
    item: PlanItem, before: tuple[SpecialistReport, ...], after: tuple[SpecialistReport, ...]
) -> ItemResult:
    label, old = _kpi(before, item.target_kpi)
    _, new = _kpi(after, item.target_kpi)
    if old is None or new is None:
        effect, note = Effect.NOT_MEASURABLE, "Falta el dato antes o después"
    elif new == old:
        effect, note = Effect.NONE, "El indicador no se ha movido"
    elif (new > old) == (item.expected is Direction.UP):
        effect = Effect.CONFIRMED
        note = "Se movió en la dirección esperada (coincide en el tiempo; no prueba la causa)"
    else:
        effect, note = Effect.NONE, "Se movió en contra de lo esperado"
    return ItemResult(item=item, effect=effect, kpi_label=label, before=old, after=new, note=note)


def _reorder(results: list[ItemResult]) -> tuple[PlanItem, ...]:
    """Done items leave the plan; what did not work comes back this week."""
    next_items = []
    for result in results:
        if result.effect is Effect.CONFIRMED:
            continue
        item = result.item
        if result.effect in {Effect.NONE, Effect.PARTIAL}:
            item = item.model_copy(
                update={"horizon": Horizon.WEEK, "title": f"Insistir: {item.title}"}
            )
        next_items.append(item)
    return tuple(sorted(next_items, key=lambda i: (i.horizon, -i.score)))
