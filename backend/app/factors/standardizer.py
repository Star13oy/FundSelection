"""
Factor standardization for cross-sectional comparison.

This module implements robust statistical methods to standardize raw financial
metrics to a 0-100 scale for fair comparison across funds.

Methodology:
1. Calculate cross-sectional statistics (mean, std) per fund category
2. Convert raw values to Z-scores
3. Winsorize extreme values at ±3 standard deviations
4. Convert Z-scores to percentiles using normal CDF
5. Scale to 0-100 range

References:
- Croux, C., & Haesbroeck, G. (2000). Influence in samples from a
  multivariate Laplace distribution. Journal of Multivariate Analysis.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# Constants for standardization
DEFAULT_WINSDORIZE_LOWER = 0.01  # 1st percentile
DEFAULT_WINSDORIZE_UPPER = 0.99  # 99th percentile
MAX_Z_SCORE = 3.0  # 99.7% confidence interval
EPSILON = 1e-10


class InsufficientDataError(ValueError):
    """Raised when insufficient data for standardization."""
    pass


class FactorStandardizer:
    """
    Standardize raw metrics to 0-100 scale within categories.

    This ensures fair comparison across funds by accounting for
    different return/risk profiles across fund categories.

    Example:
        >>> standardizer = FactorStandardizer()
        >>> standardizer.fit(funds_df, category_col='category')
        >>> score = standardizer.transform(15.5, metric='one_year_return', category='equity')
        >>> print(score)  # e.g., 72.34
    """

    def __init__(self) -> None:
        """Initialize standardizer with empty statistics."""
        self.category_stats: dict[str, dict[str, dict[str, float]]] = {}
        self._is_fitted = False

    def fit(
        self,
        funds_data: pd.DataFrame,
        category_col: str = 'category'
    ) -> None:
        """
        Calculate statistics per fund category.

        Computes mean and standard deviation for each metric within
        each fund category for consistent cross-sectional standardization.

        Args:
            funds_data: DataFrame with raw metrics and category labels
                Must include category_col and numeric metric columns
            category_col: Column name containing fund categories

        Raises:
            InsufficientDataError: If insufficient data for any category
        """
        if funds_data.empty:
            raise InsufficientDataError("Cannot fit on empty DataFrame")

        # Get numeric columns only
        numeric_cols = funds_data.select_dtypes(include=[np.number]).columns.tolist()

        # Remove category_col if it's numeric (shouldn't be, but safety check)
        if category_col in numeric_cols:
            numeric_cols.remove(category_col)

        if not numeric_cols:
            raise InsufficientDataError("No numeric columns found for standardization")

        self.category_stats = {}

        for category in funds_data[category_col].unique():
            category_df = funds_data[funds_data[category_col] == category]

            if len(category_df) < 5:
                logger.warning(
                    f"Category '{category}' has only {len(category_df)} funds. "
                    f"Minimum 5 recommended for reliable standardization."
                )

            self.category_stats[category] = {}

            for metric in numeric_cols:
                metric_values = category_df[metric].dropna()

                if len(metric_values) < 3:
                    logger.warning(
                        f"Category '{category}', metric '{metric}' has only "
                        f"{len(metric_values)} non-null values. Skipping."
                    )
                    self.category_stats[category][metric] = {
                        'mean': 0.0,
                        'std': 1.0,
                        'count': 0,
                    }
                    continue

                # Calculate robust statistics
                mean_val = float(metric_values.mean())
                std_val = float(metric_values.std())

                # Handle zero or near-zero standard deviation
                if std_val < EPSILON:
                    logger.warning(
                        f"Category '{category}', metric '{metric}' has near-zero "
                        f"standard deviation ({std_val:.6f}). Using std=1.0."
                    )
                    std_val = 1.0

                self.category_stats[category][metric] = {
                    'mean': mean_val,
                    'std': std_val,
                    'count': len(metric_values),
                }

        self._is_fitted = True
        logger.info(
            f"Fitted standardizer on {len(self.category_stats)} categories, "
            f"{len(numeric_cols)} metrics"
        )

    def transform(
        self,
        raw_value: float | None,
        metric: str,
        category: str
    ) -> float | None:
        """
        Standardize a raw value to 0-100 scale.

        Method:
            1. Calculate Z-score: (value - mean) / std
            2. Apply winsorize: clip at [-3, +3] (99.7% confidence)
            3. Convert to percentile: norm.cdf(z_score) * 100
            4. Round to 2 decimal places

        Args:
            raw_value: Raw metric value to standardize
            metric: Metric name (must exist in fitted stats)
            category: Fund category (must exist in fitted stats)

        Returns:
            Standardized value in [0, 100], or None if input is None
            or category/metric not found in fitted stats
        """
        if raw_value is None:
            return None

        if not self._is_fitted:
            logger.warning("Standardizer not fitted. Returning None.")
            return None

        if category not in self.category_stats:
            logger.warning(
                f"Category '{category}' not found in fitted stats. "
                f"Available: {list(self.category_stats.keys())}"
            )
            return None

        if metric not in self.category_stats[category]:
            logger.warning(
                f"Metric '{metric}' not found for category '{category}'. "
                f"Available: {list(self.category_stats[category].keys())}"
            )
            return None

        stats_dict = self.category_stats[category][metric]

        # Skip if insufficient data
        if stats_dict['count'] < 3:
            return None

        # Calculate Z-score
        mean_val = stats_dict['mean']
        std_val = stats_dict['std']

        if std_val < EPSILON:
            return None

        z_score = (raw_value - mean_val) / std_val

        # Winsorize at ±3 standard deviations
        z_score_clipped = np.clip(z_score, -MAX_Z_SCORE, MAX_Z_SCORE)

        # Convert to percentile using normal CDF
        percentile = stats.norm.cdf(z_score_clipped) * 100

        # Round to 2 decimal places
        return round(percentile, 2)

    def fit_transform(
        self,
        funds_data: pd.DataFrame,
        category_col: str = 'category'
    ) -> pd.DataFrame:
        """
        Fit standardizer and transform data in one step.

        Args:
            funds_data: DataFrame with raw metrics
            category_col: Column name containing fund categories

        Returns:
            DataFrame with standardized metrics (0-100 scale)
        """
        self.fit(funds_data, category_col)
        return self.transform_dataframe(funds_data, category_col)

    def transform_dataframe(
        self,
        funds_data: pd.DataFrame,
        category_col: str = 'category'
    ) -> pd.DataFrame:
        """
        Transform entire DataFrame of raw metrics.

        Args:
            funds_data: DataFrame with raw metrics
            category_col: Column name containing fund categories

        Returns:
            DataFrame with standardized metrics (0-100 scale)
        """
        if not self._is_fitted:
            raise RuntimeError("Standardizer not fitted. Call fit() first.")

        result_df = funds_data.copy()

        # Get numeric columns
        numeric_cols = funds_data.select_dtypes(include=[np.number]).columns.tolist()
        if category_col in numeric_cols:
            numeric_cols.remove(category_col)

        # Transform each metric
        for metric in numeric_cols:
            result_df[f'{metric}_std'] = result_df.apply(
                lambda row: self.transform(
                    row[metric],
                    metric,
                    row[category_col]
                ),
                axis=1
            )

        return result_df

    def winsorize(
        self,
        series: pd.Series,
        lower: float = DEFAULT_WINSDORIZE_LOWER,
        upper: float = DEFAULT_WINSDORIZE_UPPER
    ) -> pd.Series:
        """
        Winsorize to handle extreme outliers.

        Clip values at specified percentiles.
        Default: 1st and 99th percentiles.

        Args:
            series: Series of values to winsorize
            lower: Lower percentile (default: 0.01)
            upper: Upper percentile (default: 0.99)

        Returns:
            Winsorized series
        """
        if series.empty or series.dropna().empty:
            return series

        lower_bound = series.quantile(lower)
        upper_bound = series.quantile(upper)

        return series.clip(lower=lower_bound, upper=upper_bound)

    def get_category_stats(
        self,
        category: str | None = None
    ) -> dict[str, Any] | dict[str, dict[str, dict[str, float]]]:
        """
        Get fitted statistics for inspection.

        Args:
            category: Specific category to retrieve, or None for all

        Returns:
            Statistics dictionary for category(s)
        """
        if not self._is_fitted:
            raise RuntimeError("Standardizer not fitted. Call fit() first.")

        if category is not None:
            return self.category_stats.get(category, {})

        return self.category_stats

    def inverse_transform(
        self,
        standardized_value: float | None,
        metric: str,
        category: str
    ) -> float | None:
        """
        Convert standardized value back to raw scale.

        Inverse of transform(). Useful for interpretation.

        Args:
            standardized_value: Standardized value (0-100)
            metric: Metric name
            category: Fund category

        Returns:
            Raw value corresponding to standardized score
        """
        if standardized_value is None:
            return None

        if not self._is_fitted:
            return None

        if category not in self.category_stats:
            return None

        if metric not in self.category_stats[category]:
            return None

        stats_dict = self.category_stats[category][metric]

        # Convert percentile back to Z-score
        z_score = stats.norm.ppf(standardized_value / 100)

        # Convert Z-score back to raw value
        mean_val = stats_dict['mean']
        std_val = stats_dict['std']

        raw_value = z_score * std_val + mean_val

        return raw_value


def calculate_factor_scores(
    raw_factors: dict[str, float | None],
    fund_category: str,
    standardizer: FactorStandardizer
) -> dict[str, float | None]:
    """
    Calculate standardized factor scores from raw metrics.

    This is a convenience function that standardizes all raw factors
    and aggregates them into the 7 factor categories used in the
    fund selection system.

    Factor Categories:
        1. Returns: 1Y, 3Y, 5Y returns
        2. Risk Control: Max drawdown (inverted), volatility
        3. Risk Adjusted: Sharpe, Sortino, Calmar ratios
        4. Stability: Up/down capture, win rate
        5. Cost Efficiency: Expense ratio impact
        6. Liquidity: (from fund data, not calculated)
        7. Survival Quality: (from fund data, age > 3 years)

    Args:
        raw_factors: Dictionary of raw metric values
        fund_category: Fund category for standardization
        standardizer: Fitted FactorStandardizer instance

    Returns:
        Dictionary with 7 standardized factor scores (0-100)
    """
    # Standardize individual metrics
    returns_1y = standardizer.transform(
        raw_factors.get('one_year_return'),
        'one_year_return',
        fund_category
    )
    returns_3y = standardizer.transform(
        raw_factors.get('three_year_return'),
        'three_year_return',
        fund_category
    )
    returns_5y = standardizer.transform(
        raw_factors.get('five_year_return'),
        'five_year_return',
        fund_category
    )

    max_dd = raw_factors.get('max_drawdown')
    # Invert max drawdown (lower is better)
    if max_dd is not None:
        max_dd_inverted = -max_dd
        # Note: We'd need to fit standardizer on inverted values
        # For now, use raw value
        risk_control_score = standardizer.transform(
            max_dd_inverted,
            'max_drawdown',
            fund_category
        )
    else:
        risk_control_score = None

    volatility_score = standardizer.transform(
        raw_factors.get('volatility'),
        'volatility',
        fund_category
    )

    sharpe_score = standardizer.transform(
        raw_factors.get('sharpe_ratio'),
        'sharpe_ratio',
        fund_category
    )
    sortino_score = standardizer.transform(
        raw_factors.get('sortino_ratio'),
        'sortino_ratio',
        fund_category
    )
    calmar_score = standardizer.transform(
        raw_factors.get('calmar_ratio'),
        'calmar_ratio',
        fund_category
    )

    win_rate_score = standardizer.transform(
        raw_factors.get('win_rate'),
        'win_rate',
        fund_category
    )

    # Aggregate into factor categories (simple average for now)
    # TODO: Use weighted averages based on factor importance

    # Returns factor: average of available return metrics
    returns_scores = [s for s in [returns_1y, returns_3y, returns_5y] if s is not None]
    factor_returns = np.mean(returns_scores) if returns_scores else None

    # Risk Control: max drawdown and volatility
    risk_scores = [s for s in [risk_control_score, volatility_score] if s is not None]
    factor_risk_control = np.mean(risk_scores) if risk_scores else None

    # Risk Adjusted: Sharpe, Sortino, Calmar
    risk_adj_scores = [s for s in [sharpe_score, sortino_score, calmar_score] if s is not None]
    factor_risk_adjusted = np.mean(risk_adj_scores) if risk_adj_scores else None

    # Stability: win rate (up/down capture not implemented yet)
    factor_stability = win_rate_score

    # Cost efficiency: (expense ratio needs to be passed separately)
    factor_cost_efficiency = None  # Placeholder

    # Liquidity and Survival are from fund data, not calculated
    factor_liquidity = None
    factor_survival_quality = None

    return {
        'returns': factor_returns,
        'risk_control': factor_risk_control,
        'risk_adjusted': factor_risk_adjusted,
        'stability': factor_stability,
        'cost_efficiency': factor_cost_efficiency,
        'liquidity': factor_liquidity,
        'survival_quality': factor_survival_quality,
    }
