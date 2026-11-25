"""Modelo financiero de Vigía: 36 meses y cuatro escenarios (ver plan-de-negocio.md).

Uso: python docs/negocio/plan-de-negocio-modelo.py [salida.json]
Todas las cifras son hipótesis del equipo salvo el coste de la IA (medido). Dinero en Decimal.
"""

import json
import sys
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


def rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Plan:
    name: str
    price: Decimal  # precio al mes, sin IVA
    mix: Decimal  # parte de los clientes
    expert: Decimal  # coste de la revisión humana al mes


@dataclass(frozen=True)
class Scenario:
    name: str
    churn: Decimal  # bajas al mes
    gestorias_per_month: Decimal  # gestorías nuevas al mes desde GROWTH_FROM
    clients_per_gestoria: Decimal  # clientes nuevos al mes por gestoría que aún vende
    direct_per_month: Decimal  # clientes directos al mes desde GROWTH_FROM
    pilot_revenue: Decimal = Decimal(0)  # contrato menor municipal, cobrado en PILOT_END


PLANS = (
    Plan("Esencial", Decimal(79), Decimal("0.40"), Decimal(0)),
    Plan("Profesional", Decimal(149), Decimal("0.45"), Decimal(0)),
    Plan("Avanzado", Decimal(249), Decimal("0.15"), Decimal(40)),  # 1 h de asesor a 40 €/h
)
SCENARIOS = (
    Scenario("prudente", Decimal("0.05"), Decimal(1), Decimal("0.5"), Decimal(1)),
    Scenario("base", Decimal("0.03"), Decimal(2), Decimal("0.8"), Decimal(2)),
    Scenario("optimista", Decimal("0.02"), Decimal(3), Decimal("1.0"), Decimal(4)),
    Scenario(
        "base + piloto municipal",
        Decimal("0.03"),
        Decimal(2),
        Decimal("0.8"),
        Decimal(2),
        pilot_revenue=Decimal(15000),
    ),
)

MONTHS = 36
PILOT_GESTORIAS = Decimal(3)  # mes 1: tres gestorías de Málaga
PILOT_END = 3  # meses 1-3: piloto
GROWTH_FROM = PILOT_END + 1  # desde aquí: gestorías nuevas, clientes directos y marketing
FIRST_SALES_MONTH = 2  # las gestorías del piloto empiezan a traer clientes en el mes 2
GESTORIA_ACTIVE_MONTHS = 18  # cada gestoría aporta clientes durante 18 meses y se satura
GESTORIA_KEEPS = Decimal("0.30")  # comisión recurrente de la gestoría
CHANNEL_SHARE_GESTORIA = Decimal("0.75")  # para el margen medio informativo
VARIABLE_COSTS = {  # € por cliente y mes
    "IA (Claude), 3 veces lo medido": Decimal(1),
    "Infraestructura en la UE": Decimal(3),
    "Soporte y alta": Decimal(8),
    "Cobro (≈1,5 %)": Decimal(2),
}
SALARY_GROSS = Decimal(2200)  # bruto mensual por fundador
EMPLOYER_COST = Decimal("1.32")  # coste empresa ≈ bruto × 1,32 (aproximación)
FOUNDERS = 3
HIRE_AT_CLIENTS = 150
HIRE_GROSS = Decimal(1800)
FIXED_COSTS = {  # € al mes
    "Infraestructura base, dominios y herramientas": Decimal(500),
    "Gestoría propia, seguros y asesoría legal": Decimal(450),
    "Espacio (incubadora o coworking)": Decimal(300),
}
MARKETING = Decimal(1500)  # desde GROWTH_FROM
ONE_OFF = {
    "Constitución de la SL, pacto de socios y notaría": Decimal(1500),
    "Revisión legal inicial": Decimal(3000),
    "Marca (OEPM y EUIPO)": Decimal(1000),
    "Equipos": Decimal(4500),
}


def average(plans: tuple[Plan, ...], attr: str) -> Decimal:
    return sum((getattr(p, attr) * p.mix for p in plans), Decimal(0))


def founders_payroll() -> Decimal:
    return SALARY_GROSS * EMPLOYER_COST * FOUNDERS


