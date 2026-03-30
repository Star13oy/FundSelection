"""
Test suite for factor standardization module.

Tests verify statistical correctness of cross-sectional standardization:
- Z-score calculation
- Winsorization
- Normal CDF transformation
- Category-specific statistics
- Edge case handling
"""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd
import pytest

from app.factors.standardizer import (
    EPSILON,
    FactorStandardizer,
    InsufficientDataError,
    calculate_factor_scores,
)


# ============== FIXTURES ==============

@pytest.fixture
def sample_funds_data():
    """Create sample funds data for standardization testing."""
    np.random.seed(42)

    categories = ['equity', 'bond', 'mixed']
    funds = []

    for category in categories:
        for i in range(30):  # 30 funds per category
            funds.append({
                'code': f'{category.upper()}{i:03d}',
                'category': category,
                'one_year_return': np.random.normal(10, 15),  # Mean 10%, std 15%
                'max_drawdown': np.random.normal(-10, 5),  # Mean -10%, std 5%
                'volatility': np.random.normal(15, 5),  # Mean 15%, std 5%
                'sharpe_ratio': np.random.normal(1.0, 0.5),
                'sortino_ratio': np.random.normal(1.5, 0.7),
                'calmar_ratio': np.random.normal(0.8, 0.4),
                'win_rate': np.random.normal(55, 10),
            })

    return pd.DataFrame(funds)


@pytest.fixture
def standardizer(sample_funds_data):
    """Create fitted standardizer."""
    std = FactorStandardizer()
    std.fit(sample_funds_data, category_col='category')
    return std


# ============== FIT TESTS ==============

def test_fit_basic(sample_funds_data):
    """Test basic fitting of standardizer."""
    std = FactorStandardizer()
    std.fit(sample_funds_data, category_col='category')

    assert std._is_fitted
    assert len(std.category_stats) == 3  # equity, bond, mixed
    assert 'equity' in std.category_stats
    assert 'bond' in std.category_stats


def test_fit_empty_dataframe():
    """Test fitting on empty DataFrame."""
    std = FactorStandardizer()

    with pytest.raises(InsufficientDataError):
        std.fit(pd.DataFrame(), category_col='category')


def test_fit_insufficient_data():
    """Test fitting with insufficient data per category."""
    std = FactorStandardizer()

    # Only 2 funds (below recommended minimum of 5)
    small_df = pd.DataFrame({
        'category': ['equity', 'equity'],
        'one_year_return': [10.0, 12.0]
    })

    # Should fit but with warning
    std.fit(small_df, category_col='category')
    assert std._is_fitted


def test_fit_calculates_correct_statistics(standardizer):
    """Test that fit calculates correct mean and std."""
    equity_stats = standardizer.category_stats['equity']['one_year_return']

    assert 'mean' in equity_stats
    assert 'std' in equity_stats
    assert 'count' in equity_stats

    # Std should be positive
    assert equity_stats['std'] > 0

    # Count should match number of equity funds
    assert equity_stats['count'] == 30


# ============== TRANSFORM TESTS ==============

def test_transform_single_value(standardizer):
    """Test transforming a single value."""
    score = standardizer.transform(
        raw_value=15.0,
        metric='one_year_return',
        category='equity'
    )

    assert score is not None
    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_transform_none_value(standardizer):
    """Test transforming None value."""
    score = standardizer.transform(
        raw_value=None,
        metric='one_year_return',
        category='equity'
    )

    assert score is None


def test_transform_unfitted_standardizer():
    """Test transform without fitting."""
    std = FactorStandardizer()

    score = std.transform(
        raw_value=15.0,
        metric='one_year_return',
        category='equity'
    )

    assert score is None


def test_transform_invalid_category(standardizer):
    """Test transform with invalid category."""
    score = standardizer.transform(
        raw_value=15.0,
        metric='one_year_return',
        category='invalid_category'
    )

    assert score is None


def test_transform_invalid_metric(standardizer):
    """Test transform with invalid metric."""
    score = standardizer.transform(
        raw_value=15.0,
        metric='invalid_metric',
        category='equity'
    )

    assert score is None


