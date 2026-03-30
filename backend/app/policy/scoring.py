"""
Policy scoring engine for quantifying government policy impact on funds.

This module implements rigorous policy scoring methodology, replacing fake MD5-based
calculations with real policy event analysis. Scores are calculated using weighted
recency decay and intensity-based aggregation.

Methodology:
- Support Score: Measures policy support intensity with exponential recency decay
- Execution Score: Tracks implementation progress of announced policies
- Regulation Score: Assesses regulatory safety and policy direction balance
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from math import exp

from app.policy.models import PolicyEvent, PolicyScoreBreakdown
from app.policy.repository import PolicyRepository

logger = logging.getLogger(__name__)

# Recency decay parameters
RECENCY_DECAY_DAYS = 180  # Half-life for policy weight decay
MAX_LOOKBACK_DAYS = 365  # Maximum lookback period for policy analysis

# Execution status scores
EXECUTION_STATUS_SCORES = {
    "announced": 10,
    "detailed": 30,
    "implementing": 60,
    "completed": 100,
    "cancelled": 0,
}

# Policy type adjustments for regulation score
POLICY_TYPE_ADJUSTMENTS = {
    "reform": 10,  # Uncertainty reduction bonus
    "regulatory": -5,  # Compliance cost penalty
    "fiscal": 5,  # Supportive bonus
    "monetary": 5,  # Supportive bonus
    "industrial": 0,  # Neutral
}


class PolicyScorer:
    """Calculate policy impact scores for funds.

    This scorer analyzes policy events and produces three dimension scores:
    - Support Score: Policy support intensity (0-100)
    - Execution Score: Implementation progress (0-100)
    - Regulation Score: Regulatory safety (0-100)
    """

    def __init__(self, db_adapter):
        """
        Initialize policy scorer.

        Args:
            db_adapter: Database adapter instance
        """
        self.db = db_adapter
        self.repository = PolicyRepository(db_adapter)

    def calculate_policy_scores(
        self, fund_code: str, fund_category: str, fund_sector: str
    ) -> PolicyScoreBreakdown:
        """
        Calculate all three policy dimension scores for a fund.

        Args:
            fund_code: Fund code
            fund_category: Fund category
            fund_sector: Fund sector (e.g., '半导体', '新能源')

        Returns:
            PolicyScoreBreakdown with all three scores and metadata
        """
        logger.info(f"Calculating policy scores for fund {fund_code} (sector: {fund_sector})")

        # Calculate individual scores
        support_score = self.calculate_support_score(fund_sector)
        execution_score = self.calculate_execution_score(fund_sector)
        regulation_score = self.calculate_regulation_score(fund_sector)

        # Get supporting and negative policies for context
        active_policies = self.get_active_policies(fund_sector)
        supporting_policies = [p.policy_id for p in active_policies if p.impact_direction == "positive"]
        negative_policies = [p.policy_id for p in active_policies if p.impact_direction == "negative"]

        breakdown = PolicyScoreBreakdown(
            support_score=support_score,
            execution_score=execution_score,
            regulation_score=regulation_score,
            supporting_policies=supporting_policies,
            negative_policies=negative_policies,
            total_policies=len(active_policies),
        )

        logger.info(
            f"Policy scores for {fund_code}: "
            f"support={support_score:.1f}, execution={execution_score:.1f}, "
            f"regulation={regulation_score:.1f}"
        )

        return breakdown

    def calculate_support_score(self, fund_sector: str, lookback_days: int = MAX_LOOKBACK_DAYS) -> float:
        """
        Calculate policy support intensity score.

        Methodology:
        1. Fetch all active policies for the sector in lookback period
        2. Weight by recency (exponential decay: e^(-age/180))
        3. Weight by intensity level (1-5)
        4. Weight by direction (positive=1.0, neutral=0.5, negative=0.0)
        5. Aggregate weighted sum
        6. Normalize to 0-100 scale

        Formula:
        score = Σ (intensity * direction * recency_weight) / max_possible_score * 100

        Args:
            fund_sector: Sector to analyze
            lookback_days: Days to look back for policies (default 365)

        Returns:
            Support score 0-100
        """
        policies = self.get_active_policies(fund_sector, lookback_days)

        if not policies:
            logger.warning(f"No active policies found for sector: {fund_sector}")
            return 50.0  # Neutral score when no policies

        current_date = datetime.now()
        weighted_sum = 0.0
        max_possible_score = 0.0

        for policy in policies:
            # Calculate recency weight
            recency_weight = self.calculate_recency_weight(policy.published_at, current_date)

            # Direction multiplier
            direction_multiplier = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}[
                policy.impact_direction
            ]

            # Weighted score
            weighted_score = policy.intensity_level * direction_multiplier * recency_weight
            weighted_sum += weighted_score

            # Maximum possible if all were positive and recent
            max_possible_score += 5.0 * 1.0 * 1.0  # max intensity * positive * recent

        # Normalize to 0-100
        score = (weighted_sum / max_possible_score) * 100 if max_possible_score > 0 else 50.0
        return round(max(0.0, min(100.0, score)), 2)

    def calculate_execution_score(self, fund_sector: str, lookback_days: int = MAX_LOOKBACK_DAYS) -> float:
        """
        Calculate policy implementation progress score.

        Methodology:
        1. Fetch all policies for the sector
        2. Score by execution status (announced=10, detailed=30, implementing=60, completed=100)
        3. Weight by recency and intensity
        4. Aggregate and normalize to 0-100

        Higher score = more policies are actually being implemented.

        Args:
            fund_sector: Sector to analyze
            lookback_days: Days to look back for policies (default 365)

        Returns:
            Execution score 0-100
        """
        policies = self.get_active_policies(fund_sector, lookback_days)

        if not policies:
            return 50.0  # Neutral when no policies

        current_date = datetime.now()
        weighted_sum = 0.0
        max_possible_score = 0.0

        for policy in policies:
            # Execution status score
            status_score = EXECUTION_STATUS_SCORES[policy.execution_status]

            # Recency weight
            recency_weight = self.calculate_recency_weight(policy.published_at, current_date)

            # Intensity weight (more intense policies matter more)
            intensity_weight = policy.intensity_level / 5.0

            # Weighted score
            weighted_score = status_score * recency_weight * intensity_weight
            weighted_sum += weighted_score

            # Maximum possible (completed, recent, high intensity)
            max_possible_score += 100.0 * 1.0 * 1.0

        # Normalize to 0-100
        score = (weighted_sum / max_possible_score) * 100 if max_possible_score > 0 else 50.0
        return round(max(0.0, min(100.0, score)), 2)

    def calculate_regulation_score(self, fund_sector: str) -> float:
        """
        Calculate regulatory safety score.

        Methodology:
        1. Count positive vs negative policies in last 365 days
        2. Calculate ratio: positive / (positive + negative)
        3. Adjust for policy type (reform +10, regulatory -5, fiscal/monetary +5)
        4. Add base score of 60
        5. Clip to 0-100 range

        Higher score = safer regulatory environment.

        Args:
            fund_sector: Sector to analyze

        Returns:
            Regulation score 0-100
        """
        policies = self.get_active_policies(fund_sector, MAX_LOOKBACK_DAYS)

        if not policies:
            return 60.0  # Base score when no policies

        # Count positive and negative policies
        positive_count = sum(1 for p in policies if p.impact_direction == "positive")
        negative_count = sum(1 for p in policies if p.impact_direction == "negative")

        # Calculate positive ratio (0-1)
        total_directional = positive_count + negative_count
        positive_ratio = positive_count / total_directional if total_directional > 0 else 0.5

        # Policy type adjustment
        type_adjustment_sum = sum(
            POLICY_TYPE_ADJUSTMENTS.get(p.policy_type, 0) for p in policies
        )
        avg_type_adjustment = type_adjustment_sum / len(policies) if policies else 0

        # Calculate score
        base_score = 60.0
        positive_bonus = positive_ratio * 30.0  # Max 30 points for positive policies
        type_bonus = avg_type_adjustment  # Policy type adjustment

        score = base_score + positive_bonus + type_bonus
        return round(max(0.0, min(100.0, score)), 2)

    def get_active_policies(self, sector: str, lookback_days: int = MAX_LOOKBACK_DAYS) -> list[PolicyEvent]:
        """
        Fetch active policies for a sector.

        Filters:
        - related_sectors contains sector
        - published_at >= (now - lookback_days)
        - execution_status != 'cancelled'
        - (expires_at is None OR expires_at > now)

        Args:
            sector: Sector name
            lookback_days: Days to look back (default 365)

        Returns:
            List of PolicyEvent sorted by published_at DESC
        """
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        current_date = datetime.now()

        # Fetch all policies in the lookback period
        policies = self.repository.list_policies(sector=sector, start_date=cutoff_date)

        # Filter for active policies
        active_policies = []
        for policy in policies:
            # Skip cancelled policies
            if policy.execution_status == "cancelled":
                continue

            # Skip expired policies
            if policy.expires_at and policy.expires_at < current_date:
                continue

            # Ensure sector is in related_sectors
            if sector not in policy.related_sectors:
                continue

            active_policies.append(policy)

        # Sort by published_at DESC
        active_policies.sort(key=lambda p: p.published_at, reverse=True)

        return active_policies

    def calculate_recency_weight(self, policy_date: datetime, current_date: datetime) -> float:
        """
        Calculate recency weight with exponential decay.

        Formula: exp(-age_days / 180)

        Policies from 6+ months ago have minimal weight.
        Recent policies (<3 months) have high weight.

        Args:
            policy_date: Policy publication date
            current_date: Current date for weight calculation

        Returns:
            Recency weight 0-1
        """
        age_days = (current_date - policy_date).days
        weight = exp(-age_days / RECENCY_DECAY_DAYS)
        return round(weight, 4)
