"""
Comprehensive tests for the policy scoring system.

Tests cover:
- PolicyEvent model validation
- Policy scoring calculations (support, execution, regulation)
- Sector classification
- Recency weight calculations
- Seed data functionality
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from app.policy.models import PolicyEvent, PolicyScoreBreakdown, SectorPolicyMapping
from app.policy.scoring import PolicyScorer, EXECUTION_STATUS_SCORES, POLICY_TYPE_ADJUSTMENTS
from app.policy.sector_classifier import (
    classify_fund_sector,
    get_sector_keywords,
    is_sector_fund,
    is_policy_relevant_sector,
    get_all_sectors,
)


class TestPolicyEventModel:
    """Test PolicyEvent model validation."""

    def test_valid_policy_event(self):
        """Test creating a valid policy event."""
        policy = PolicyEvent(
            policy_id="P2025010101",
            title="Test Policy",
            published_at=datetime.now(),
            related_sectors=["半导体", "科技"],
            intensity_level=5,
            execution_status="announced",
            impact_direction="positive",
            policy_type="fiscal",
            support_amount_billion=100,
        )

        assert policy.policy_id == "P2025010101"
        assert policy.intensity_level == 5
        assert len(policy.related_sectors) == 2

    def test_policy_event_intensity_validation(self):
        """Test intensity level constraints (1-5)."""
        with pytest.raises(ValueError):
            PolicyEvent(
                policy_id="P001",
                title="Invalid",
                published_at=datetime.now(),
                related_sectors=["科技"],
                intensity_level=6,  # Invalid: > 5
                execution_status="announced",
                impact_direction="positive",
                policy_type="fiscal",
            )

        with pytest.raises(ValueError):
            PolicyEvent(
                policy_id="P002",
                title="Invalid",
                published_at=datetime.now(),
                related_sectors=["科技"],
                intensity_level=0,  # Invalid: < 1
                execution_status="announced",
                impact_direction="positive",
                policy_type="fiscal",
            )

    def test_policy_event_tax_incentive_validation(self):
        """Test tax incentive rate constraints (0-1)."""
        with pytest.raises(ValueError):
            PolicyEvent(
                policy_id="P003",
                title="Invalid",
                published_at=datetime.now(),
                related_sectors=["科技"],
                intensity_level=3,
                execution_status="announced",
                impact_direction="positive",
                policy_type="fiscal",
                tax_incentive_rate=1.5,  # Invalid: > 1
            )


class TestSectorClassifier:
    """Test fund sector classification."""

    def test_classify_semiconductor_fund(self):
        """Test classifying semiconductor funds."""
        assert classify_fund_sector("半导体ETF", "行业") == "半导体"
        assert classify_fund_sector("芯片产业基金", "行业") == "半导体"
        assert classify_fund_sector("集成电路主题", "行业") == "半导体"

    def test_classify_new_energy_fund(self):
        """Test classifying new energy funds."""
        assert classify_fund_sector("光伏ETF", "行业") == "新能源"
        assert classify_fund_sector("风电产业", "行业") == "新能源"
        assert classify_fund_sector("储能主题", "行业") == "新能源"
        assert classify_fund_sector("锂电池ETF", "行业") == "新能源"

    def test_classify_broad_category_funds(self):
        """Test classifying broad category funds."""
        assert classify_fund_sector("沪深300ETF", "宽基") == "宽基"
        assert classify_fund_sector("中证500增强", "宽基") == "宽基"
        assert classify_fund_sector("国债基金", "债券") == "债券"
        assert classify_fund_sector("混合精选", "混合") == "混合"

    def test_classify_unknown_fund(self):
        """Test classifying unknown funds returns default."""
        assert classify_fund_sector("未知主题基金", "行业") == "其他"

    def test_get_sector_keywords(self):
        """Test retrieving sector keywords."""
        keywords = get_sector_keywords("半导体")
        assert "半导体" in keywords
        assert "芯片" in keywords
        assert "集成电路" in keywords

    def test_is_sector_fund(self):
        """Test checking if fund belongs to sector."""
        assert is_sector_fund("半导体ETF", "行业", "半导体") is True
        assert is_sector_fund("沪深300ETF", "宽基", "半导体") is False

    def test_is_policy_relevant_sector(self):
        """Test checking if sector is policy-relevant."""
        assert is_policy_relevant_sector("半导体") is True
        assert is_policy_relevant_sector("新能源") is True
        assert is_policy_relevant_sector("宽基") is False
        assert is_policy_relevant_sector("债券") is False

    def test_get_all_sectors(self):
        """Test retrieving all defined sectors."""
        sectors = get_all_sectors()
        assert "半导体" in sectors
        assert "新能源" in sectors
        assert "宽基" in sectors
        assert "其他" in sectors


class TestPolicyScorer:
    """Test policy scoring calculations."""

    @pytest.fixture
    def mock_db_adapter(self, mocker):
        """Mock database adapter."""
        adapter = mocker.Mock()
        return adapter

    @pytest.fixture
    def sample_policies(self):
        """Create sample policies for testing."""
        now = datetime.now()
        return [
            PolicyEvent(
                policy_id="P001",
                title="Recent Positive Policy",
                published_at=now - timedelta(days=30),
                related_sectors=["半导体"],
                intensity_level=5,
                execution_status="implementing",
                impact_direction="positive",
                policy_type="fiscal",
                support_amount_billion=100,
            ),
            PolicyEvent(
                policy_id="P002",
                title="Old Policy",
                published_at=now - timedelta(days=300),
                related_sectors=["半导体"],
                intensity_level=3,
                execution_status="completed",
                impact_direction="positive",
                policy_type="industrial",
            ),
            PolicyEvent(
                policy_id="P003",
                title="Negative Policy",
                published_at=now - timedelta(days=60),
                related_sectors=["半导体"],
                intensity_level=2,
                execution_status="announced",
                impact_direction="negative",
                policy_type="regulatory",
            ),
        ]

    def test_calculate_recency_weight(self, mock_db_adapter):
        """Test exponential recency decay."""
        scorer = PolicyScorer(mock_db_adapter)
        now = datetime.now()

        # Recent policy (< 90 days) should have high weight
        recent_weight = scorer.calculate_recency_weight(now - timedelta(days=30), now)
        assert recent_weight > 0.8

        # Old policy (> 300 days) should have low weight
        old_weight = scorer.calculate_recency_weight(now - timedelta(days=300), now)
        assert old_weight < 0.2

        # Weight should decrease with age
        recent_weight > old_weight

    def test_execution_status_scores(self):
        """Test execution status score mappings."""
        assert EXECUTION_STATUS_SCORES["announced"] == 10
        assert EXECUTION_STATUS_SCORES["detailed"] == 30
        assert EXECUTION_STATUS_SCORES["implementing"] == 60
        assert EXECUTION_STATUS_SCORES["completed"] == 100
        assert EXECUTION_STATUS_SCORES["cancelled"] == 0

    def test_policy_type_adjustments(self):
        """Test policy type adjustment scores."""
        assert POLICY_TYPE_ADJUSTMENTS["reform"] == 10  # Uncertainty reduction
        assert POLICY_TYPE_ADJUSTMENTS["regulatory"] == -5  # Compliance cost
        assert POLICY_TYPE_ADJUSTMENTS["fiscal"] == 5  # Supportive
        assert POLICY_TYPE_ADJUSTMENTS["monetary"] == 5  # Supportive
        assert POLICY_TYPE_ADJUSTMENTS["industrial"] == 0  # Neutral

    def test_calculate_support_score_with_no_policies(self, mock_db_adapter, mocker):
        """Test support score returns neutral when no policies."""
        scorer = PolicyScorer(mock_db_adapter)
        mocker.patch.object(scorer, "get_active_policies", return_value=[])

        score = scorer.calculate_support_score("半导体")
        assert score == 50.0  # Neutral score

    def test_calculate_support_score_with_policies(
        self, mock_db_adapter, mocker, sample_policies
    ):
        """Test support score calculation with sample policies."""
        scorer = PolicyScorer(mock_db_adapter)
        mocker.patch.object(scorer, "get_active_policies", return_value=sample_policies)

        score = scorer.calculate_support_score("半导体")
        assert 0 <= score <= 100
        # Recent positive high-intensity policy should boost score
        assert score > 50

    def test_calculate_execution_score_progression(
        self, mock_db_adapter, mocker, sample_policies
    ):
        """Test execution score increases with implementation progress."""
        scorer = PolicyScorer(mock_db_adapter)
        mocker.patch.object(scorer, "get_active_policies", return_value=sample_policies)

        score = scorer.calculate_execution_score("半导体")
        assert 0 <= score <= 100
        # Mix of announced, implementing, completed should give moderate score
        assert score > 30

    def test_calculate_regulation_score_balance(
        self, mock_db_adapter, mocker, sample_policies
    ):
        """Test regulation score balances positive vs negative policies."""
        scorer = PolicyScorer(mock_db_adapter)
        mocker.patch.object(scorer, "get_active_policies", return_value=sample_policies)

        score = scorer.calculate_regulation_score("半导体")
        assert 0 <= score <= 100
        # Base 60 + adjustment for 2 positive vs 1 negative
        assert score >= 60

    def test_get_active_policies_filters_cancelled(
        self, mock_db_adapter, mocker
    ):
        """Test that cancelled policies are filtered out."""
        scorer = PolicyScorer(mock_db_adapter)
        now = datetime.now()

        policies = [
            PolicyEvent(
                policy_id="P001",
                title="Active",
                published_at=now - timedelta(days=30),
                related_sectors=["半导体"],
                intensity_level=3,
                execution_status="implementing",
                impact_direction="positive",
                policy_type="fiscal",
            ),
            PolicyEvent(
                policy_id="P002",
                title="Cancelled",
                published_at=now - timedelta(days=30),
                related_sectors=["半导体"],
                intensity_level=3,
                execution_status="cancelled",  # Should be filtered
                impact_direction="positive",
                policy_type="fiscal",
            ),
        ]

        mocker.patch.object(scorer.repository, "list_policies", return_value=policies)

        active = scorer.get_active_policies("半导体")
        assert len(active) == 1
        assert active[0].policy_id == "P001"

    def test_get_active_policies_filters_expired(
        self, mock_db_adapter, mocker
    ):
        """Test that expired policies are filtered out."""
        scorer = PolicyScorer(mock_db_adapter)
        now = datetime.now()

        policies = [
            PolicyEvent(
                policy_id="P001",
                title="Active",
                published_at=now - timedelta(days=30),
                related_sectors=["半导体"],
                intensity_level=3,
                execution_status="implementing",
                impact_direction="positive",
                policy_type="fiscal",
            ),
            PolicyEvent(
                policy_id="P002",
                title="Expired",
                published_at=now - timedelta(days=30),
                expires_at=now - timedelta(days=1),  # Expired
                related_sectors=["半导体"],
                intensity_level=3,
                execution_status="implementing",
                impact_direction="positive",
                policy_type="fiscal",
            ),
        ]

        mocker.patch.object(scorer.repository, "list_policies", return_value=policies)

        active = scorer.get_active_policies("半导体")
        assert len(active) == 1
        assert active[0].policy_id == "P001"


class TestSeedData:
    """Test seed data functionality."""

    def test_seed_data_exists(self):
        """Test that seed data module exists and has policies."""
        from app.policy.seed_data import INITIAL_POLICIES, get_policy_count

        count = get_policy_count()
        assert count > 0
        assert len(INITIAL_POLICIES) == count

    def test_seed_data_policies_valid(self):
        """Test that all seed data policies are valid."""
        from app.policy.seed_data import INITIAL_POLICIES

        for policy_data in INITIAL_POLICIES:
            policy = PolicyEvent(**policy_data)
            assert policy.policy_id.startswith("P")
            assert 1 <= policy.intensity_level <= 5
            assert policy.impact_direction in ["positive", "negative", "neutral"]
            assert policy.policy_type in ["fiscal", "monetary", "industrial", "regulatory", "reform"]
            assert len(policy.related_sectors) > 0

    def test_seed_data_sectors_covered(self):
        """Test that seed data covers major sectors."""
        from app.policy.seed_data import INITIAL_POLICIES

        sectors = set()
        for policy_data in INITIAL_POLICIES:
            sectors.update(policy_data["related_sectors"])

        # Check coverage of major sectors
        assert "半导体" in sectors
        assert "新能源" in sectors
        assert len(sectors) >= 5  # At least 5 sectors covered


class TestSectorPolicyMapping:
    """Test SectorPolicyMapping model."""

    def test_valid_sector_mapping(self):
        """Test creating a valid sector mapping."""
        mapping = SectorPolicyMapping(
            sector="半导体",
            fund_categories=["半导体ETF", "芯片ETF"],
            related_policy_ids=["P001", "P002"],
            sector_weight=1.5,
            benchmark_index="399006.SZ",
        )

        assert mapping.sector == "半导体"
        assert mapping.sector_weight == 1.5
        assert len(mapping.fund_categories) == 2

    def test_sector_weight_validation(self):
        """Test sector weight constraints (0-2)."""
        with pytest.raises(ValueError):
            SectorPolicyMapping(
                sector="科技",
                fund_categories=["科技ETF"],
                related_policy_ids=["P001"],
                sector_weight=2.5,  # Invalid: > 2
            )

        with pytest.raises(ValueError):
            SectorPolicyMapping(
                sector="科技",
                fund_categories=["科技ETF"],
                related_policy_ids=["P001"],
                sector_weight=-0.1,  # Invalid: < 0
            )


class TestPolicyScoreBreakdown:
    """Test PolicyScoreBreakdown model."""

    def test_valid_score_breakdown(self):
        """Test creating a valid score breakdown."""
        breakdown = PolicyScoreBreakdown(
            support_score=75.5,
            execution_score=80.0,
            regulation_score=70.0,
            supporting_policies=["P001", "P002"],
            negative_policies=["P003"],
            total_policies=3,
        )

        assert breakdown.support_score == 75.5
        assert breakdown.total_policies == 3
        assert len(breakdown.supporting_policies) == 2

    def test_score_constraints(self):
        """Test score constraints (0-100)."""
        with pytest.raises(ValueError):
            PolicyScoreBreakdown(
                support_score=101,  # Invalid: > 100
                execution_score=50,
                regulation_score=50,
                total_policies=1,
            )

        with pytest.raises(ValueError):
            PolicyScoreBreakdown(
                support_score=-1,  # Invalid: < 0
                execution_score=50,
                regulation_score=50,
                total_policies=1,
            )
