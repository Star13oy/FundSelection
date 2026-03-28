from app.data import FUNDS
from app.scoring import base_score, final_score, overlay_weight, policy_score, watchlist_alerts


def test_policy_score_formula() -> None:
    fund = FUNDS[0]
    score = policy_score(fund)
    assert score == round(0.4 * 70 + 0.3 * 72 + 0.3 * 86, 2)


def test_overlay_weight_by_type_and_profile() -> None:
    equity = FUNDS[0]
    etf = FUNDS[2]
    bond = FUNDS[-1]

    assert overlay_weight(equity, "保守") == 0.10
    assert overlay_weight(etf, "进取") == 0.25
    assert overlay_weight(bond, "均衡") == 0.08


def test_final_score_blend_changes_with_profile() -> None:
    fund = FUNDS[2]
    conservative, *_ = final_score(fund, "保守")
    aggressive, *_ = final_score(fund, "进取")
    assert aggressive != conservative


def test_base_score_range() -> None:
    for fund in FUNDS:
        score = base_score(fund)
        assert 0 <= score <= 100


def test_watchlist_alerts() -> None:
    high_drawdown_fund = FUNDS[2]
    alerts = watchlist_alerts(high_drawdown_fund, "均衡")
    assert any("回撤超阈值" in x for x in alerts)
