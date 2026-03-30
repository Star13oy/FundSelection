"""
Production-grade factor calculation engine for fund selection.

This module implements real financial mathematics for factor scoring, replacing
placeholder MD5 hash calculations with rigorous quantitative metrics.

References:
- Sharpe, W. F. (1994). The Sharpe Ratio. Journal of Portfolio Management.
- Sortino, F. A., & Price, L. N. (1994). Performance measurement in a downside risk framework.
- Calmar, R. (1998). Calmar Ratio: A smoother tool.
- Grinold, R. C., & Kahn, R. N. (2000). Active Portfolio Management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from scipy import stats

if TYPE_CHECKING:
    from app.market_data import MarketQuote
    from app.store import Fund

logger = logging.getLogger(__name__)

# China A-share specific constants
TRADING_DAYS_PER_YEAR = 252
DEFAULT_RISK_FREE_RATE = 0.03  # 3% China 10-yr treasury yield
MIN_DATA_POINTS_1Y = 252
MIN_DATA_POINTS_3Y = 756
MIN_DATA_POINTS_5Y = 1260
MIN_DATA_POINTS_SHORT = 100
EPSILON = 1e-10  # Small value to prevent division by zero


@dataclass
class NAVHistoryRecord:
    """Single NAV history record."""
    date: date
    nav: float
    daily_return: float | None = None


class InsufficientDataError(ValueError):
    """Raised when NAV data is insufficient for calculation."""
    def __init__(self, fund_code: str, required: int, actual: int, metric: str):
        self.fund_code = fund_code
        self.required = required
        self.actual = actual
        self.metric = metric
        super().__init__(
            f"Insufficient data for {fund_code} {metric}: "
            f"need {required} records, got {actual}"
        )


class NAVHistoryManager:
    """
    Manage NAV history data for funds.

    This is a placeholder interface. In production, this would fetch
    historical NAV data from a database or external API.
    """

    def get_nav_history(self, fund_code: str, min_records: int = 0) -> list[NAVHistoryRecord]:
        """
        Retrieve NAV history for a fund.

        Args:
            fund_code: Fund identifier
            min_records: Minimum records required (raises error if not met)

        Returns:
            List of NAV records sorted by date ascending

        Raises:
            InsufficientDataError: If insufficient records available
        """
        # TODO: Implement actual NAV data fetching from database
        # For now, return synthetic data for testing
        raise NotImplementedError(
            "NAV history fetching not yet implemented. "
            "Connect to database or external API for historical NAV data."
        )


class BenchmarkManager:
    """
    Manage benchmark index data for comparison.

    This is now a wrapper around the full benchmark management system.
    Import the real BenchmarkManager from app.benchmark.manager for production use.
    """

    DEFAULT_BENCHMARKS = {
        "equity": "000300.SH",      # CSI 300
        "etf_theme": "000300.SH",   # CSI 300
        "bond": "CBA00101.CS",      # China Bond Composite
    }

    def __init__(self, adapter: Any = None):
        """
        Initialize benchmark manager.

        Args:
            adapter: Optional database adapter. If None, uses real BenchmarkManager
        """
        if adapter is not None:
            # Import real benchmark manager
            from app.benchmark.manager import BenchmarkManager as RealBenchmarkManager
            self._real_manager = RealBenchmarkManager(adapter)
        else:
            self._real_manager = None

    def get_benchmark_returns(self, benchmark_code: str) -> pd.Series:
        """
        Retrieve benchmark return series.

        Args:
            benchmark_code: Benchmark identifier (e.g., "000300.SH")

        Returns:
            Series of daily returns indexed by date
        """
        if self._real_manager:
            # Use real benchmark manager
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=365*5)  # 5 years
            return self._real_manager.get_benchmark_return_series(
                benchmark_code, start_date, end_date
            )
        else:
            # Placeholder - not implemented
            raise NotImplementedError(
                "Benchmark data fetching requires database adapter. "
                "Pass adapter to BenchmarkManager constructor."
            )

    def get_default_benchmark(self, fund_type: str) -> str:
        """Get default benchmark code for fund type."""
        return self.DEFAULT_BENCHMARKS.get(fund_type, "000300.SH")


def clean_nav_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare NAV data for calculations.

    Steps:
    1. Forward-fill missing NAV values (max 3 consecutive)
    2. Remove outliers beyond 5 standard deviations
    3. Ensure chronological order
    4. Calculate daily log returns
    5. Drop rows with NaN returns
    6. Validate minimum data points

    Args:
        df: DataFrame with 'date' and 'nav' columns

    Returns:
        Cleaned DataFrame with 'date', 'nav', 'daily_return' columns

    Raises:
        InsufficientDataError: If insufficient data after cleaning
    """
    if df.empty:
        raise InsufficientDataError("", MIN_DATA_POINTS_SHORT, 0, "empty data")

    # Ensure chronological order
    df = df.sort_values('date').reset_index(drop=True)

    # Forward-fill missing NAV values (max 3 consecutive)
    df['nav'] = df['nav'].ffill(limit=3)

    # Remove outliers beyond 5 standard deviations
    nav_mean = df['nav'].mean()
    nav_std = df['nav'].std()
    if nav_std > 0:
        df = df[np.abs(df['nav'] - nav_mean) <= 5 * nav_std]

    # Calculate daily log returns: ln(NAV_t / NAV_{t-1})
    df['daily_return'] = np.log(df['nav'] / df['nav'].shift(1))

    # Drop first row (NaN return) and any remaining NaNs
    df = df.dropna(subset=['daily_return'])

    # Validate data count
    if len(df) < MIN_DATA_POINTS_SHORT:
        raise InsufficientDataError(
            "", MIN_DATA_POINTS_SHORT, len(df), "after cleaning"
        )

    # Data validation: China A-share limit up/down is ±20%
    extreme_returns = df[np.abs(df['daily_return']) > 0.20]
    if not extreme_returns.empty:
        logger.warning(
            f"Found {len(extreme_returns)} returns outside ±20% limits. "
            f"Dates: {extreme_returns['date'].tolist()}"
        )

    return df


