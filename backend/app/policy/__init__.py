"""
Policy analysis and scoring system for fund selection.

This package provides production-grade policy event tracking and scoring,
replacing fake MD5-based calculations with real Chinese government policy analysis.

Components:
- models: Pydantic models for policy events and sector mappings
- repository: Database operations for policy data
- scoring: Policy scoring engine with recency decay and intensity weighting
- sector_classifier: Fund sector classification for policy mapping
- seed_data: Initial realistic Chinese policy data (2024-2025)
"""

from app.policy.models import PolicyEvent, PolicyScoreBreakdown, SectorPolicyMapping
from app.policy.repository import PolicyRepository
from app.policy.scoring import PolicyScorer
from app.policy.sector_classifier import (
    classify_fund_sector,
    get_all_sectors,
    get_sector_keywords,
    is_policy_relevant_sector,
    is_sector_fund,
)

__all__ = [
    # Models
    "PolicyEvent",
    "PolicyScoreBreakdown",
    "SectorPolicyMapping",
    # Repository
    "PolicyRepository",
    # Scoring
    "PolicyScorer",
    # Classification
    "classify_fund_sector",
    "get_all_sectors",
    "get_sector_keywords",
    "is_policy_relevant_sector",
    "is_sector_fund",
]
