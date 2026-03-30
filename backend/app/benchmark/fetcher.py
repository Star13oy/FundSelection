"""
Benchmark data fetcher from akshare and other sources.

This module implements data fetching for Chinese A-share benchmark indices
from multiple sources, with akshare as the primary provider.

Critical infrastructure: Without reliable benchmark data fetching,
relative performance calculations cannot be performed.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from time import sleep
from typing import Any

import numpy as np
import pandas as pd

from app.benchmark.models import BenchmarkHistory, BenchmarkIndex
from app.benchmark.repository import BenchmarkRepository
from app.db import get_adapter

logger = logging.getLogger(__name__)

# Fetch configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0  # seconds
BATCH_SIZE = 1000
MAX_WORKERS = 5


class BenchmarkFetcher:
    """Fetch benchmark index data from various sources.

    Supports:
    - akshare: Primary data source for Chinese indices
    - Eastmoney API: Fallback source (to be implemented)
    - Automatic symbol format conversion
    - Bulk backfill for all benchmarks
    - Daily incremental updates

    Attributes:
        adapter: Database adapter
        repo: BenchmarkRepository instance

    Examples:
        >>> fetcher = BenchmarkFetcher(get_adapter())
        >>> df = fetcher.fetch_index_history("000300.SH")
        >>> print(df.head())
    """

    def __init__(self, adapter: Any) -> None:
        """
        Initialize benchmark fetcher.

        Args:
            adapter: Database adapter instance
        """
        self.adapter = adapter
        self.repo = BenchmarkRepository(adapter)

    def fetch_index_history(
        self,
        index_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch historical index data.

        Data sources (tried in order):
        1. akshare: Primary source for Chinese indices
        2. Eastmoney API: Fallback (not yet implemented)

        Args:
            index_code: Index code (e.g., '000300.SH', '399001.SZ')
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            DataFrame with columns:
            - date (trade_date)
            - close (close_price)
            - open (open_price)
            - high (high_price)
            - low (low_price)
            - volume

            Empty DataFrame if fetch fails
        """
        logger.info(f"Fetching index history for {index_code}")

        # Try akshare first
        df = self.fetch_akshare_index(index_code)

        if df.empty:
            logger.warning(f"Failed to fetch {index_code} from akshare")
            return pd.DataFrame()

        # Filter by date range if specified
        if start_date:
            df = df[df['date'] >= pd.Timestamp(start_date)]

        if end_date:
            df = df[df['date'] <= pd.Timestamp(end_date)]

        logger.info(f"Fetched {len(df)} records for {index_code}")
        return df

    def fetch_akshare_index(self, index_code: str) -> pd.DataFrame:
        """
        Fetch from akshare.

        Uses:
        - ak.stock_zh_index_daily() for SH/SZ indices
        - ak.index_zh_a_hist() for CSI indices

        Symbol format conversion:
        - '000300.SH' → 'sh000300'
        - '399001.SZ' → 'sz399001'

        Args:
            index_code: Index code in standard format

        Returns:
            DataFrame with price history

        Note:
            Implements exponential backoff retry on failures (3 attempts)
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                import akshare as ak

                logger.info(
                    f"Fetching index {index_code} from akshare "
                    f"(attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS})"
                )

                # Convert symbol format for akshare
                akshare_symbol = self._convert_symbol_format(index_code, "akshare")
                logger.debug(f"Converted {index_code} to {akshare_symbol}")

                # Try different akshare functions based on market
                if index_code.endswith('.SH'):
                    # Shanghai index
                    df = ak.stock_zh_index_daily(symbol=akshare_symbol)
                elif index_code.endswith('.SZ'):
                    # Shenzhen index
                    df = ak.stock_zh_index_daily(symbol=akshare_symbol)
                elif index_code.endswith('.CS'):
                    # China Bond index (different API)
                    logger.warning(f"China Bond indices not yet supported: {index_code}")
                    return pd.DataFrame()
                else:
                    logger.warning(f"Unknown market for index: {index_code}")
                    return pd.DataFrame()

                if df.empty:
                    logger.warning(f"No data returned for index {index_code}")
                    return pd.DataFrame()

                # Normalize column names
                column_map = {
                    "date": "date",
                    "close": "close",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "volume": "volume",
                }

                # Select available columns
                available_columns = [col for col in column_map if col in df.columns]
                df = df[available_columns].copy()
                df.rename(columns=column_map, inplace=True)

                # Convert date column
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])

                # Sort by date ascending
                df = df.sort_values("date").reset_index(drop=True)

                logger.debug(f"Fetched {len(df)} records for {index_code} from akshare")
                return df

            except ImportError:
                logger.error("akshare not installed - cannot fetch benchmark data")
                return pd.DataFrame()
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Failed to fetch index {index_code} from akshare "
                        f"(attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to fetch index {index_code} from akshare "
                        f"after {MAX_RETRY_ATTEMPTS} attempts: {e}"
                    )

        # Should not reach here, but handle the case
        if last_error is not None:
            logger.error(f"Final error for {index_code}: {last_error}")

        return pd.DataFrame()

    def _convert_symbol_format(self, index_code: str, to_format: str) -> str:
        """
        Convert index code format.

        Examples:
            - '000300.SH' → 'sh000300' (akshare format)
            - 'sh000300' → '000300.SH' (standard format)
            - '399001.SZ' → 'sz399001' (akshare format)

        Args:
            index_code: Index code in any format
            to_format: Target format ('akshare' or 'standard')

        Returns:
            Converted index code
        """
        if to_format == "akshare":
            # Convert '000300.SH' → 'sh000300'
            if '.' in index_code:
                code, market = index_code.split('.')
                return f"{market.lower()}{code}"
            else:
                # Already in akshare format or unknown
                return index_code

        elif to_format == "standard":
            # Convert 'sh000300' → '000300.SH'
            if '.' not in index_code and len(index_code) >= 9:
                # Assume format like 'sh000300' or 'sz399001'
                market = index_code[:2].upper()
                code = index_code[2:]
                return f"{code}.{market}"
            else:
                # Already in standard format
                return index_code

        else:
            logger.warning(f"Unknown target format: {to_format}")
            return index_code

    def backfill_all_benchmarks(self, lookback_years: int = 5) -> dict[str, Any]:
        """
        Backfill historical data for all benchmarks.

        Fetches historical data for all benchmark indices in the database.
        Uses parallel processing with ThreadPoolExecutor.

        Args:
            lookback_years: Number of years to look back (default: 5)

        Returns:
            Dictionary with statistics:
            {
                'total': int,
                'success': int,
                'failed': int,
                'errors': list[str]
            }
        """
        logger.info(f"Starting backfill for all benchmarks (lookback: {lookback_years} years)")

        # Get all benchmarks
        benchmarks = self.repo.list_benchmarks()

        if not benchmarks:
            logger.warning("No benchmarks found in database")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'errors': ['No benchmarks found']
            }

        stats = {
            'total': len(benchmarks),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        # Calculate start date
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_years * 365)

        # Parallel fetch with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_benchmark = {
                executor.submit(
                    self._backfill_single_benchmark,
                    benchmark.index_code,
                    start_date,
                    end_date
                ): benchmark
                for benchmark in benchmarks
            }

            for future in as_completed(future_to_benchmark):
                benchmark = future_to_benchmark[future]
                try:
                    success = future.result()
                    if success:
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                        stats['errors'].append(f"Failed to backfill {benchmark.index_code}")
                except Exception as e:
                    logger.error(f"Backfill failed for benchmark {benchmark.index_code}: {e}")
                    stats['failed'] += 1
                    stats['errors'].append(f"{benchmark.index_code}: {str(e)}")

        logger.info(
            f"Backfill completed: {stats['success']} success, "
            f"{stats['failed']} failed"
        )

        return stats

    def _backfill_single_benchmark(
        self,
        index_code: str,
        start_date: date,
        end_date: date,
    ) -> bool:
        """
        Backfill historical data for a single benchmark.

        Args:
            index_code: Benchmark index code
            start_date: Start date
            end_date: End date

        Returns:
            True if success, False otherwise
        """
        try:
            # Fetch historical data
            df = self.fetch_index_history(index_code, start_date, end_date)

            if df.empty:
                logger.warning(f"No data available for benchmark {index_code}")
                return False

            # Calculate daily returns
            df = self.calculate_daily_returns(df)

            # Convert to BenchmarkHistory models
            history_records = []
            for _, row in df.iterrows():
                record = BenchmarkHistory(
                    index_code=index_code,
                    trade_date=row['date'].date(),
                    close_price=float(row['close']),
                    open_price=float(row['open']) if pd.notna(row.get('open')) else None,
                    high_price=float(row['high']) if pd.notna(row.get('high')) else None,
                    low_price=float(row['low']) if pd.notna(row.get('low')) else None,
                    volume=float(row['volume']) if pd.notna(row.get('volume')) else None,
                    daily_return=float(row['daily_return']) if pd.notna(row.get('daily_return')) else None,
                )
                history_records.append(record)

            # Bulk insert
            result = self.repo.bulk_insert_history(history_records)

            return result['success'] > 0

        except Exception as e:
            logger.error(f"Failed to backfill benchmark {index_code}: {e}")
            return False

    def incremental_update(self) -> dict[str, int]:
        """
        Daily incremental update for all benchmarks.

        Fetches latest data point for each benchmark and appends new records.
        Only adds records that don't already exist.

        Returns:
            Dictionary with statistics: total, success, failed, added
        """
        logger.info("Starting incremental update for all benchmarks")

        # Get all benchmarks
        benchmarks = self.repo.list_benchmarks()

        if not benchmarks:
            logger.warning("No benchmarks found in database")
            return {'total': 0, 'success': 0, 'failed': 0, 'added': 0}

        stats = {'total': len(benchmarks), 'success': 0, 'failed': 0, 'added': 0}

        # Parallel update with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_benchmark = {
                executor.submit(self._incremental_update_single_benchmark, benchmark.index_code): benchmark
                for benchmark in benchmarks
            }

            for future in as_completed(future_to_benchmark):
                benchmark = future_to_benchmark[future]
                try:
                    added_count = future.result()
                    if added_count >= 0:
                        stats['success'] += 1
                        stats['added'] += added_count
                    else:
                        stats['failed'] += 1
                except Exception as e:
                    logger.error(f"Incremental update failed for benchmark {benchmark.index_code}: {e}")
                    stats['failed'] += 1

        logger.info(
            f"Incremental update completed: {stats['success']} success, "
            f"{stats['failed']} failed, {stats['added']} records added"
        )

        return stats

    def _incremental_update_single_benchmark(self, index_code: str) -> int:
        """
        Perform incremental update for a single benchmark.

        Args:
            index_code: Benchmark index code

        Returns:
            Number of new records added, or -1 if failed
        """
        try:
            # Get latest date in database
            min_date, max_date = self.repo.get_history_date_range(index_code)

            if max_date is None:
                # No existing data, do full backfill (last 5 years)
                end_date = date.today()
                start_date = end_date - timedelta(days=5 * 365)
                df = self.fetch_index_history(index_code, start_date, end_date)
            else:
                # Fetch new data (last 30 days to be safe)
                start_date = max_date + timedelta(days=1)
                end_date = date.today() + timedelta(days=7)  # Buffer for future dates
                df = self.fetch_index_history(index_code, start_date, end_date)

            if df.empty:
                logger.debug(f"No new data for benchmark {index_code}")
                return 0

            # Filter only new records
            if max_date:
                df = df[df['date'] > pd.Timestamp(max_date)]

            if df.empty:
                logger.debug(f"No new records to add for benchmark {index_code}")
                return 0

            # Calculate daily returns
            df = self.calculate_daily_returns(df)

            # Convert to BenchmarkHistory models
            history_records = []
            for _, row in df.iterrows():
                record = BenchmarkHistory(
                    index_code=index_code,
                    trade_date=row['date'].date(),
                    close_price=float(row['close']),
                    open_price=float(row['open']) if pd.notna(row.get('open')) else None,
                    high_price=float(row['high']) if pd.notna(row.get('high')) else None,
                    low_price=float(row['low']) if pd.notna(row.get('low')) else None,
                    volume=float(row['volume']) if pd.notna(row.get('volume')) else None,
                    daily_return=float(row['daily_return']) if pd.notna(row.get('daily_return')) else None,
                )
                history_records.append(record)

            # Store new records
            success_count = 0
            for record in history_records:
                if self.repo.insert_history(record):
                    success_count += 1

            logger.debug(f"Added {success_count} new records for benchmark {index_code}")
            return success_count

        except Exception as e:
            logger.error(f"Failed incremental update for benchmark {index_code}: {e}")
            return -1

    def calculate_daily_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily returns from price data.

        Formula: (P_t - P_{t-1}) / P_{t-1}

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with added 'daily_return' column
        """
        if df.empty or 'close' not in df.columns:
            logger.warning("Cannot calculate daily returns: empty DataFrame or missing 'close' column")
            return df

        # Sort by date to ensure correct calculation
        df = df.sort_values('date').reset_index(drop=True)

        # Calculate daily return: (P_t - P_{t-1}) / P_{t-1}
        df['daily_return'] = df['close'].pct_change()

        # First row has NaN return (no previous day)
        # This is expected and will be stored as NULL in database

        logger.debug(f"Calculated daily returns for {len(df)} records")
        return df

    def validate_benchmark_data(self, df: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        Validate benchmark data quality.

        Checks:
        - No missing dates
        - Price values > 0
        - daily_return in [-20%, +20%] (China limits)
        - No duplicate dates
        - Chronological order

        Args:
            df: DataFrame with benchmark data

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if df.empty:
            errors.append("DataFrame is empty")
            return False, errors

        # Check required columns
        required_columns = ["date", "close"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            return False, errors

        # Check for missing values
        if df["date"].isnull().any():
            errors.append("Missing dates found")
        if df["close"].isnull().any():
            errors.append("Missing close prices")

        # Check price values are positive
        if (df["close"] <= 0).any():
            errors.append("Close prices must be > 0")

        # Check daily_return range if present
        if "daily_return" in df.columns:
            invalid_returns = df[
                (df["daily_return"] < -0.20) | (df["daily_return"] > 0.20)
            ]
            if not invalid_returns.empty:
                errors.append(
                    f"daily_return out of range [-20%, +20%]: "
                    f"{len(invalid_returns)} records"
                )

        # Check for duplicate dates
        if df["date"].duplicated().any():
            duplicate_count = df["date"].duplicated().sum()
            errors.append(f"Duplicate dates found: {duplicate_count} records")

        # Check chronological order
        if not df["date"].is_monotonic_increasing:
            errors.append("Dates are not in chronological order")

        is_valid = len(errors) == 0
        return is_valid, errors
