"""
Factor calculation and standardization for fund selection.

This package provides production-grade financial mathematics for
calculating and standardizing fund performance metrics.

Modules:
    calculator: Core factor calculation engine
    standardizer: Cross-sectional standardization utilities

Key Classes:
    FactorCalculator: Calculate return, risk, and risk-adjusted metrics
    FactorStandardizer: Standardize raw metrics to 0-100 scale
    NAVHistoryManager: Manage historical NAV data
    BenchmarkManager: Manage benchmark index data
"""

from app.factors.calculator import (
    BenchmarkManager,
    FactorCalculator,
    InsufficientDataError,
    NAVHistoryManager,
    NAVHistoryRecord,
    align_to_benchmark,
    clean_nav_data,
)
from app.factors.standardizer import (
    FactorStandardizer,
    InsufficientDataError as StandardizationError,
    calculate_factor_scores,
)

__all__ = [
    # Calculator
    "FactorCalculator",
    "NAVHistoryManager",
    "NAVHistoryRecord",
    "BenchmarkManager",
    "InsufficientDataError",
    "clean_nav_data",
    "align_to_benchmark",
    # Standardizer
    "FactorStandardizer",
    "StandardizationError",
    "calculate_factor_scores",
]
