"""Console run of the whole demo journey: uv run python -m centra [--fallo]"""

import argparse
import sys
from pathlib import Path

from centra.actions.mailer import build_mailer
from centra.audit import AuditLog
from centra.config import Settings
from centra.data.loader import load_company_data
from centra.data.synthetic import AFTER, BEFORE, DEMO_ROOT
from centra.domain.findings import AREA_LABELS
from centra.domain.priority import HORIZON_LABELS, Horizon
from centra.llm.base import total_cost
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
from centra.remeasure import Remeasurement

SIMULATED = "Gerencia (aprobación simulada en la demo de consola)"


def _print_analysis(analysis: Analysis) -> None:
    for report in analysis.reports:
        print(f"== {report.specialist}")
        for finding in report.findings:
            print(f"   - {finding.title}")
    print("\n== Coordinador")
    for cause in analysis.crossing.causes:
        areas = " + ".join(AREA_LABELS[a] for a in cause.areas)
        print(f"   CAUSA ({areas}): {cause.title}")
    for discarded in analysis.crossing.discarded:
        print(f"   Descartado: {discarded.hypothesis}. {discarded.reason}")
    print("\n== Plan")
    for item in analysis.plan.items:
        print(f"   [{HORIZON_LABELS[item.horizon]}] {item.title} — {item.autonomy.value}")


def _print_results(execution: Execution, result: Remeasurement) -> None:
    print("\n== Acciones")
    for sent in execution.sent:
        print(f"   ✉ {sent.claim.subject} → {sent.claim.client_name} ({sent.delivery})")
    print("\n== Un mes después")
    for r in result.results:
        print(f"   {r.effect.value:>18} · {r.item.title} · {r.note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recorrido completo de la demo de Centra")
    parser.add_argument("--fallo", action="store_true", help="un pago llega con 1 céntimo de menos")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    settings = Settings.from_env()
    model, mailer, log = build_model(settings), build_mailer(settings), AuditLog()
    before = load_company_data(Path(DEMO_ROOT / BEFORE))
    after = load_company_data(Path(DEMO_ROOT / AFTER))
    print(f"IA: {model.mode}\n")
    analysis = analyze(before, model, log)
    _print_analysis(analysis)
    # The console demo simulates the manager's approvals, and says so in the log.
    execution = execute_plan(analysis, model, mailer, log, settings)
    for item_id in list(execution.pending):
        approve(analysis, item_id, execution, mailer, log, approver=SIMULATED)
    for item in analysis.plan.items:
        if item.id not in execution.claimed and item.horizon is not Horizon.QUARTER:
            mark_done(item.id, execution, log, who=SIMULATED)
    print("\n(Demo de consola: las aprobaciones de la gerencia están simuladas)")
    if args.fallo:
        reference = first_paid_reference(after, "ASG-GAMMA", before.company.analysis_date)
        if reference:
            after = inject_short_payment(after, reference)
            print(f"\n(fallo inyectado: el pago de {reference} llega con 1 céntimo de menos)")
    _, result = measure_after(analysis, after, execution, model, log)
    _print_results(execution, result)
    print(f"\nCoste de IA: {total_cost(model.calls):.4f} $ en {len(model.calls)} llamadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
