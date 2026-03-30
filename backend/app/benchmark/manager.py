"""
High-level benchmark management interface.

This module provides a unified interface for benchmark data operations,
combining fetching, storage, and analysis capabilities.

Critical infrastructure: This is the main entry point for all benchmark
operations in the factor calculation engine.
"""

from __future__ import annotations

import logging
from datetime import date

import numpy as np
import pandas as pd

from app.benchmark.fetcher import BenchmarkFetcher
from app.benchmark.models import STANDARD_BENCHMARK_CODES
from app.benchmark.repository import BenchmarkRepository
from app.db import get_adapter

logger = logging.getLogger(__name__)


class BenchmarkManager:
    """High-level interface for benchmark data operations.

    This class combines fetching, storage, and analysis capabilities
    into a unified interface for the factor calculation engine.

    Attributes:
        adapter: Database adapter
        fetcher: BenchmarkFetcher instance
        repo: BenchmarkRepository instance

    Examples:
        >>> manager = BenchmarkManager(get_adapter())
        >>> returns = manager.get_benchmark_return_series("000300.SH", start_date, end_date)
        >>> benchmark = manager.get_appropriate_benchmark("宽基", "科技")
    """

    def __init__(self, adapter: any) -> None:
        """
        Initialize benchmark manager.

        Args:
            adapter: Database adapter instance
        """
        self.adapter = adapter
        self.fetcher = BenchmarkFetcher(adapter)
        self.repo = BenchmarkRepository(adapter)

    def get_benchmark_return_series(
        self,
        index_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.Series:
        """
        Get return series for benchmark.

        Returns pd.Series with:
        - Index: dates (datetime)
        - Values: daily returns (decimal, e.g., 0.0125 for 1.25%)

        Used in Information Ratio and tracking error calculations.

        Args:
            index_code: Benchmark index code (e.g., '000300.SH')
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            pd.Series of daily returns indexed by date

        Raises:
            ValueError: If no data found for the index
        """
        logger.debug(f"Getting return series for {index_code} from {start_date} to {end_date}")

        # Fetch historical data
        df = self.repo.get_history(index_code, start_date, end_date)

        if df.empty:
            logger.warning(f"No historical data found for benchmark {index_code}")
            return pd.Series(dtype=float)

        # Ensure we have daily_return column
        if 'daily_return' not in df.columns:
            logger.warning(f"No daily_return column for {index_code}, calculating from close prices")
            df = self.fetcher.calculate_daily_returns(df)

        # Create series with date index
        returns_series = pd.Series(
            df['daily_return'].values,
            index=pd.to_datetime(df['trade_date']),
            name=f"{index_code}_returns"
        )

        # Drop NaN values (first row has no return)
        returns_series = returns_series.dropna()

        logger.debug(f"Retrieved {len(returns_series)} return values for {index_code}")
        return returns_series

    def align_fund_to_benchmark(
        self,
        fund_returns: pd.Series,
        benchmark_code: str,
    ) -> tuple[pd.Series, pd.Series]:
        """
        Align fund and benchmark returns to same dates.

        Performs inner join on dates to ensure matching time periods.
        This is critical for accurate relative performance calculations.

        Args:
            fund_returns: Fund returns Series indexed by date
            benchmark_code: Benchmark index code

        Returns:
            Tuple of (fund_returns_aligned, benchmark_returns_aligned)
            Both Series have matching date indices

        Examples:
            >>> fund_returns = pd.Series([0.01, 0.02, -0.01], index=pd.date_range('2025-01-01', periods=3))
            >>> fund_aligned, bench_aligned = manager.align_fund_to_benchmark(fund_returns, "000300.SH")
            >>> assert len(fund_aligned) == len(bench_aligned)
        """
        logger.debug(f"Aligning fund returns to benchmark {benchmark_code}")

        # Get benchmark returns for the same date range
        start_date = fund_returns.index.min().date()
        end_date = fund_returns.index.max().date()

        benchmark_returns = self.get_benchmark_return_series(
            benchmark_code, start_date, end_date
        )

        if benchmark_returns.empty:
            logger.warning(f"No benchmark returns available for {benchmark_code}")
            return fund_returns, pd.Series(dtype=float)

        # Perform inner join on dates
        aligned = pd.concat(
            [fund_returns, benchmark_returns],
            axis=1,
            join='inner'
        )

        fund_aligned = aligned.iloc[:, 0]
        benchmark_aligned = aligned.iloc[:, 1]

        logger.debug(f"Aligned {len(fund_aligned)} dates between fund and benchmark")
        return fund_aligned, benchmark_aligned

    def calculate_excess_returns(
        self,
        fund_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> pd.Series:
        """
        Calculate excess returns (fund - benchmark).

        Formula: R_excess = R_fund - R_benchmark

        Args:
            fund_returns: Fund returns Series
            benchmark_returns: Benchmark returns Series

        Returns:
            pd.Series of excess returns

        Examples:
            >>> fund_returns = pd.Series([0.01, 0.02, -0.01])
            >>> benchmark_returns = pd.Series([0.008, 0.015, -0.005])
            >>> excess = manager.calculate_excess_returns(fund_returns, benchmark_returns)
            >>> print(excess)
            0    0.002
            1    0.005
            2   -0.005
            dtype: float64
        """
        if fund_returns.index.equals(benchmark_returns.index):
            # Same index, direct calculation
            excess_returns = fund_returns - benchmark_returns
        else:
            # Different indices, align first
            aligned = pd.concat([fund_returns, benchmark_returns], axis=1, join='inner')
            excess_returns = aligned.iloc[:, 0] - aligned.iloc[:, 1]

        logger.debug(f"Calculated {len(excess_returns)} excess return values")
        return excess_returns

    def get_appropriate_benchmark(
        self,
        fund_category: str,
        fund_sector: str | None = None,
    ) -> str:
        """
        Get appropriate benchmark code for a fund.

        Benchmark mapping logic:
        - Broad/mixed funds: '000300.SH' (CSI 300)
        - Mid-cap: '000905.SH' (CSI 500)
        - Small-cap: '399406.SZ' (CSI 1000)
        - Tech: '399006.SZ' (CSI Tech)
        - Semiconductor: '399006.SZ' + sector override
        - New energy: '399412.SZ' (CSI New Energy)
        - Healthcare: '399911.SZ' (CSI Healthcare)
        - Consumer: '399932.SZ' (CSI Consumer)
        - Financial: '399975.SZ' (CSI Financial)
        - Bond funds: 'CBA00101.CS' (China Bond Composite)

        Args:
            fund_category: Fund category (e.g., '宽基', '科技', '债券')
            fund_sector: Optional fund sector for more specific matching

        Returns:
            Benchmark index code (e.g., '000300.SH')

        Examples:
            >>> manager.get_appropriate_benchmark("宽基")
            '000300.SH'
            >>> manager.get_appropriate_benchmark("科技", "半导体")
            '399006.SZ'
        """
        logger.debug(f"Getting appropriate benchmark for category={fund_category}, sector={fund_sector}")

        # Use repository to find matching benchmark
        benchmark = self.repo.get_benchmark_for_fund(fund_category, fund_sector)

        if benchmark:
            logger.info(f"Selected benchmark {benchmark.index_code} for {fund_category}")
            return benchmark.index_code

        # Fall back to default benchmarks
        if "债券" in fund_category or "货币" in fund_category:
            logger.info(f"Using China Bond Composite for bond fund category {fund_category}")
            return STANDARD_BENCHMARK_CODES["CHINA_BOND_COMPOSITE"]
        else:
            logger.info(f"Using CSI 300 as default benchmark for category {fund_category}")
            return STANDARD_BENCHMARK_CODES["CSI_300"]

    def get_tracking_error(
        self,
        fund_returns: pd.Series,
        benchmark_code: str,
    ) -> float | None:
        """
        Calculate tracking error for a fund relative to benchmark.

        Formula: std(R_fund - R_benchmark) * sqrt(252)

        Annualized standard deviation of excess returns.

        Args:
            fund_returns: Fund returns Series indexed by date
            benchmark_code: Benchmark index code

        Returns:
            Annualized tracking error as percentage (e.g., 5.23 for 5.23%)
            None if calculation fails
        """
        try:
            # Align returns
            fund_aligned, benchmark_aligned = self.align_fund_to_benchmark(
                fund_returns, benchmark_code
            )

            if fund_aligned.empty or benchmark_aligned.empty:
                logger.warning("Cannot calculate tracking error: no aligned data")
                return None

            # Calculate excess returns
            excess_returns = self.calculate_excess_returns(fund_aligned, benchmark_aligned)

            # Calculate tracking error (annualized)
            tracking_error = excess_returns.std() * np.sqrt(252) * 100

            logger.debug(f"Tracking error for {benchmark_code}: {tracking_error:.2f}%")
            return float(tracking_error)

        except Exception as e:
            logger.error(f"Failed to calculate tracking error: {e}")
            return None

    def get_information_ratio(
        self,
        fund_returns: pd.Series,
        benchmark_code: str,
    ) -> float | None:
        """
        Calculate Information Ratio for a fund relative to benchmark.

        Formula: (R_fund - R_benchmark) / tracking_error

        Where:
            - R_fund = Mean annualized fund return
            - R_benchmark = Mean annualized benchmark return
            - tracking_error = Annualized standard deviation of excess returns

        Measures excess return per unit of tracking risk.

        Args:
            fund_returns: Fund returns Series indexed by date
            benchmark_code: Benchmark index code

        Returns:
            Information Ratio (dimensionless)
            None if calculation fails
        """
        try:
            # Align returns
            fund_aligned, benchmark_aligned = self.align_fund_to_benchmark(
                fund_returns, benchmark_code
            )

            if fund_aligned.empty or benchmark_aligned.empty:
                logger.warning("Cannot calculate IR: no aligned data")
                return None

            # Calculate excess returns
            excess_returns = self.calculate_excess_returns(fund_aligned, benchmark_aligned)

            # Calculate tracking error
            tracking_error = excess_returns.std() * np.sqrt(252)

            if tracking_error == 0:
                logger.warning("Tracking error is zero, cannot calculate IR")
                return None

            # Calculate mean excess return (annualized)
            mean_excess_return = excess_returns.mean() * 252

            # Calculate Information Ratio
            information_ratio = mean_excess_return / tracking_error

            logger.debug(f"Information Ratio for {benchmark_code}: {information_ratio:.4f}")
            return float(information_ratio)

        except Exception as e:
            logger.error(f"Failed to calculate Information Ratio: {e}")
            return None

    def get_up_down_capture(
        self,
        fund_returns: pd.Series,
        benchmark_code: str,
    ) -> dict[str, float | None]:
        """
        Calculate up/down market capture ratios.

        Returns:
            Dictionary with:
                - up_capture: Fund return / Benchmark return in up markets
                - down_capture: Fund return / Benchmark return in down markets

        Methodology:
            - Identify up markets: benchmark return > 0
            - Identify down markets: benchmark return < 0
            - Calculate capture ratios as regression slopes
            - Ideal: up_capture > 100%, down_capture < 100%

        Args:
            fund_returns: Fund returns Series indexed by date
            benchmark_code: Benchmark index code

        Returns:
            Dictionary with up_capture and down_capture percentages
        """
        try:
            # Align returns
            fund_aligned, benchmark_aligned = self.align_fund_to_benchmark(
                fund_returns, benchmark_code
            )

            if fund_aligned.empty or benchmark_aligned.empty:
                logger.warning("Cannot calculate capture ratios: no aligned data")
                return {'up_capture': None, 'down_capture': None}

            # Identify up and down markets
            up_mask = benchmark_aligned > 0
            down_mask = benchmark_aligned < 0

            if up_mask.sum() == 0 or down_mask.sum() == 0:
                logger.warning("Insufficient data for capture ratio calculation")
                return {'up_capture': None, 'down_capture': None}

            # Calculate up capture: (fund_up / benchmark_up) geometric mean
            fund_up = fund_aligned[up_mask]
            benchmark_up = benchmark_aligned[up_mask]

            # Compound return formula: (1 + r1) * (1 + r2) * ... - 1
            fund_up_cumulative = (1 + fund_up).prod() - 1
            benchmark_up_cumulative = (1 + benchmark_up).prod() - 1

            up_capture = (
                (fund_up_cumulative / benchmark_up_cumulative * 100)
                if benchmark_up_cumulative != 0
                else None
            )

            # Calculate down capture
            fund_down = fund_aligned[down_mask]
            benchmark_down = benchmark_aligned[down_mask]

            fund_down_cumulative = (1 + fund_down).prod() - 1
            benchmark_down_cumulative = (1 + benchmark_down).prod() - 1

            down_capture = (
                (fund_down_cumulative / benchmark_down_cumulative * 100)
                if benchmark_down_cumulative != 0
                else None
            )

            logger.debug(
                f"Capture ratios for {benchmark_code}: "
                f"up={up_capture:.2f}%, down={down_capture:.2f}%"
            )

            return {
                'up_capture': float(up_capture) if up_capture is not None else None,
                'down_capture': float(down_capture) if down_capture is not None else None,
            }

        except Exception as e:
            logger.error(f"Failed to calculate capture ratios: {e}")
            return {'up_capture': None, 'down_capture': None}

    def backfill_all_benchmarks(self, lookback_years: int = 5) -> dict[str, any]:
        """
        Backfill historical data for all benchmarks.

        Convenience method that delegates to fetcher.

        Args:
            lookback_years: Number of years to look back (default: 5)

        Returns:
            Dictionary with statistics
        """
        logger.info(f"Starting benchmark backfill (lookback: {lookback_years} years)")
        return self.fetcher.backfill_all_benchmarks(lookback_years)

    def incremental_update(self) -> dict[str, int]:
        """
        Perform daily incremental update for all benchmarks.

        Convenience method that delegates to fetcher.

        Returns:
            Dictionary with statistics
        """
        logger.info("Starting benchmark incremental update")
        return self.fetcher.incremental_update()

    def get_benchmark_info(self, index_code: str) -> dict[str, any] | None:
        """
        Get comprehensive benchmark information.

        Args:
            index_code: Benchmark index code

        Returns:
            Dictionary with benchmark info or None if not found
        """
        benchmark = self.repo.get_benchmark(index_code)

        if not benchmark:
            return None

        # Get date range
        min_date, max_date = self.repo.get_history_date_range(index_code)

        # Get latest price
        latest_price = self.repo.get_latest_price(index_code)

        return {
            'index_code': benchmark.index_code,
            'index_name': benchmark.index_name,
            'index_type': benchmark.index_type,
            'market': benchmark.market,
            'base_date': benchmark.base_date,
            'base_value': benchmark.base_value,
            'constituents_count': benchmark.constituents_count,
            'suitable_for_categories': benchmark.suitable_for_categories,
            'data_source': benchmark.data_source,
            'update_frequency': benchmark.update_frequency,
            'description': benchmark.description,
            'data_range': {
                'start_date': min_date,
                'end_date': max_date,
                'latest_price': latest_price,
            },
        }
