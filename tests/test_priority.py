from decimal import Decimal

from vigia.domain.findings import Area, Confidence, Evidence, Finding
from vigia.domain.priority import Horizon, horizon_for, score


def _finding(impact: int, urgency: int, effort: int) -> Finding:
    return Finding(
        id="F-1",
        area=Area.FINANCE,
        title="t",
        detail="d",
        evidence=(Evidence(source="s", fact="f"),),
        confidence=Confidence.HIGH,
        impact=impact,
        urgency=urgency,
        effort=effort,
    )


def test_score_rewards_impact_and_urgency_and_penalises_effort() -> None:
    assert score(_finding(5, 5, 1)) == Decimal("25.00")
    assert score(_finding(4, 3, 3)) == Decimal("4.00")


def test_horizon_rules() -> None:
    assert horizon_for(urgency=5, effort=1) is Horizon.WEEK
    assert horizon_for(urgency=5, effort=4) is Horizon.QUARTER
    assert horizon_for(urgency=3, effort=2) is Horizon.MONTH