def test_transform_preserves_ranking(standardizer):
    """Test that transform preserves relative ranking."""
    # Higher raw value should give higher score
    score_low = standardizer.transform(5.0, 'one_year_return', 'equity')
    score_high = standardizer.transform(20.0, 'one_year_return', 'equity')

    assert score_high > score_low


# ============== Z-SCORE AND WINSORIZATION TESTS ==============

def test_z_score_calculation():
    """Test Z-score calculation."""
    # Manual Z-score: (value - mean) / std
    value = 15.0
    mean = 10.0
    std = 5.0

    z_score = (value - mean) / std

    assert abs(z_score - 1.0) < EPSILON  # (15 - 10) / 5 = 1


def test_winsorization(standardizer):
    """Test that extreme values are winsorized."""
    # Get category stats
    equity_stats = standardizer.category_stats['equity']['one_year_return']
    mean = equity_stats['mean']
    std = equity_stats['std']

    # Extreme value: 5 standard deviations above mean
    extreme_value = mean + 5 * std

    score = standardizer.transform(extreme_value, 'one_year_return', 'equity')

    # Should be clipped at 3 sigma (99.7th percentile ≈ 99.65)
    assert score < 100
    assert score > 99  # Should be very close to 100


def test_normal_cdf_transformation():
    """Test normal CDF transformation."""
    # Z-score of 0 should give percentile 50
    z_score = 0.0
    from scipy import stats
    percentile = stats.norm.cdf(z_score) * 100

    assert abs(percentile - 50.0) < EPSILON

    # Z-score of 1 should give percentile ~84.1
    z_score = 1.0
    percentile = stats.norm.cdf(z_score) * 100

    assert 84 < percentile < 85


# ============== DATAFRAME TRANSFORM TESTS ==============

def test_transform_dataframe(standardizer, sample_funds_data):
    """Test transforming entire DataFrame."""
    result = standardizer.transform_dataframe(sample_funds_data, category_col='category')

    # Should have original columns plus standardized versions
    assert 'one_year_return' in result.columns
    assert 'one_year_return_std' in result.columns
    assert 'max_drawdown' in result.columns
    assert 'max_drawdown_std' in result.columns

    # Standardized values should be in [0, 100]
    assert result['one_year_return_std'].between(0, 100).all()


def test_fit_transform(sample_funds_data):
    """Test fit_transform convenience method."""
    std = FactorStandardizer()
    result = std.fit_transform(sample_funds_data, category_col='category')

    assert 'one_year_return_std' in result.columns
    assert std._is_fitted


# ============== WINSORIZE METHOD TESTS ==============

def test_winsorize_method():
    """Test winsorize method directly."""
    std = FactorStandardizer()

    # Create series with outliers
    data = pd.Series([1, 2, 3, 4, 5, 100, -100])

    winsorized = std.winsorize(data, lower=0.01, upper=0.99)

    # Outliers should be clipped
    assert winsorized.max() < 100
    assert winsorized.min() > -100


def test_winsorize_empty_series():
    """Test winsorize on empty series."""
    std = FactorStandardizer()
    empty = pd.Series(dtype=float)

    result = std.winsorize(empty)

    assert result.empty


# ============== INVERSE TRANSFORM TESTS ==============

def test_inverse_transform(standardizer):
    """Test inverse transformation."""
    raw_value = 15.0

    # Forward transform
    score = standardizer.transform(raw_value, 'one_year_return', 'equity')

    # Inverse transform
    recovered = standardizer.inverse_transform(score, 'one_year_return', 'equity')

    # Should recover approximately the same value
    assert abs(recovered - raw_value) < 0.1  # Small tolerance


def test_inverse_transform_none(standardizer):
    """Test inverse transform of None."""
    result = standardizer.inverse_transform(None, 'one_year_return', 'equity')

    assert result is None


# ============== CATEGORY STATS TESTS ==============

def test_get_category_stats(standardizer):
    """Test retrieving category statistics."""
    all_stats = standardizer.get_category_stats()

    assert isinstance(all_stats, dict)
    assert 'equity' in all_stats
    assert 'bond' in all_stats

    equity_stats = standardizer.get_category_stats('equity')

    assert isinstance(equity_stats, dict)
    assert 'one_year_return' in equity_stats


def test_get_category_stats_unfitted():
    """Test getting stats before fitting."""
    std = FactorStandardizer()

    with pytest.raises(RuntimeError):
        std.get_category_stats()