def run(s: Scenario, plans: tuple[Plan, ...] = PLANS) -> dict[str, object]:
    price = average(plans, "price")
    variable = sum(VARIABLE_COSTS.values(), Decimal(0)) + average(plans, "expert")
    net_gestoria = price * (1 - GESTORIA_KEEPS)
    cohorts: list[tuple[int, Decimal]] = []
    by_gestoria = direct = Decimal(0)
    new_clients = marketing_spent = Decimal(0)
    cash = -sum(ONE_OFF.values(), Decimal(0))
    lowest_cash = cash
    breakeven: int | None = None
    rows = []
    for month in range(1, MONTHS + 1):
        growing = month >= GROWTH_FROM
        if month == 1:
            cohorts.append((month, PILOT_GESTORIAS))
        elif growing:
            cohorts.append((month, s.gestorias_per_month))
        selling = sum(
            (n for start, n in cohorts if month - start < GESTORIA_ACTIVE_MONTHS), Decimal(0)
        )
        from_gestorias = selling * s.clients_per_gestoria if month >= FIRST_SALES_MONTH else 0
        from_direct = s.direct_per_month if growing else Decimal(0)
        new_clients += from_gestorias + from_direct
        by_gestoria = by_gestoria * (1 - s.churn) + from_gestorias
        direct = direct * (1 - s.churn) + from_direct
        clients = by_gestoria + direct
        recurring = by_gestoria * net_gestoria + direct * price
        payroll = founders_payroll() + (
            HIRE_GROSS * EMPLOYER_COST if clients >= HIRE_AT_CLIENTS else 0
        )
        marketing = MARKETING if growing else Decimal(0)
        marketing_spent += marketing
        costs = clients * variable + payroll + sum(FIXED_COSTS.values(), Decimal(0)) + marketing
        one_off_income = s.pilot_revenue if month == PILOT_END else Decimal(0)
        result = recurring + one_off_income - costs
        cash += result
        lowest_cash = min(lowest_cash, cash)
        if breakeven is None and recurring >= costs:  # equilibrio solo con ingresos recurrentes
            breakeven = month
        rows.append(
            {
                "mes": month,
                "gestorias": float(sum((n for _, n in cohorts), Decimal(0))),
                "clientes": float(rounded(clients)),
                "ingresos": float(rounded(recurring + one_off_income)),
                "costes": float(rounded(costs)),
                "resultado": float(rounded(result)),
                "caja": float(rounded(cash)),
            }
        )
    margin_g = net_gestoria - variable
    margin_d = price - variable
    margin = margin_g * CHANNEL_SHARE_GESTORIA + margin_d * (1 - CHANNEL_SHARE_GESTORIA)
    seller = SALARY_GROSS * EMPLOYER_COST * MONTHS  # un fundador dedicado a ventas
    years = {}
    for year in (1, 2, 3):
        chunk = rows[(year - 1) * 12 : year * 12]
        years[str(year)] = {
            "ingresos": sum(float(x["ingresos"]) for x in chunk),
            "resultado": sum(float(x["resultado"]) for x in chunk),
            "clientes_fin": chunk[-1]["clientes"],
            "gestorias_fin": chunk[-1]["gestorias"],
        }
    return {
        "escenario": s.name,
        "pvp_medio": float(price),
        "coste_variable_cliente": float(variable),
        "neto_por_cliente_gestoria": float(net_gestoria),
        "contribucion_gestoria": float(margin_g),
        "contribucion_directo": float(margin_d),
        "margen_contribucion_medio": float(rounded(margin)),
        "ltv_medio": float(rounded(margin / s.churn)),
        "vida_media_meses": float(rounded(1 / s.churn)),
        "mes_equilibrio": breakeven,
        "clientes_nuevos_36m": float(rounded(new_clients)),
        "cac_marketing": float(rounded(marketing_spent / new_clients)),
        "cac_con_fundadores_comercial": float(rounded((marketing_spent + seller) / new_clients)),
        "necesidad_maxima_de_caja": float(rounded(-lowest_cash)),
        "inversion_puntual": float(sum(ONE_OFF.values(), Decimal(0))),
        "anios": years,
        "filas": rows,
    }


def sensitivity() -> list[str]:
    lines = []
    for factor in (Decimal("0.6"), Decimal("0.8"), Decimal(1), Decimal("1.2")):
        plans = tuple(replace(p, price=rounded(p.price * factor)) for p in PLANS)
        cells = []
        for churn in (Decimal("0.02"), Decimal("0.03"), Decimal("0.05")):
            o = run(replace(SCENARIOS[1], churn=churn), plans)
            cells.append(
                f"bajas {churn * 100:.0f} %: mes {o['mes_equilibrio']}"
                f" / {o['necesidad_maxima_de_caja']:.0f} €"
            )
        lines.append(f"precio ×{factor} ({average(plans, 'price'):.0f} €): " + " | ".join(cells))
    return lines


def main() -> None:
    results = [run(s) for s in SCENARIOS]
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps(results, ensure_ascii=False, indent=1))
    for o in results:
        print(f"{o['escenario']}: equilibrio en el mes {o['mes_equilibrio']},")
        print(f"  necesidad máxima de caja {o['necesidad_maxima_de_caja']:.0f} €")
    print("Sensibilidad (escenario base):", *sensitivity(), sep="\n  ")


if __name__ == "__main__":
    main()
