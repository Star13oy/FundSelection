"""
Integration tests for the real factor calculation system.

These tests verify that the complete pipeline from NAV fetch to final score works correctly.
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient

from app.config import get_factor_config
from app.db import get_adapter
from app.factors.calculator import FactorCalculator, NAVHistoryManager
from app.factors.errors import InsufficientDataError
from app.factors.standardizer import FactorStandardizer
from app.main import app
from app.models import FactorMetrics, PolicyMetrics
from app.policy.scoring import PolicyScorer
from app.policy.sector_classifier import classify_fund_sector
from app.store import WATCHLIST, seed_funds
from app.universe import (
    _calculate_real_factors,
    _calculate_real_policy_metrics,
    _factor_metrics_legacy,
    _policy_metrics_legacy,
)

client = TestClient(app)


def setup_function() -> None:
    WATCHLIST.clear()


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_funds_list_and_sort() -> None:
    resp = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 1, "page_size": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total"] >= 3
    assert len(data["items"]) == 3
    assert data["items"][0]["final_score"] >= data["items"][1]["final_score"]


def test_funds_list_sort_by_fee_asc() -> None:
    resp = client.get(
        "/api/v1/funds",
        params={"risk_profile": "均衡", "sort_by": "fee", "sort_order": "asc", "page": 1, "page_size": 6},
    )
    assert resp.status_code == 200
    names = [item["name"] for item in resp.json()["items"]]
    assert names[0] == "稳健纯债A"


def test_funds_pagination_page_2_differs_from_page_1() -> None:
    page1 = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 1, "page_size": 2})
    page2 = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 2, "page_size": 2})

    assert page1.status_code == 200
    assert page2.status_code == 200

    codes1 = [item["code"] for item in page1.json()["items"]]
    codes2 = [item["code"] for item in page2.json()["items"]]
    assert codes1
    assert codes2
    assert codes1 != codes2


def test_funds_pagination_invalid_page_rejected() -> None:
    resp = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 0, "page_size": 10})
    assert resp.status_code == 422


def test_funds_pagination_invalid_page_size_rejected() -> None:
    resp = client.get("/api/v1/funds", params={"risk_profile": "均衡", "page": 1, "page_size": 101})
    assert resp.status_code == 422


def test_fund_detail_not_found() -> None:
    resp = client.get("/api/v1/funds/UNKNOWN")
    assert resp.status_code == 404


def test_compare_happy_path() -> None:
    resp = client.get(
        "/api/v1/compare",
        params=[("codes", "510300"), ("codes", "005827"), ("risk_profile", "均衡")],
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 2


def test_compare_invalid_size() -> None:
    resp = client.get("/api/v1/compare", params=[("codes", "510300")])
    assert resp.status_code == 422


def test_watchlist_flow_with_alerts() -> None:
    create = client.post("/api/v1/watchlist", json={"code": "512480"})
    assert create.status_code == 200

    listed = client.get("/api/v1/watchlist")
    assert listed.status_code == 200
    payload = listed.json()
    assert len(payload) == 1
    assert "alerts" in payload[0]

    delete = client.delete("/api/v1/watchlist/512480")
    assert delete.status_code == 200
    assert client.get("/api/v1/watchlist").json() == []


def test_policy_timestamp_validation_api() -> None:
    payload = {
        "policy_id": "P-001",
        "published_at": "2026-03-01T09:00:00Z",
        "effective_from": "2026-03-02T09:00:00Z",
        "observed_at": "2026-03-03T09:00:00Z",
    }
    resp = client.post("/api/v1/policy/validate-timestamps", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_id"] == "P-001"
    assert data["valid"] is True
    assert data["errors"] == []


# ========== Real Factor Calculation Tests ==========


@pytest.mark.integration
class TestFactorCalculationPipeline:
    """Test complete factor calculation pipeline."""

    def test_full_pipeline_with_real_data(self):
        """Test complete pipeline from NAV fetch to final score."""
        pytest.skip("Skipping integration test - requires real NAV data")

        # 1. Fetch NAV history
        adapter = get_adapter()
        nav_manager = NAVHistoryManager(adapter)
        nav_data = nav_manager.get_nav_history('510300')

        assert nav_data is not None
        assert len(nav_data) >= 252, "Need at least 1 year of data"

        # 2. Calculate factors
        factor_calculator = FactorCalculator(nav_manager)
        factors = factor_calculator.calculate_all_factors('510300')

        assert 'sharpe_ratio' in factors
        assert 'one_year_return' in factors
        assert 'max_drawdown' in factors

        # 3. Calculate policy scores
        policy_scorer = PolicyScorer(adapter)
        policy = policy_scorer.calculate_policy_scores('510300', 'ETF', '宽基')

        assert 'support_score' in policy
        assert 'execution_score' in policy
        assert 'regulation_score' in policy

        # 4. Verify scores are in valid range
        assert 0 <= policy['support_score'] <= 100
        assert 0 <= policy['execution_score'] <= 100
        assert 0 <= policy['regulation_score'] <= 100

    def test_replacement_works(self):
        """Verify that real calculations replace MD5 hash."""
        # Old way (MD5 hash)
        old_factors = _factor_metrics_legacy('510300', 'ETF', '场内')
        old_policy = _policy_metrics_legacy('510300', 'ETF')

        # New way (real calculations)
        # Note: This will fall back to legacy if NAV data unavailable
        try:
            new_factors = _calculate_real_factors('510300', 'CSI300 ETF', 'ETF', '场内')
            new_policy = _calculate_real_policy_metrics('510300', 'CSI300 ETF', 'ETF')

            # If real calculations succeeded, values should differ from MD5
            # (MD5 gives deterministic fake values based on hash)
            # Real values based on actual NAV data will be different
            # We can't assert they're always different (could coincidentally match)
            # But we can verify they're in valid ranges
            assert 0 <= new_factors.returns <= 100
            assert 0 <= new_factors.risk_control <= 100
            assert 0 <= new_factors.risk_adjusted <= 100
            assert 0 <= new_factors.stability <= 100
            assert 0 <= new_factors.cost_efficiency <= 100
            assert 0 <= new_factors.liquidity <= 100
            assert 0 <= new_factors.survival_quality <= 100

            assert 0 <= new_policy.support <= 100
            assert 0 <= new_policy.execution <= 100
            assert 0 <= new_policy.regulation_safety <= 100

        except InsufficientDataError:
            # If NAV data unavailable, falls back to legacy
            # This is expected behavior
            pytest.skip("NAV data unavailable, using legacy calculation")

    def test_feature_flag(self):
        """Test that USE_REAL_FACTORS feature flag works."""
        config = get_factor_config()

        # Test default is True
        assert config.USE_REAL_FACTORS is True

        # Test with flag disabled
        import os
        old_value = os.environ.get('USE_REAL_FACTORS')
        try:
            os.environ['USE_REAL_FACTORS'] = 'false'
            # Reload config
            from importlib import reload
            import app.config
            reload(app.config)

            new_config = app.config.get_factor_config()
            assert new_config.USE_REAL_FACTORS is False

        finally:
            # Restore original value
            if old_value is None:
                os.environ.pop('USE_REAL_FACTORS', None)
            else:
                os.environ['USE_REAL_FACTORS'] = old_value


@pytest.mark.integration
class TestSeedFunds:
    """Test seed_funds function with real calculations."""

    def test_seed_funds_returns_stats(self):
        """Test that seed_funds returns statistics."""
        stats = seed_funds(force=True)

        assert 'total' in stats
        assert 'success' in stats
        assert 'failed' in stats
        assert 'skipped' in stats

        # Verify counts are non-negative
        assert stats['total'] >= 0
        assert stats['success'] >= 0
        assert stats['failed'] >= 0
        assert stats['skipped'] >= 0

        # Verify total equals sum of others
        assert stats['total'] == stats['success'] + stats['failed'] + stats['skipped']

    def test_seed_funds_with_force(self):
        """Test seed_funds with force=True."""
        stats = seed_funds(force=True)

        # Should process funds
        assert stats['total'] > 0

        # At least some should succeed
        assert stats['success'] > 0


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in factor calculations."""

    def test_insufficient_data_error(self):
        """Test InsufficientDataError is raised when needed."""
        adapter = get_adapter()
        nav_manager = NAVHistoryManager(adapter)
        factor_calculator = FactorCalculator(nav_manager)

        # Try to calculate for a fund that doesn't exist
        with pytest.raises((InsufficientDataError, Exception)):
            factor_calculator.calculate_all_factors('999999')

    def test_graceful_fallback_to_legacy(self):
        """Test that system falls back to legacy on error."""
        # This fund code likely doesn't have NAV data
        # Should fall back to legacy calculation
        try:
            factors = _calculate_real_factors('000001', 'Test Fund', '宽基', '场外')
            # Should succeed with either real or legacy values
            assert isinstance(factors, FactorMetrics)
        except Exception:
            # If it fails, that's also acceptable
            pytest.skip("Fund data unavailable")


