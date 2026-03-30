"""
Policy event models for government regulatory impact analysis.

This module defines Pydantic models for representing Chinese government policies
and their impact on fund sectors. These models replace fake MD5-based policy scoring
with real policy event tracking and scoring.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PolicyEvent(BaseModel):
    """Represents a government policy/regulatory event.

    Attributes:
        policy_id: Unique policy identifier (e.g., P2025033001)
        title: Policy title
        published_at: Announcement date
        effective_from: Effective date (optional)
        expires_at: Expiration date for temporary policies (optional)
        related_sectors: Sectors affected (e.g., ['科技', '半导体', '新能源'])
        intensity_level: Policy intensity 1-5 (1=minor, 5=breakthrough)
        execution_status: Implementation status
        impact_direction: Market impact direction
        policy_type: Policy category
        support_amount_billion: Fiscal support amount in billion RMB (optional)
        tax_incentive_rate: Tax incentive rate 0-1 (optional)
        source_url: Official source URL (optional)
        description: Policy description (optional)
        key_points: Key policy points list
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    # Core identifiers
    policy_id: str = Field(..., description="Unique policy ID (e.g., P2025033001)")
    title: str = Field(..., description="Policy title")

    # Temporal data
    published_at: datetime = Field(..., description="Announcement date")
    effective_from: datetime | None = Field(None, description="Effective date")
    expires_at: datetime | None = Field(None, description="Expiration date (if temporary)")

    # Sector mapping
    related_sectors: list[str] = Field(
        ..., description="Sectors affected (e.g., ['科技', '半导体', '新能源'])"
    )

    # Impact assessment
    intensity_level: int = Field(
        ..., ge=1, le=5, description="Policy intensity (1=minor, 5=breakthrough)"
    )

    execution_status: Literal["announced", "detailed", "implementing", "completed", "cancelled"] = Field(
        default="announced", description="Implementation status"
    )

    impact_direction: Literal["positive", "negative", "neutral"] = Field(
        default="neutral", description="Market impact direction"
    )

    # Classification
    policy_type: Literal["fiscal", "monetary", "industrial", "regulatory", "reform"] = Field(
        ..., description="Policy category"
    )

    # Quantitative measures
    support_amount_billion: float | None = Field(
        None, ge=0, description="Fiscal support amount (billion RMB)"
    )

    tax_incentive_rate: float | None = Field(
        None, ge=0, le=1, description="Tax incentive rate (0-1)"
    )

    # Documentation
    source_url: str | None = Field(None, description="Official source URL")
    description: str | None = Field(None, description="Policy description")
    key_points: list[str] = Field(default_factory=list, description="Key policy points")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SectorPolicyMapping(BaseModel):
    """Maps policy events to fund sectors.

    Attributes:
        sector: Sector name (e.g., '科技', '医药', '消费')
        fund_categories: Fund categories in this sector
        related_policy_ids: Policy IDs affecting this sector
        sector_weight: Sector importance weight (0-2, default 1.0)
        benchmark_index: Benchmark index code (optional)
    """

    sector: str = Field(..., description="Sector name (e.g., '科技', '医药', '消费')")

    # Fund categories in this sector
    fund_categories: list[str] = Field(
        ..., description="Fund categories (e.g., ['半导体ETF', '科技主题基金'])"
    )

    # Related policy IDs
    related_policy_ids: list[str] = Field(
        ..., description="Policy IDs affecting this sector"
    )

    # Sector weights
    sector_weight: float = Field(
        default=1.0, ge=0, le=2, description="Sector importance weight (0-2)"
    )

    # Benchmark for this sector
    benchmark_index: str | None = Field(
        None, description="Benchmark index code (e.g., '000300.SH')"
    )


class PolicyScoreBreakdown(BaseModel):
    """Detailed breakdown of policy scores for a fund.

    Attributes:
        support_score: Policy support intensity (0-100)
        execution_score: Implementation progress (0-100)
        regulation_score: Regulatory safety (0-100)
        supporting_policies: List of positive policy IDs
        negative_policies: List of negative policy IDs
        total_policies: Total number of policies considered
        last_updated: Timestamp of score calculation
    """

    support_score: float = Field(..., ge=0, le=100, description="Policy support intensity (0-100)")
    execution_score: float = Field(..., ge=0, le=100, description="Implementation progress (0-100)")
    regulation_score: float = Field(..., ge=0, le=100, description="Regulatory safety (0-100)")
    supporting_policies: list[str] = Field(default_factory=list, description="Positive policy IDs")
    negative_policies: list[str] = Field(default_factory=list, description="Negative policy IDs")
    total_policies: int = Field(..., ge=0, description="Total policies considered")
    last_updated: datetime = Field(default_factory=datetime.now)