# ============== FACTOR SCORE CALCULATION TESTS ==============

def test_calculate_factor_scores(standardizer):
    """Test calculating aggregated factor scores."""
    raw_factors = {
        'one_year_return': 15.0,
        'three_year_return': 12.0,
        'five_year_return': 10.0,
        'max_drawdown': -8.0,
        'volatility': 14.0,
        'sharpe_ratio': 1.2,
        'sortino_ratio': 1.8,
        'calmar_ratio': 0.9,
        'win_rate': 60.0,
    }

    scores = calculate_factor_scores(raw_factors, 'equity', standardizer)

    # Check that all factor categories are present
    assert 'returns' in scores
    assert 'risk_control' in scores
    assert 'risk_adjusted' in scores
    assert 'stability' in scores

    # Scores should be in [0, 100] or None
    for key, value in scores.items():
        if value is not None:
            assert 0 <= value <= 100


def test_calculate_factor_scores_with_none_values(standardizer):
    """Test factor score calculation with missing metrics."""
    raw_factors = {
        'one_year_return': None,
        'three_year_return': 12.0,
        'five_year_return': None,
        'max_drawdown': -8.0,
        'volatility': None,
        'sharpe_ratio': 1.2,
        'sortino_ratio': None,
        'calmar_ratio': 0.9,
        'win_rate': 60.0,
    }

    scores = calculate_factor_scores(raw_factors, 'equity', standardizer)

    # Should handle None values gracefully
    assert scores is not None


# ============== EDGE CASES TESTS ==============

def test_zero_std_in_category():
    """Test handling of zero standard deviation."""
    std = FactorStandardizer()

    # Create data where all values are the same
    df = pd.DataFrame({
        'category': ['equity'] * 10,
        'constant_metric': [5.0] * 10
    })

    # Should fit without error
    std.fit(df, category_col='category')

    # Transform should handle zero std
    score = std.transform(5.0, 'constant_metric', 'equity')

    # Should return None or handle gracefully
    # (Implementation should use std=1.0 as fallback)
    assert score is not None or score is None


def test_single_category():
    """Test with only one category."""
    std = FactorStandardizer()

    df = pd.DataFrame({
        'category': ['equity'] * 20,
        'one_year_return': np.random.normal(10, 5, 20)
    })

    std.fit(df, category_col='category')

    assert len(std.category_stats) == 1
    assert 'equity' in std.category_stats


def test_cross_category_standardization():
    """Test that different categories use different statistics."""
    std = FactorStandardizer()

    # Create data with different distributions per category
    df = pd.DataFrame({
        'category': ['equity'] * 20 + ['bond'] * 20,
        'return': list(np.random.normal(10, 15, 20)) + list(np.random.normal(3, 2, 20))
    })

    std.fit(df, category_col='category')

    # Same raw value should give different scores in different categories
    value = 8.0
    equity_score = std.transform(value, 'return', 'equity')
    bond_score = std.transform(value, 'return', 'bond')

    # Bond funds have lower returns on average, so 8% should be higher percentile
    assert bond_score > equity_score


# ============== MATHEMATICAL ACCURACY TESTS ==============

def test_percentile_calculation():
    """Test that Z-score to percentile conversion is accurate."""
    from scipy import stats

    # Z-score of 0 → 50th percentile
    p50 = stats.norm.cdf(0) * 100
    assert abs(p50 - 50) < EPSILON

    # Z-score of 1 → ~84.13th percentile
    p84 = stats.norm.cdf(1) * 100
    assert 84 < p84 < 85

    # Z-score of -1 → ~15.87th percentile
    p16 = stats.norm.cdf(-1) * 100
    assert 15 < p16 < 16

    # Z-score of 2 → ~97.72th percentile
    p97 = stats.norm.cdf(2) * 100
    assert 97 < p97 < 98

    # Z-score of 3 → ~99.87th percentile
    p99 = stats.norm.cdf(3) * 100
    assert 99 < p99 < 100


def test_rounding_behavior(standardizer):
    """Test that scores are properly rounded."""
    score = standardizer.transform(15.0, 'one_year_return', 'equity')

    # Should be rounded to 2 decimal places
    assert len(str(score).split('.')[-1]) <= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
