"""
NAV (Net Asset Value) historical data management for Chinese A-share funds.

This module provides production-grade NAV history storage and retrieval,
supporting both ETFs and open-end funds with comprehensive validation,
error handling, and performance optimizations.

Critical infrastructure: Without NAV historical data, factor calculations
are impossible. This module stores time-series data, not just snapshots.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from time import sleep
from typing import Any

import pandas as pd

from app.db import get_adapter

logger = logging.getLogger(__name__)

# Chinese A-share trading constraints
MAX_DAILY_RETURN = 0.20  # 20% (2x limit for errors)
MIN_DAILY_RETURN = -0.20  # -20%
MIN_RECORDS = 252  # 1 year of trading days
BATCH_SIZE = 1000  # Records per batch for bulk insert
MAX_WORKERS = 5  # Parallel workers for backfill


class NAVHistoryManager:
    """
    Manager for NAV historical data operations.

    Supports:
    - Fetching NAV history from akshare (ETFs and open-end funds)
    - Storing with duplicate handling (UPSERT)
    - Retrieving with date range filtering
    - Batch backfill for all funds
    - Daily incremental updates
    """

    def __init__(self) -> None:
        """Initialize NAV history manager with database adapter."""
        self.adapter = get_adapter()
        self._cache: dict[str, pd.DataFrame] = {}

    def fetch_historical_nav(self, fund_code: str, fund_type: str) -> pd.DataFrame:
        """
        Fetch historical NAV data from akshare.

        Args:
            fund_code: Fund code (6-digit string)
            fund_type: Fund type - "equity" (ETF) or "bond" (open-end fund)

        Returns:
            DataFrame with columns: date, unit_nav, accumulated_nav, daily_return
            Empty DataFrame if fetch fails

        Raises:
            ValueError: If fund_type is invalid
        """
        if fund_type == "equity":
            return self._fetch_etf_nav(fund_code)
        elif fund_type == "bond":
            return self._fetch_open_fund_nav(fund_code)
        else:
            raise ValueError(f"Invalid fund_type: {fund_type}. Must be 'equity' or 'bond'")

    def _fetch_etf_nav(self, fund_code: str) -> pd.DataFrame:
        """
        Fetch ETF NAV history from akshare.

        Uses: ak.fund_etf_hist_em(symbol=code)

        Args:
            fund_code: ETF fund code

        Returns:
            DataFrame with NAV history

        Note:
            Implements exponential backoff retry on failures (3 attempts)
        """
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                import akshare as ak

                logger.info(f"Fetching ETF NAV history for {fund_code} (attempt {attempt + 1}/3)")
                df = ak.fund_etf_hist_em(symbol=fund_code)

                # Normalize column names
                if df.empty:
                    logger.warning(f"No NAV data returned for ETF {fund_code}")
                    return pd.DataFrame()

                # Map akshare columns to our schema
                column_map = {
                    "日期": "date",
                    "收盘": "unit_nav",
                    "涨跌幅": "daily_return",
                }

                # Select available columns
                available_columns = [col for col in column_map if col in df.columns]
                df = df[available_columns].copy()
                df.rename(columns=column_map, inplace=True)

                # Convert date to datetime
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"]).dt.date

                # accumulated_nav is not available for ETFs, set equal to unit_nav
                if "accumulated_nav" not in df.columns and "unit_nav" in df.columns:
                    df["accumulated_nav"] = df["unit_nav"]

                # Validate data
                is_valid, errors = validate_nav_data(df)
                if not is_valid:
                    logger.warning(f"NAV data validation failed for ETF {fund_code}: {errors}")
                    # Return partial data anyway - log warning but don't fail

                logger.debug(f"Fetched {len(df)} NAV records for ETF {fund_code}")
                return df

            except ImportError:
                logger.error("akshare not installed - cannot fetch NAV data")
                return pd.DataFrame()
            except Exception as e:
                last_error = e
                if attempt < 2:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 1.0 * (2 ** attempt)
                    logger.warning(
                        f"Failed to fetch ETF NAV for {fund_code} (attempt {attempt + 1}/3): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch ETF NAV for {fund_code} after 3 attempts: {e}")
                    raise

        # Should not reach here, but handle the case
        if last_error is not None:
            raise last_error
        return pd.DataFrame()

    def _fetch_open_fund_nav(self, fund_code: str) -> pd.DataFrame:
        """
        Fetch open-end fund NAV history from akshare.

        Uses: ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")

        Args:
            fund_code: Open-end fund code

        Returns:
            DataFrame with NAV history

        Note:
            Implements exponential backoff retry on failures (3 attempts)
        """
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                import akshare as ak

                logger.info(f"Fetching open-end fund NAV history for {fund_code} (attempt {attempt + 1}/3)")
                df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

                # Normalize column names
                if df.empty:
                    logger.warning(f"No NAV data returned for fund {fund_code}")
                    return pd.DataFrame()

                # Map akshare columns to our schema
                column_map = {
                    "净值日期": "date",
                    "单位净值": "unit_nav",
                    "累计净值": "accumulated_nav",
                    "日增长率": "daily_return",
                }

                # Select available columns
                available_columns = [col for col in column_map if col in df.columns]
                df = df[available_columns].copy()
                df.rename(columns=column_map, inplace=True)

                # Convert date to datetime
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"]).dt.date

                # Convert percentage to decimal (akshare returns "1.23%" format)
                if "daily_return" in df.columns:
                    df["daily_return"] = (
                        df["daily_return"]
                        .astype(str)
                        .str.replace("%", "")
                        .astype(float)
                        / 100
                    )

                # Validate data
                is_valid, errors = validate_nav_data(df)
                if not is_valid:
                    logger.warning(f"NAV data validation failed for fund {fund_code}: {errors}")

                logger.debug(f"Fetched {len(df)} NAV records for fund {fund_code}")
                return df

            except ImportError:
                logger.error("akshare not installed - cannot fetch NAV data")
                return pd.DataFrame()
            except Exception as e:
                last_error = e
                if attempt < 2:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 1.0 * (2 ** attempt)
                    logger.warning(
                        f"Failed to fetch open-end fund NAV for {fund_code} (attempt {attempt + 1}/3): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch open-end fund NAV for {fund_code} after 3 attempts: {e}")
                    raise

        # Should not reach here, but handle the case
        if last_error is not None:
            raise last_error
        return pd.DataFrame()

    def store_nav_history(self, fund_code: str, nav_data: pd.DataFrame) -> bool:
        """
        Store NAV history to database with duplicate handling.

        Uses UPSERT (INSERT ... ON CONFLICT/ON DUPLICATE KEY UPDATE)
        to handle duplicates gracefully. Batch inserts for performance.

        Args:
            fund_code: Fund code
            nav_data: DataFrame with NAV history (must have columns: date, unit_nav, accumulated_nav)

        Returns:
            True if storage succeeded, False otherwise
        """
        if nav_data.empty:
            logger.warning(f"No NAV data to store for fund {fund_code}")
            return False

        required_columns = ["date", "unit_nav", "accumulated_nav"]
        missing_columns = [col for col in required_columns if col not in nav_data.columns]

        if missing_columns:
            logger.error(
                f"Missing required columns for fund {fund_code}: {missing_columns}"
            )
            return False

        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                # Generate UPSERT SQL
                columns = ["fund_code", "date", "unit_nav", "accumulated_nav", "daily_return"]
                update_columns = ["unit_nav", "accumulated_nav", "daily_return"]
                upsert_sql = self.adapter.get_upsert_syntax(
                    "fund_nav_history", columns, update_columns
                )

                # Prepare records for batch insert
                records = []
                for _, row in nav_data.iterrows():
                    records.append(
                        {
                            "fund_code": fund_code,
                            "date": row["date"],
                            "unit_nav": float(row["unit_nav"]),
                            "accumulated_nav": float(row["accumulated_nav"]),
                            "daily_return": float(row["daily_return"])
                            if pd.notna(row.get("daily_return"))
                            else None,
                        }
                    )

                # Batch insert (1000 records at a time)
                success_count = 0
                for i in range(0, len(records), BATCH_SIZE):
                    batch = records[i : i + BATCH_SIZE]
                    batch_params = [
                        (
                            rec["fund_code"],
                            rec["date"],
                            rec["unit_nav"],
                            rec["accumulated_nav"],
                            rec["daily_return"],
                        )
                        for rec in batch
                    ]

                    cursor.executemany(upsert_sql, batch_params)
                    success_count += len(batch)
                    logger.debug(f"Stored batch {i // BATCH_SIZE + 1} for fund {fund_code}")

                conn.commit()
                logger.info(
                    f"Stored {success_count} NAV records for fund {fund_code}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to store NAV history for fund {fund_code}: {e}")
            return False

    def get_nav_history(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        Retrieve NAV history for a fund from database.

        Args:
            fund_code: Fund code
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            DataFrame with NAV history, sorted by date ascending
            Empty DataFrame if no data found
        """
        try:
            # Check cache first
            cache_key = f"{fund_code}_{start_date}_{end_date}"
            if cache_key in self._cache:
                logger.debug(f"Cache hit for {fund_code} NAV history")
                return self._cache[cache_key].copy()

            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                # Build query with optional date filtering
                sql = "SELECT date, unit_nav, accumulated_nav, daily_return FROM fund_nav_history WHERE fund_code = %s"
                params = [fund_code]

                if start_date:
                    sql += " AND date >= %s"
                    params.append(start_date)

                if end_date:
                    sql += " AND date <= %s"
                    params.append(end_date)

                sql += " ORDER BY date ASC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                if not rows:
                    logger.warning(f"No NAV history found for fund {fund_code}")
                    return pd.DataFrame()

                df = pd.DataFrame(rows)

                # Cache for repeated access
                self._cache[cache_key] = df.copy()

                logger.debug(f"Retrieved {len(df)} NAV records for fund {fund_code}")
                return df

        except Exception as e:
            logger.error(f"Failed to retrieve NAV history for fund {fund_code}: {e}")
            return pd.DataFrame()

    def backfill_all_funds(self, max_age_days: int = 7) -> dict[str, int]:
        """
        Backfill NAV history for all funds in the database.

        Only updates funds whose NAV data is older than max_age_days.
        Uses parallel processing with ThreadPoolExecutor.

        Args:
            max_age_days: Only update funds older than this many days

        Returns:
            Dictionary with statistics: total, success, failed, skipped
        """
        from app.universe import load_fund_universe

        funds = load_fund_universe()
        logger.info(f"Starting backfill for {len(funds)} funds")

        stats = {"total": len(funds), "success": 0, "failed": 0, "skipped": 0}

        # Get last update time for each fund
        fund_last_update = self._get_last_update_times()

        # Filter funds that need updating
        funds_to_update = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        for fund in funds:
            last_update = fund_last_update.get(fund.code)
            if last_update is None or last_update < cutoff_date:
                funds_to_update.append(fund)
            else:
                stats["skipped"] += 1

        logger.info(
            f"Updating {len(funds_to_update)} funds, skipping {stats['skipped']} recent funds"
        )

        # Parallel fetch with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_fund = {
                executor.submit(
                    self._backfill_single_fund, fund.code, fund.fund_type
                ): fund
                for fund in funds_to_update
            }

            for future in as_completed(future_to_fund):
                fund = future_to_fund[future]
                try:
                    success = future.result()
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Backfill failed for fund {fund.code}: {e}")
                    stats["failed"] += 1

        logger.info(
            f"Backfill completed: {stats['success']} success, {stats['failed']} failed, {stats['skipped']} skipped"
        )
        return stats

    def _backfill_single_fund(self, fund_code: str, fund_type: str) -> bool:
        """
        Backfill NAV history for a single fund.

        Args:
            fund_code: Fund code
            fund_type: Fund type (equity/bond)

        Returns:
            True if success, False otherwise
        """
        try:
            nav_data = self.fetch_historical_nav(fund_code, fund_type)
            if nav_data.empty:
                logger.warning(f"No NAV data available for fund {fund_code}")
                return False

            return self.store_nav_history(fund_code, nav_data)
        except Exception as e:
            logger.error(f"Failed to backfill fund {fund_code}: {e}")
            return False

    def _get_last_update_times(self) -> dict[str, datetime]:
        """
        Get last update time for all funds.

        Returns:
            Dictionary mapping fund_code to last_update datetime
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT fund_code, MAX(created_at) as last_update
                    FROM fund_nav_history
                    GROUP BY fund_code
                """

                cursor.execute(sql)
                rows = cursor.fetchall()

                return {row["fund_code"]: row["last_update"] for row in rows}

        except Exception as e:
            logger.error(f"Failed to get last update times: {e}")
            return {}

    def incremental_update(self) -> dict[str, int]:
        """
        Perform daily incremental update for all funds.

        Fetches the latest NAV data for all funds and appends new records.
        Only adds records that don't already exist.

        Returns:
            Dictionary with statistics: total, success, failed, added
        """
        from app.universe import load_fund_universe

        funds = load_fund_universe()
        logger.info(f"Starting incremental update for {len(funds)} funds")

        stats = {"total": len(funds), "success": 0, "failed": 0, "added": 0}

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_fund = {
                executor.submit(
                    self._incremental_update_single_fund, fund.code, fund.fund_type
                ): fund
                for fund in funds
            }

            for future in as_completed(future_to_fund):
                fund = future_to_fund[future]
                try:
                    added_count = future.result()
                    if added_count >= 0:
                        stats["success"] += 1
                        stats["added"] += added_count
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Incremental update failed for fund {fund.code}: {e}")
                    stats["failed"] += 1

        logger.info(
            f"Incremental update completed: {stats['success']} success, {stats['failed']} failed, {stats['added']} records added"
        )
        return stats

    def _incremental_update_single_fund(self, fund_code: str, fund_type: str) -> int:
        """
        Perform incremental update for a single fund.

        Args:
            fund_code: Fund code
            fund_type: Fund type

        Returns:
            Number of new records added, or -1 if failed
        """
        try:
            # Get latest date in database
            existing_df = self.get_nav_history(fund_code)
            if existing_df.empty:
                # No existing data, do full backfill
                nav_data = self.fetch_historical_nav(fund_code, fund_type)
                if nav_data.empty:
                    return 0
                self.store_nav_history(fund_code, nav_data)
                return len(nav_data)

            latest_date = existing_df["date"].max()

            # Fetch new data (last 30 days to be safe)
            nav_data = self.fetch_historical_nav(fund_code, fund_type)
            if nav_data.empty:
                return 0

            # Filter only new records
            new_data = nav_data[nav_data["date"] > latest_date]
            if new_data.empty:
                logger.debug(f"No new NAV data for fund {fund_code}")
                return 0

            # Store new records
            self.store_nav_history(fund_code, new_data)
            logger.debug(f"Added {len(new_data)} new NAV records for fund {fund_code}")
            return len(new_data)

        except Exception as e:
            logger.error(f"Failed incremental update for fund {fund_code}: {e}")
            return -1


