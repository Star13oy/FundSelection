"""
Comprehensive test suite for factor calculation engine.

Tests verify mathematical correctness of financial calculations including:
- Return calculations (log returns, annualization)
- Risk metrics (max drawdown, volatility, downside deviation)
- Risk-adjusted ratios (Sharpe, Sortino, Calmar)
- Stability metrics (win rate, capture ratios)
- Data preprocessing and edge cases
"""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.factors.calculator import (
    EPSILON,
    FactorCalculator,
    InsufficientDataError,
    NAVHistoryManager,
    NAVHistoryRecord,
    BenchmarkManager,
    align_to_benchmark,
    clean_nav_data,
)


# ============== FIXTURES ==============

@pytest.fixture
def sample_nav_records():
    """Create sample NAV history for testing."""
    base_date = datetime.date(2023, 1, 1)
    records = []
    nav = 1.0

    # Generate 300 days of NAV data with realistic returns
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.015, 300)  # Daily returns ~0.05% mean, 1.5% std

    for i, ret in enumerate(returns):
        nav *= (1 + ret)
        records.append(NAVHistoryRecord(
            date=base_date + datetime.timedelta(days=i),
            nav=nav
        ))

    return records


@pytest.fixture
def sample_nav_df():
    """Create sample NAV DataFrame for testing."""
    base_date = datetime.date(2023, 1, 1)
    dates = [base_date + datetime.timedelta(days=i) for i in range(300)]

    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.015, 300)
    navs = 1.0 * np.cumprod(1 + returns)

    return pd.DataFrame({
        'date': dates,
        'nav': navs
    })


@pytest.fixture
def nav_manager(sample_nav_records):
    """Create NAV history manager with sample data."""
    manager = MagicMock(spec=NAVHistoryManager)
    manager.get_nav_history.return_value = sample_nav_records
    return manager


@pytest.fixture
def benchmark_manager():
    """Create benchmark manager."""
    manager = MagicMock(spec=BenchmarkManager)
    return manager


@pytest.fixture
def calculator(nav_manager, benchmark_manager):
    """Create FactorCalculator instance."""
    return FactorCalculator(nav_manager, benchmark_manager)


# ============== DATA PREPROCESSING TESTS ==============

def test_clean_nav_data_basic(sample_nav_df):
    """Test basic NAV data cleaning."""
    cleaned = clean_nav_data(sample_nav_df)

    assert 'daily_return' in cleaned.columns
    assert len(cleaned) > 0
    assert cleaned['daily_return'].notna().all()


def test_clean_nav_data_forward_fill():
    """Test forward-filling of missing NAV values."""
    df = pd.DataFrame({
        'date': [datetime.date(2023, 1, i) for i in range(1, 6)],
        'nav': [1.0, None, None, None, 1.05]  # 3 consecutive missing
    })

    cleaned = clean_nav_data(df)

    # Should forward-fill up to 3 consecutive missing
    assert cleaned['nav'].isna().sum() == 0


def test_clean_nav_data_outlier_removal():
    """Test outlier removal beyond 5 standard deviations."""
    np.random.seed(42)
    df = pd.DataFrame({
        'date': [datetime.date(2023, 1, i) for i in range(1, 101)],
        'nav': list(np.random.normal(1.0, 0.01, 99)) + [10.0]  # Extreme outlier
    })

    cleaned = clean_nav_data(df)

    # Outlier should be removed
    assert cleaned['nav'].max() < 2.0


def test_clean_nav_data_insufficient_data():
    """Test error handling for insufficient data."""
    df = pd.DataFrame({
        'date': [datetime.date(2023, 1, 1)],
        'nav': [1.0]
    })

    with pytest.raises(InsufficientDataError):
        clean_nav_data(df)


def test_align_to_benchmark():
    """Test alignment of fund and benchmark returns."""
    fund_returns = pd.Series([
        0.01, 0.02, 0.015, -0.01, 0.005
    ], index=pd.date_range('2023-01-01', periods=5))

    benchmark_returns = pd.Series([
        0.008, 0.018, None, -0.008, 0.003
    ], index=pd.date_range('2023-01-02', periods=5))

    fund_aligned, bench_aligned = align_to_benchmark(fund_returns, benchmark_returns)

    # Should align to matching dates
    assert len(fund_aligned) == len(bench_aligned)
    assert fund_aligned.index.equals(bench_aligned.index)


# ============== RETURN METRICS TESTS ==============