def align_to_benchmark(
    fund_returns: pd.Series,
    benchmark_returns: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """
    Align fund and benchmark returns to same dates.

    Performs inner join on dates to ensure matching time periods.

    Args:
        fund_returns: Series indexed by date
        benchmark_returns: Series indexed by date

    Returns:
        Tuple of (fund_aligned, benchmark_aligned) with matching dates
    """
    aligned = pd.concat(
        [fund_returns, benchmark_returns],
        axis=1,
        join='inner'
    )
    return aligned.iloc[:, 0], aligned.iloc[:, 1]


class FactorCalculator:
    """
    Production-grade factor calculation engine.

    Implements rigorous financial mathematics for factor scoring.
    All calculations use log returns for proper compounding.

    Attributes:
        nav_history: Manager for NAV history data
        benchmark: Manager for benchmark data
    """

    def __init__(
        self,
        nav_history_manager: NAVHistoryManager,
        benchmark_manager: BenchmarkManager
    ):
        self.nav_history = nav_history_manager
        self.benchmark = benchmark_manager

    # ============== RETURN METRICS ==============

    def calculate_returns(self, fund_code: str) -> dict[str, float | None]:
        """
        Calculate return metrics over multiple periods.

        Returns:
            Dictionary with:
                - six_month_return: Annualized 6M return
                - one_year_return: Annualized 1Y return
                - three_year_return: Annualized 3Y return
                - five_year_return: Annualized 5Y return
                - inception_return: Since inception

        Methodology:
            - Use LOG RETURNS for compounding: ln(P_t / P_0)
            - Annualize: (1 + total_return) ^ (252 / n_days) - 1
            - Return None if insufficient data (< 20 records)
        """
        try:
            records = self.nav_history.get_nav_history(fund_code)
        except InsufficientDataError:
            # Return all None if insufficient data
            return {
                'six_month_return': None,
                'one_year_return': None,
                'three_year_return': None,
                'five_year_return': None,
                'inception_return': None,
            }

        if len(records) < 20:
            return {k: None for k in [
                'six_month_return', 'one_year_return', 'three_year_return',
                'five_year_return', 'inception_return'
            ]}

        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': r.date,
            'nav': r.nav
        } for r in records])

        df = clean_nav_data(df)

        # Calculate returns for different periods
        periods_days = {
            'six_month_return': 126,    # ~6 months
            'one_year_return': 252,     # 1 year
            'three_year_return': 756,   # 3 years
            'five_year_return': 1260,   # 5 years
        }

        results = {}
        for metric, days in periods_days.items():
            if len(df) >= days:
                # Get NAV at start and end of period
                nav_start = df['nav'].iloc[-days]
                nav_end = df['nav'].iloc[-1]

                # Log return: ln(NAV_end / NAV_start)
                total_log_return = np.log(nav_end / nav_start)

                # Annualize: (1 + total_return) ^ (252 / n_days) - 1
                annualized_return = (np.exp(total_log_return * 252 / days) - 1) * 100
                results[metric] = annualized_return
            else:
                results[metric] = None

        # Inception return (entire history)
        nav_inception = df['nav'].iloc[0]
        nav_latest = df['nav'].iloc[-1]
        total_log_return = np.log(nav_latest / nav_inception)
        total_days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        if total_days > 0:
            annualized_return = (np.exp(total_log_return * 252 / total_days) - 1) * 100
            results['inception_return'] = annualized_return
        else:
            results['inception_return'] = None

        return results

    def calculate_cumulative_return(
        self,
        fund_code: str,
        period_days: int
    ) -> float | None:
        """
        Calculate cumulative return over period.

        Formula: (NAV_t - NAV_0) / NAV_0

        Args:
            fund_code: Fund identifier
            period_days: Lookback period in days

        Returns:
            Cumulative return as percentage
        """
        try:
            records = self.nav_history.get_nav_history(fund_code, min_records=period_days)
        except InsufficientDataError:
            return None

        if len(records) < period_days:
            return None

        nav_start = records[0].nav
        nav_end = records[-1].nav

        cumulative_return = ((nav_end - nav_start) / nav_start) * 100
        return cumulative_return

    # ============== RISK METRICS ==============

    def calculate_max_drawdown(self, fund_code: str) -> dict[str, float | int]:
        """
        Calculate maximum drawdown with recovery analysis.

        Returns:
            Dictionary with:
                - max_drawdown: Peak-to-trough decline (%)
                - max_drawdown_duration: Days from peak to trough
                - recovery_duration: Days from trough to new peak (0 if not recovered)

        Methodology:
            - Calculate running maximum: cummax(NAV_series)
            - Drawdown: (NAV_t - cummax_t) / cummax_t
            - Max drawdown: min(drawdown_series)
            - Find dates for peak, trough, recovery
        """
        try:
            records = self.nav_history.get_nav_history(
                fund_code,
                min_records=MIN_DATA_POINTS_SHORT
            )
        except InsufficientDataError as e:
            logger.warning(f"Cannot calculate max drawdown: {e}")
            return {
                'max_drawdown': 0.0,
                'max_drawdown_duration': 0,
                'recovery_duration': 0,
            }

        df = pd.DataFrame([{
            'date': r.date,
            'nav': r.nav
        } for r in records])

        df = clean_nav_data(df)

        # Calculate running maximum
        df['cummax'] = df['nav'].cummax()

        # Calculate drawdown
        df['drawdown'] = (df['nav'] - df['cummax']) / df['cummax']

        # Find max drawdown
        max_dd_idx = df['drawdown'].idxmin()
        max_dd = df.loc[max_dd_idx, 'drawdown'] * 100  # Convert to percentage

        # Find peak (highest point before trough)
        peak_idx = df.loc[:max_dd_idx, 'nav'].idxmax()
        peak_date = df.loc[peak_idx, 'date']
        trough_date = df.loc[max_dd_idx, 'date']

        # Calculate duration from peak to trough
        dd_duration = (trough_date - peak_date).days

        # Find recovery (if any)
        recovery_duration = 0
        if max_dd_idx < len(df) - 1:
            post_trough = df.loc[max_dd_idx:, 'nav']
            peak_nav = df.loc[peak_idx, 'nav']

            # Find first day where NAV exceeds peak
            recovery_mask = post_trough >= peak_nav
            if recovery_mask.any():
                recovery_idx = recovery_mask.idxmax()
                recovery_date = df.loc[recovery_idx, 'date']
                recovery_duration = (recovery_date - trough_date).days

        return {
            'max_drawdown': max_dd,
            'max_drawdown_duration': dd_duration,
            'recovery_duration': recovery_duration,
        }

    def calculate_volatility(
        self,
        fund_code: str,
        period: int = 252
    ) -> float | None:
        """
        Calculate annualized volatility.

        Formula: std(daily_returns) * sqrt(252)

        Uses daily returns from NAV data.
        Annualizes using 252 trading days (China A-share).

        Args:
            fund_code: Fund identifier
            period: Lookback period in days (default: 1 year)

        Returns:
            Annualized volatility as percentage
        """
        try:
            records = self.nav_history.get_nav_history(
                fund_code,
                min_records=min(period, MIN_DATA_POINTS_SHORT)
            )
        except InsufficientDataError:
            return None

        if len(records) < period:
            period = len(records)

        df = pd.DataFrame([{
            'date': r.date,
            'nav': r.nav
        } for r in records])

        df = clean_nav_data(df)

        # Use last 'period' records
        if len(df) > period:
            df = df.iloc[-period:]

        # Calculate volatility: std(daily_returns) * sqrt(252)
        volatility = df['daily_return'].std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100

        return volatility

    def calculate_downside_deviation(
        self,
        fund_code: str,
        min_return: float = 0.0
    ) -> float | None:
        """
        Calculate downside deviation (semi-deviation).

        Only consider returns below min_return (typically 0 or risk-free rate).

        Formula: sqrt(sum(min(0, r_t - min_return))^2 / n) * sqrt(252)

        Used in Sortino ratio calculation.

        Args:
            fund_code: Fund identifier
            min_return: Minimum acceptable return (default: 0.0)

        Returns:
            Annualized downside deviation as percentage
        """
        try:
            records = self.nav_history.get_nav_history(
                fund_code,
                min_records=MIN_DATA_POINTS_SHORT
            )
        except InsufficientDataError:
            return None

        df = pd.DataFrame([{
            'date': r.date,
            'nav': r.nav
        } for r in records])

        df = clean_nav_data(df)

        # Convert min_return to daily
        daily_min_return = min_return / TRADING_DAYS_PER_YEAR

        # Calculate downside returns
        downside_returns = df['daily_return'] - daily_min_return
        downside_returns = downside_returns[downside_returns < 0]

        if downside_returns.empty:
            return 0.0

        # Downside deviation: sqrt(mean(downside^2)) * sqrt(252)
        downside_dev = np.sqrt(np.mean(downside_returns ** 2))
        downside_dev_annual = downside_dev * np.sqrt(TRADING_DAYS_PER_YEAR) * 100

        return downside_dev_annual

    # ============== RISK-ADJUSTED METRICS ==============

    def calculate_sharpe_ratio(
        self,
        fund_code: str,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    ) -> float | None:
        """
        Calculate Sharpe ratio.

        Formula: (R_p - R_f) / sigma_p

        Where:
            - R_p = Portfolio annualized return
            - R_f = Risk-free rate (annualized, China 10-yr treasury ~3%)
            - sigma_p = Annualized volatility

        Note: Uses 3% as default risk-free rate for China.

        Args:
            fund_code: Fund identifier
            risk_free_rate: Annual risk-free rate (default: 0.03)

        Returns:
            Sharpe ratio
        """
        returns = self.calculate_returns(fund_code)
        annual_return = returns.get('one_year_return')

        if annual_return is None:
            return None

        volatility = self.calculate_volatility(fund_code)
        if volatility is None or volatility < EPSILON:
            return None

        # Sharpe = (R_p - R_f) / sigma_p
        sharpe = (annual_return / 100 - risk_free_rate) / (volatility / 100)

        return sharpe

    def calculate_sortino_ratio(
        self,
        fund_code: str,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    ) -> float | None:
        """
        Calculate Sortino ratio.

        Formula: (R_p - R_f) / sigma_downside

        Uses downside deviation instead of total volatility.
        More sensitive to downside risk.

        Args:
            fund_code: Fund identifier
            risk_free_rate: Annual risk-free rate (default: 0.03)

        Returns:
            Sortino ratio
        """
        returns = self.calculate_returns(fund_code)
        annual_return = returns.get('one_year_return')

        if annual_return is None:
            return None

        downside_dev = self.calculate_downside_deviation(
            fund_code,
            min_return=risk_free_rate
        )

        if downside_dev is None or downside_dev < EPSILON:
            return None

        # Sortino = (R_p - R_f) / sigma_downside
        sortino = (annual_return / 100 - risk_free_rate) / (downside_dev / 100)

        return sortino

    def calculate_calmar_ratio(self, fund_code: str) -> float | None:
        """
        Calculate Calmar ratio.

        Formula: Annualized Return / abs(Max Drawdown)

        Reward-to-risk ratio using drawdown as risk measure.
        Higher is better.

        Returns:
            Calmar ratio
        """
        returns = self.calculate_returns(fund_code)
        annual_return = returns.get('one_year_return')

        if annual_return is None:
            return None

        drawdown_info = self.calculate_max_drawdown(fund_code)
        max_dd = abs(drawdown_info['max_drawdown'])

        if max_dd < EPSILON:
            return None

        # Calmar = Return / |Max DD|
        calmar = annual_return / max_dd

        return calmar

    def calculate_information_ratio(
        self,
        fund_code: str,
        benchmark_code: str | None = None
    ) -> float | None:
        """
        Calculate Information Ratio with real benchmark data.

        Formula: (R_p - R_b) / tracking_error

        Where:
            - R_p = Portfolio return
            - R_b = Benchmark return
            - tracking_error = std(R_p - R_b)

        Measures excess return per unit of tracking risk.

        Args:
            fund_code: Fund identifier
            benchmark_code: Benchmark code (None for default)

        Returns:
            Information ratio
        """
        try:
            # Get fund returns
            fund_nav = self.nav_history.get_nav_history(fund_code, min_records=MIN_DATA_POINTS_SHORT)

            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': r.date,
                'nav': r.nav
            } for r in fund_nav])

            df = clean_nav_data(df)

            # Create fund returns series
            fund_returns = pd.Series(
                df['daily_return'].values,
                index=pd.to_datetime(df['date']),
                name=f"{fund_code}_returns"
            )

            # Get benchmark returns
            if benchmark_code is None:
                # Auto-select benchmark based on fund type
                benchmark_code = self.benchmark.get_default_benchmark("equity")

            benchmark_returns = self.benchmark.get_benchmark_returns(benchmark_code)

            if benchmark_returns.empty:
                logger.warning(f"No benchmark data available for {benchmark_code}")
                return None

            # Align dates
            fund_returns_aligned, benchmark_returns_aligned = align_to_benchmark(
                fund_returns, benchmark_returns
            )

            if fund_returns_aligned.empty or benchmark_returns_aligned.empty:
                logger.warning("Insufficient aligned data for IR calculation")
                return None

            # Calculate excess returns
            excess_returns = fund_returns_aligned - benchmark_returns_aligned

            # Calculate tracking error (annualized)
            tracking_error = excess_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)

            if tracking_error < EPSILON:
                logger.warning("Tracking error is near zero, cannot calculate IR")
                return None

            # Calculate mean excess return (annualized)
            mean_excess_return = excess_returns.mean() * TRADING_DAYS_PER_YEAR

            # Calculate Information Ratio
            information_ratio = mean_excess_return / tracking_error

            logger.debug(f"Information Ratio for {fund_code}: {information_ratio:.4f}")
            return float(information_ratio)

        except Exception as e:
            logger.error(f"Failed to calculate Information Ratio for {fund_code}: {e}")
            return None

    # ============== STABILITY METRICS ==============

    def calculate_up_down_capture(
        self,
        fund_code: str,
        benchmark_code: str | None = None
    ) -> dict[str, float | None]:
        """
        Calculate up/down market capture ratios with real benchmark data.

        Returns:
            Dictionary with:
                - up_capture: Fund return / Benchmark return in up markets
                - down_capture: Fund return / Benchmark return in down markets

        Methodology:
            - Identify up markets: benchmark return > 0
            - Identify down markets: benchmark return < 0
            - Calculate capture ratios as regression slopes
            - Ideal: up_capture > 100%, down_capture < 100%
        """
        try:
            # Get fund returns
            fund_nav = self.nav_history.get_nav_history(fund_code, min_records=MIN_DATA_POINTS_SHORT)

            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': r.date,
                'nav': r.nav
            } for r in fund_nav])

            df = clean_nav_data(df)

            # Create fund returns series
            fund_returns = pd.Series(
                df['daily_return'].values,
                index=pd.to_datetime(df['date']),
                name=f"{fund_code}_returns"
            )

            # Get benchmark returns
            if benchmark_code is None:
                # Auto-select benchmark based on fund type
                benchmark_code = self.benchmark.get_default_benchmark("equity")

            benchmark_returns = self.benchmark.get_benchmark_returns(benchmark_code)

            if benchmark_returns.empty:
                logger.warning(f"No benchmark data available for {benchmark_code}")
                return {
                    'up_capture': None,
                    'down_capture': None,
                }

            # Align dates
            fund_returns_aligned, benchmark_returns_aligned = align_to_benchmark(
                fund_returns, benchmark_returns
            )

            if fund_returns_aligned.empty or benchmark_returns_aligned.empty:
                logger.warning("Insufficient aligned data for capture calculation")
                return {
                    'up_capture': None,
                    'down_capture': None,
                }

            # Identify up and down markets
            up_mask = benchmark_returns_aligned > 0
            down_mask = benchmark_returns_aligned < 0

            if up_mask.sum() == 0 or down_mask.sum() == 0:
                logger.warning("Insufficient up/down market data")
                return {
                    'up_capture': None,
                    'down_capture': None,
                }

            # Calculate up capture
            fund_up = fund_returns_aligned[up_mask]
            benchmark_up = benchmark_returns_aligned[up_mask]

            # Compound return formula: (1 + r1) * (1 + r2) * ... - 1
            fund_up_cumulative = (1 + fund_up).prod() - 1
            benchmark_up_cumulative = (1 + benchmark_up).prod() - 1

            up_capture = (
                (fund_up_cumulative / benchmark_up_cumulative * 100)
                if benchmark_up_cumulative != 0
                else None
            )

            # Calculate down capture
            fund_down = fund_returns_aligned[down_mask]
            benchmark_down = benchmark_returns_aligned[down_mask]

            fund_down_cumulative = (1 + fund_down).prod() - 1
            benchmark_down_cumulative = (1 + benchmark_down).prod() - 1

            down_capture = (
                (fund_down_cumulative / benchmark_down_cumulative * 100)
                if benchmark_down_cumulative != 0
                else None
            )

            logger.debug(
                f"Up/Down capture for {fund_code}: "
                f"up={up_capture:.2f}%, down={down_capture:.2f}%"
            )

            return {
                'up_capture': float(up_capture) if up_capture is not None else None,
                'down_capture': float(down_capture) if down_capture is not None else None,
            }

        except Exception as e:
            logger.error(f"Failed to calculate up/down capture for {fund_code}: {e}")
            return {
                'up_capture': None,
                'down_capture': None,
            }

    def calculate_rolling_win_rate(
        self,
        fund_code: str,
        window: int = 20
    ) -> float | None:
        """
        Calculate rolling win rate.

        Percentage of rolling windows with positive returns.

        Formula: count(return > 0) / total_windows

        Measures consistency of positive performance.

        Args:
            fund_code: Fund identifier
            window: Rolling window size in days (default: 20)

        Returns:
            Win rate as percentage (0-100)
        """
        try:
            records = self.nav_history.get_nav_history(
                fund_code,
                min_records=MIN_DATA_POINTS_SHORT
            )
        except InsufficientDataError:
            return None

        if len(records) < window:
            return None

        df = pd.DataFrame([{
            'date': r.date,
            'nav': r.nav
        } for r in records])

        df = clean_nav_data(df)

        # Calculate rolling returns
        rolling_returns = df['nav'].pct_change(window).dropna()

        if rolling_returns.empty:
            return None

        # Win rate: percentage of positive returns
        win_rate = (rolling_returns > 0).sum() / len(rolling_returns) * 100

        return win_rate

    def calculate_tracking_error(
        self,
        fund_code: str,
        benchmark_code: str | None = None
    ) -> float | None:
        """
        Calculate tracking error with real benchmark data.

        Formula: std(R_p - R_b) * sqrt(252)

        Annualized standard deviation of excess returns.

        Args:
            fund_code: Fund identifier
            benchmark_code: Benchmark code (None for default)

        Returns:
            Tracking error as percentage
        """
        try:
            # Get fund returns
            fund_nav = self.nav_history.get_nav_history(fund_code, min_records=MIN_DATA_POINTS_SHORT)

            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': r.date,
                'nav': r.nav
            } for r in fund_nav])

            df = clean_nav_data(df)

            # Create fund returns series
            fund_returns = pd.Series(
                df['daily_return'].values,
                index=pd.to_datetime(df['date']),
                name=f"{fund_code}_returns"
            )

            # Get benchmark returns
            if benchmark_code is None:
                # Auto-select benchmark based on fund type
                benchmark_code = self.benchmark.get_default_benchmark("equity")

            benchmark_returns = self.benchmark.get_benchmark_returns(benchmark_code)

            if benchmark_returns.empty:
                logger.warning(f"No benchmark data available for {benchmark_code}")
                return None

            # Align dates
            fund_returns_aligned, benchmark_returns_aligned = align_to_benchmark(
                fund_returns, benchmark_returns
            )

            if fund_returns_aligned.empty or benchmark_returns_aligned.empty:
                logger.warning("Insufficient aligned data for tracking error calculation")
                return None

            # Calculate excess returns
            excess_returns = fund_returns_aligned - benchmark_returns_aligned

            # Calculate tracking error (annualized)
            tracking_error = excess_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100

            logger.debug(f"Tracking error for {fund_code}: {tracking_error:.2f}%")
            return float(tracking_error)

        except Exception as e:
            logger.error(f"Failed to calculate tracking error for {fund_code}: {e}")
            return None

    # ============== COST & EFFICIENCY METRICS ==============

    def calculate_expense_ratio_impact(
        self,
        fund_code: str,
        expense_ratio: float
    ) -> dict[str, float | int | None]:
        """
        Calculate impact of expense ratio on returns.

        Returns:
            Dictionary with:
                - net_return: Return after fees
                - fee_impact: Basis points lost to fees
                - fee_rank: Percentile rank vs category (1-100)
        """
        returns = self.calculate_returns(fund_code)
        gross_return = returns.get('one_year_return')

        if gross_return is None:
            return {
                'net_return': None,
                'fee_impact': None,
                'fee_rank': None,
            }

        # Net return = gross - expense_ratio
        net_return = gross_return - expense_ratio * 100

        # Fee impact in basis points
        fee_impact = expense_ratio * 10000  # Convert to bps

        # TODO: Calculate percentile rank vs category
        # This requires cross-sectional data from all funds
        fee_rank = 50  # Placeholder

        return {
            'net_return': net_return,
            'fee_impact': fee_impact,
            'fee_rank': fee_rank,
        }

    def calculate_turnover_rate(self, fund_code: str) -> float | None:
        """
        Calculate portfolio turnover rate.

        Measures trading activity.
        High turnover = higher transaction costs.

        Note: This data may not be available in NAV history.
        Return None if data unavailable.

        Returns:
            Annual turnover rate as percentage
        """
        # TODO: Implement when turnover data is available
        # This requires portfolio holdings data, not just NAV
        logger.warning("Turnover rate not yet implemented - requires holdings data")
        return None

    # ============== AGGREGATE FACTOR SCORES ==============

    def calculate_all_factors(self, fund_code: str) -> dict[str, float | None]:
        """
        Calculate all factor scores for a fund.

        Returns dict with all raw metrics:
            - Returns: 1Y, 3Y, 5Y returns
            - Risk: max_dd, volatility, downside_dev
            - Risk-adjusted: sharpe, sortino, calmar, info_ratio
            - Stability: up_capture, down_capture, win_rate
            - Cost: expense_ratio_impact

        Note: This returns RAW metrics, not standardized 0-100 scores.
        Use FactorStandardizer for standardization.
        """
        factors = {}

        # Return metrics
        returns = self.calculate_returns(fund_code)
        factors['one_year_return'] = returns.get('one_year_return')
        factors['three_year_return'] = returns.get('three_year_return')
        factors['five_year_return'] = returns.get('five_year_return')

        # Risk metrics
        drawdown_info = self.calculate_max_drawdown(fund_code)
        factors['max_drawdown'] = drawdown_info['max_drawdown']
        factors['volatility'] = self.calculate_volatility(fund_code)
        factors['downside_deviation'] = self.calculate_downside_deviation(fund_code)

        # Risk-adjusted metrics
        factors['sharpe_ratio'] = self.calculate_sharpe_ratio(fund_code)
        factors['sortino_ratio'] = self.calculate_sortino_ratio(fund_code)
        factors['calmar_ratio'] = self.calculate_calmar_ratio(fund_code)
        factors['information_ratio'] = self.calculate_information_ratio(fund_code)

        # Stability metrics
        capture = self.calculate_up_down_capture(fund_code)
        factors['up_capture'] = capture.get('up_capture')
        factors['down_capture'] = capture.get('down_capture')
        factors['win_rate'] = self.calculate_rolling_win_rate(fund_code)

        # Cost metrics (expense ratio needs to be passed in)
        # factors['expense_ratio_impact'] = ... (caller provides)

        return factors