def validate_nav_data(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate NAV data quality.

    Checks:
    - No missing dates (trading days only)
    - NAV values > 0 (unit_nav, accumulated_nav)
    - daily_return in [-20%, +20%] (China limit: 10% daily, allow 2x for errors)
    - No duplicate dates
    - Chronological order
    - At least 252 records (1 year) for meaningful calculations

    Args:
        df: DataFrame with NAV data

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if df.empty:
        errors.append("DataFrame is empty")
        return False, errors

    # Check required columns
    required_columns = ["date", "unit_nav", "accumulated_nav"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
        return False, errors

    # Check for missing values
    if df["date"].isnull().any():
        errors.append("Missing dates found")
    if df["unit_nav"].isnull().any():
        errors.append("Missing unit_nav values")
    if df["accumulated_nav"].isnull().any():
        errors.append("Missing accumulated_nav values")

    # Check NAV values are positive
    if (df["unit_nav"] <= 0).any():
        errors.append("unit_nav values must be > 0")
    if (df["accumulated_nav"] <= 0).any():
        errors.append("accumulated_nav values must be > 0")

    # Check daily_return range if present
    if "daily_return" in df.columns:
        invalid_returns = df[
            (df["daily_return"] < MIN_DAILY_RETURN) | (df["daily_return"] > MAX_DAILY_RETURN)
        ]
        if not invalid_returns.empty:
            errors.append(
                f"daily_return out of range [{MIN_DAILY_RETURN*100}%, {MAX_DAILY_RETURN*100}%]: "
                f"{len(invalid_returns)} records"
            )

    # Check for duplicate dates
    if df["date"].duplicated().any():
        duplicate_count = df["date"].duplicated().sum()
        errors.append(f"Duplicate dates found: {duplicate_count} records")

    # Check chronological order
    if not df["date"].is_monotonic_increasing:
        errors.append("Dates are not in chronological order")

    # Check minimum records (warning only - don't fail validation)
    if len(df) < MIN_RECORDS:
        # Just log this, don't add to errors
        logger.warning(
            f"Insufficient records: {len(df)} < {MIN_RECORDS} (1 year of trading days)"
        )

    is_valid = len(errors) == 0
    return is_valid, errors


def adjust_to_trading_days(date_series: pd.Series) -> pd.Series:
    """
    Adjust dates to China A-share trading calendar.

    Filters out:
    - Weekends (Saturday, Sunday)
    - Public holidays (simplified - for production use akshare holiday calendar)

    Args:
        date_series: Series of dates

    Returns:
        Filtered Series with only trading days
    """
    if date_series.empty:
        return date_series

    df = pd.DataFrame({"date": date_series})
    df["date"] = pd.to_datetime(df["date"])

    # Filter weekends
    df["weekday"] = df["date"].dt.weekday
    df = df[df["weekday"] < 5]  # Monday=0, Friday=4

    # Note: For production, use akshare holiday calendar:
    # import akshare as ak
    # holidays = ak.tool_trade_date_hist_sina()
    # df = df[~df["date"].isin(holidays)]

    return df["date"].dt.date