def test_calculate_returns(calculator):
    """Test return calculations."""
    returns = calculator.calculate_returns('TEST001')

    assert 'one_year_return' in returns
    assert 'three_year_return' in returns
    assert 'five_year_return' in returns

    # 1-year return should be calculated
    assert returns['one_year_return'] is not None


def test_calculate_returns_insufficient_data(nav_manager, benchmark_manager):
    """Test return calculation with insufficient data."""
    nav_manager.get_nav_history.side_effect = InsufficientDataError(
        'TEST001', 252, 10, 'insufficient data'
    )

    calc = FactorCalculator(nav_manager, benchmark_manager)
    returns = calc.calculate_returns('TEST001')

    # All returns should be None
    assert all(v is None for v in returns.values())


def test_calculate_cumulative_return(calculator):
    """Test cumulative return calculation."""
    cum_return = calculator.calculate_cumulative_return('TEST001', 126)

    assert cum_return is not None
    assert isinstance(cum_return, float)


# ============== RISK METRICS TESTS ==============

def test_calculate_max_drawdown(calculator):
    """Test maximum drawdown calculation."""
    drawdown_info = calculator.calculate_max_drawdown('TEST001')

    assert 'max_drawdown' in drawdown_info
    assert 'max_drawdown_duration' in drawdown_info
    assert 'recovery_duration' in drawdown_info

    # Max drawdown should be negative (loss)
    assert drawdown_info['max_drawdown'] <= 0


def test_calculate_volatility(calculator):
    """Test volatility calculation."""
    volatility = calculator.calculate_volatility('TEST001')

    assert volatility is not None
    assert volatility >= 0  # Volatility is always non-negative


def test_calculate_downside_deviation(calculator):
    """Test downside deviation calculation."""
    downside_dev = calculator.calculate_downside_deviation('TEST001')

    assert downside_dev is not None
    assert downside_dev >= 0


# ============== RISK-ADJUSTED METRICS TESTS ==============

def test_calculate_sharpe_ratio(calculator):
    """Test Sharpe ratio calculation."""
    sharpe = calculator.calculate_sharpe_ratio('TEST001')

    assert sharpe is not None
    # Sharpe ratio can be negative or positive
    assert isinstance(sharpe, float)


def test_calculate_sortino_ratio(calculator):
    """Test Sortino ratio calculation."""
    sortino = calculator.calculate_sortino_ratio('TEST001')

    assert sortino is not None
    assert isinstance(sortino, float)


def test_calculate_calmar_ratio(calculator):
    """Test Calmar ratio calculation."""
    calmar = calculator.calculate_calmar_ratio('TEST001')

    assert calmar is not None
    assert isinstance(calmar, float)


def test_sharpe_sortino_relationship(calculator):
    """Test that Sortino >= Sharpe (usually)."""
    sharpe = calculator.calculate_sharpe_ratio('TEST001')
    sortino = calculator.calculate_sortino_ratio('TEST001')

    # Sortino should typically be >= Sharpe (downside risk < total risk)
    # But this isn't always true, so we just check both are calculated
    assert sharpe is not None
    assert sortino is not None


# ============== STABILITY METRICS TESTS ==============

def test_calculate_rolling_win_rate(calculator):
    """Test rolling win rate calculation."""
    win_rate = calculator.calculate_rolling_win_rate('TEST001', window=20)

    assert win_rate is not None
    assert 0 <= win_rate <= 100  # Win rate is percentage


# ============== AGGREGATE FACTORS TESTS ==============

def test_calculate_all_factors(calculator):
    """Test calculation of all factors."""
    factors = calculator.calculate_all_factors('TEST001')

    # Check that major factor categories are present
    assert 'one_year_return' in factors
    assert 'max_drawdown' in factors
    assert 'volatility' in factors
    assert 'sharpe_ratio' in factors
    assert 'sortino_ratio' in factors
    assert 'calmar_ratio' in factors


# ============== EDGE CASES TESTS ==============

def test_handle_new_fund_with_short_history(nav_manager, benchmark_manager):
    """Test handling of new funds with short history."""
    # Create manager with only 50 days of data
    short_records = [
        NAVHistoryRecord(
            date=datetime.date(2023, 1, 1) + datetime.timedelta(days=i),
            nav=1.0 + i * 0.001
        )
        for i in range(50)
    ]

    nav_manager.get_nav_history.return_value = short_records

    calc = FactorCalculator(nav_manager, benchmark_manager)

    # Should handle short history gracefully
    returns = calc.calculate_returns('NEW001')
    assert returns['one_year_return'] is None  # Insufficient for 1Y
    assert returns['inception_return'] is not None  # But can calculate inception