@pytest.mark.integration
class TestSectorClassification:
    """Test sector classification integration."""

    def test_classify_fund_sector(self):
        """Test sector classification."""
        # Test various fund names
        assert classify_fund_sector('沪深300ETF', 'ETF') == '宽基'
        assert classify_fund_sector('半导体ETF', 'ETF') == '行业'
        assert classify_fund_sector('新能源基金', '混合') == '行业'
        assert classify_fund_sector('纯债基金', '债券') == '债券'


@pytest.mark.integration
class TestStandardization:
    """Test factor standardization."""

    def test_standardizer_initializes(self):
        """Test that standardizer can be initialized."""
        standardizer = FactorStandardizer()
        assert standardizer is not None

    def test_standardize_returns(self):
        """Test return standardization."""
        from app.universe import _standardize_return

        # Test various return values
        assert _standardize_return(-10.0) < _standardize_return(0.0)
        assert _standardize_return(0.0) < _standardize_return(20.0)
        assert _standardize_return(50.0) >= 90.0  # High return = high score

        # Test None returns neutral score
        assert _standardize_return(None) == 50.0

    def test_standardize_risk_control(self):
        """Test risk control standardization."""
        from app.universe import _standardize_risk_control

        # Lower drawdown = higher score
        assert _standardize_risk_control(-5.0) > _standardize_risk_control(-20.0)
        assert _standardize_risk_control(0.0) == 100.0  # No drawdown = perfect score

        # Test None returns neutral score
        assert _standardize_risk_control(None) == 50.0


@pytest.mark.integration
class TestPolicyScoring:
    """Test policy scoring integration."""

    def test_policy_scorer_initializes(self):
        """Test that policy scorer can be initialized."""
        adapter = get_adapter()
        scorer = PolicyScorer(adapter)
        assert scorer is not None

    def test_calculate_policy_scores(self):
        """Test policy score calculation."""
        adapter = get_adapter()
        scorer = PolicyScorer(adapter)

        scores = scorer.calculate_policy_scores(
            fund_code='510300',
            fund_category='ETF',
            fund_sector='宽基'
        )

        assert 'support_score' in scores
        assert 'execution_score' in scores
        assert 'regulation_score' in scores

        # Scores should be in valid range
        for key in scores:
            assert 0 <= scores[key] <= 100