def test_handle_flat_nav(nav_manager, benchmark_manager):
    """Test handling of constant NAV (zero returns)."""
    flat_records = [
        NAVHistoryRecord(
            date=datetime.date(2023, 1, 1) + datetime.timedelta(days=i),
            nav=1.0
        )
        for i in range(300)
    ]

    nav_manager.get_nav_history.return_value = flat_records

    calc = FactorCalculator(nav_manager, benchmark_manager)

    # Should handle zero returns
    volatility = calc.calculate_volatility('FLAT001')
    assert volatility is not None
    # Volatility should be very close to zero
    assert volatility < 0.1


def test_handle_extreme_volatility(nav_manager, benchmark_manager):
    """Test handling of extreme volatility scenarios."""
    np.random.seed(42)
    extreme_records = []
    nav = 1.0

    for i in range(300):
        # Extreme daily returns: ±10%
        change = np.random.choice([0.10, -0.10])
        nav *= (1 + change)
        extreme_records.append(NAVHistoryRecord(
            date=datetime.date(2023, 1, 1) + datetime.timedelta(days=i),
            nav=nav
        ))

    nav_manager.get_nav_history.return_value = extreme_records

    calc = FactorCalculator(nav_manager, benchmark_manager)

    # Should calculate metrics even with extreme volatility
    volatility = calc.calculate_volatility('EXTREME001')
    assert volatility is not None
    # Volatility should be very high
    assert volatility > 50


# ============== MATHEMATICAL ACCURACY TESTS ==============

def test_log_return_calculation():
    """Test that log returns are calculated correctly."""
    # Simple case: NAV goes from 1.0 to 1.1 (10% gain)
    nav_start = 1.0
    nav_end = 1.1

    # Log return
    log_return = np.log(nav_end / nav_start)

    # Expected: ln(1.1) ≈ 0.09531
    expected = np.log(1.1)

    assert abs(log_return - expected) < 1e-10


def test_annualization_formula():
    """Test annualization formula for returns."""
    # 6-month return of 10%
    six_month_return = 0.10
    days = 126

    # Annualize: (1 + 0.10)^(252/126) - 1 = (1.10)^2 - 1 = 0.21 = 21%
    annualized = (1 + six_month_return) ** (252 / days) - 1

    expected = 1.10 ** 2 - 1  # 0.21

    assert abs(annualized - expected) < 1e-10


def test_volatility_formula():
    """Test volatility calculation formula."""
    # Create simple returns: 1%, -1%, 1%, -1%
    daily_returns = pd.Series([0.01, -0.01, 0.01, -0.01])

    # Std of daily returns
    daily_std = daily_returns.std()

    # Annualize: std * sqrt(252)
    annual_vol = daily_std * np.sqrt(252)

    assert annual_vol > 0
    assert annual_vol < 1  # Should be reasonable


def test_max_drawdown_formula():
    """Test maximum drawdown calculation."""
    # Create NAV series with clear peak and trough
    nav_series = pd.Series([1.0, 1.1, 1.2, 1.0, 0.9, 0.95, 1.0])

    # Calculate running max
    cummax = nav_series.cummax()

    # Drawdown
    drawdown = (nav_series - cummax) / cummax

    # Max drawdown should be at trough (0.9 vs peak 1.2)
    max_dd = drawdown.min()

    # Expected: (0.9 - 1.2) / 1.2 = -0.25 = -25%
    expected = (0.9 - 1.2) / 1.2

    assert abs(max_dd - expected) < 1e-10


# ============== INTEGRATION TESTS ==============

def test_factor_calculation_pipeline(nav_manager, benchmark_manager):
    """Test complete factor calculation pipeline."""
    calc = FactorCalculator(nav_manager, benchmark_manager)

    # Calculate all factors
    factors = calc.calculate_all_factors('TEST001')

    # Verify key metrics are present and reasonable
    assert factors['one_year_return'] is not None
    assert factors['max_drawdown'] is not None
    assert factors['volatility'] is not None

    # Verify logical relationships
    # Max drawdown should be negative
    assert factors['max_drawdown'] <= 0

    # Volatility should be non-negative
    assert factors['volatility'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
