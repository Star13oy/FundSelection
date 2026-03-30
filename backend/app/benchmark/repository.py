"""
Benchmark data repository for database operations.

This module provides database access layer for benchmark indices and
their historical price data. Supports both SQLite and MySQL through
the unified database adapter.

Critical infrastructure: All benchmark data access flows through this
repository, ensuring data consistency and proper error handling.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

from app.benchmark.models import BenchmarkHistory, BenchmarkIndex
from app.db import get_adapter

logger = logging.getLogger(__name__)

# Batch size for bulk inserts
BATCH_SIZE = 1000


class BenchmarkRepository:
    """Database operations for benchmark data.

    This repository handles all database interactions for benchmark indices
    and historical price data, providing a clean abstraction layer over
    the database adapter.

    Attributes:
        adapter: Database adapter (SQLite or MySQL)

    Examples:
        >>> repo = BenchmarkRepository(get_adapter())
        >>> benchmark = BenchmarkIndex(
        ...     index_code="000300.SH",
        ...     index_name="沪深300",
        ...     index_type="broad",
        ...     market="CSI",
        ...     base_date=date(2004, 12, 31),
        ...     base_value=1000,
        ...     constituents_count=300,
        ...     suitable_for_categories=["宽基", "混合"]
        ... )
        >>> repo.insert_benchmark(benchmark)
        True
    """

    def __init__(self, adapter: Any) -> None:
        """
        Initialize benchmark repository.

        Args:
            adapter: Database adapter instance (SQLiteAdapter or MySQLAdapter)
        """
        self.adapter = adapter

    def insert_benchmark(self, benchmark: BenchmarkIndex) -> bool:
        """
        Insert or update a benchmark index.

        Uses UPSERT (INSERT ... ON CONFLICT/ON DUPLICATE KEY UPDATE)
        to handle duplicates gracefully.

        Args:
            benchmark: BenchmarkIndex model instance

        Returns:
            True if insertion succeeded, False otherwise
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                # Generate UPSERT SQL
                columns = [
                    "index_code", "index_name", "index_type", "market",
                    "base_date", "base_value", "constituents_count",
                    "suitable_for_categories", "data_source", "update_frequency",
                    "description", "created_at", "updated_at"
                ]
                update_columns = [
                    "index_name", "index_type", "market", "base_date",
                    "base_value", "constituents_count", "suitable_for_categories",
                    "data_source", "update_frequency", "description", "updated_at"
                ]

                upsert_sql = self.adapter.get_upsert_syntax(
                    "benchmark_indices", columns, update_columns
                )

                # Convert suitable_for_categories list to JSON string
                categories_json = str(benchmark.suitable_for_categories)

                params = (
                    benchmark.index_code,
                    benchmark.index_name,
                    benchmark.index_type,
                    benchmark.market,
                    benchmark.base_date,
                    benchmark.base_value,
                    benchmark.constituents_count,
                    categories_json,
                    benchmark.data_source,
                    benchmark.update_frequency,
                    benchmark.description,
                    benchmark.created_at,
                    benchmark.updated_at,
                )

                cursor.execute(upsert_sql, params)
                conn.commit()

                logger.info(f"Inserted/updated benchmark {benchmark.index_code}")
                return True

        except Exception as e:
            logger.error(f"Failed to insert benchmark {benchmark.index_code}: {e}")
            return False

    def get_benchmark(self, index_code: str) -> BenchmarkIndex | None:
        """
        Fetch benchmark by code.

        Args:
            index_code: Benchmark index code (e.g., '000300.SH')

        Returns:
            BenchmarkIndex instance if found, None otherwise
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT index_code, index_name, index_type, market,
                           base_date, base_value, constituents_count,
                           suitable_for_categories, data_source, update_frequency,
                           description, created_at, updated_at
                    FROM benchmark_indices
                    WHERE index_code = %s
                """

                cursor.execute(sql, [index_code])
                row = cursor.fetchone()

                if not row:
                    logger.warning(f"Benchmark {index_code} not found")
                    return None

                # Parse suitable_for_categories from JSON string
                import ast
                categories = ast.literal_eval(row["suitable_for_categories"])

                benchmark = BenchmarkIndex(
                    index_code=row["index_code"],
                    index_name=row["index_name"],
                    index_type=row["index_type"],
                    market=row["market"],
                    base_date=row["base_date"],
                    base_value=row["base_value"],
                    constituents_count=row["constituents_count"],
                    suitable_for_categories=categories,
                    data_source=row["data_source"],
                    update_frequency=row["update_frequency"],
                    description=row["description"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

                logger.debug(f"Retrieved benchmark {index_code}")
                return benchmark

        except Exception as e:
            logger.error(f"Failed to get benchmark {index_code}: {e}")
            return None

    def list_benchmarks(
        self,
        index_type: str | None = None,
        market: str | None = None,
        suitable_for_category: str | None = None,
    ) -> list[BenchmarkIndex]:
        """
        List benchmarks with optional filters.

        Args:
            index_type: Filter by index type (broad, sector, style, bond, commodity)
            market: Filter by market (SH, SZ, CSI, CIC)
            suitable_for_category: Filter by fund category suitability

        Returns:
            List of BenchmarkIndex instances matching filters
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT index_code, index_name, index_type, market,
                           base_date, base_value, constituents_count,
                           suitable_for_categories, data_source, update_frequency,
                           description, created_at, updated_at
                    FROM benchmark_indices
                    WHERE 1=1
                """
                params = []

                if index_type:
                    sql += " AND index_type = %s"
                    params.append(index_type)

                if market:
                    sql += " AND market = %s"
                    params.append(market)

                if suitable_for_category:
                    sql += " AND suitable_for_categories LIKE %s"
                    params.append(f"%{suitable_for_category}%")

                sql += " ORDER BY index_code ASC"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                import ast
                benchmarks = []
                for row in rows:
                    categories = ast.literal_eval(row["suitable_for_categories"])
                    benchmark = BenchmarkIndex(
                        index_code=row["index_code"],
                        index_name=row["index_name"],
                        index_type=row["index_type"],
                        market=row["market"],
                        base_date=row["base_date"],
                        base_value=row["base_value"],
                        constituents_count=row["constituents_count"],
                        suitable_for_categories=categories,
                        data_source=row["data_source"],
                        update_frequency=row["update_frequency"],
                        description=row["description"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    benchmarks.append(benchmark)

                logger.debug(f"Retrieved {len(benchmarks)} benchmarks")
                return benchmarks

        except Exception as e:
            logger.error(f"Failed to list benchmarks: {e}")
            return []

    def insert_history(self, history: BenchmarkHistory) -> bool:
        """
        Insert or update historical data point.

        Args:
            history: BenchmarkHistory model instance

        Returns:
            True if insertion succeeded, False otherwise
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                # Generate UPSERT SQL
                columns = [
                    "index_code", "trade_date", "close_price", "open_price",
                    "high_price", "low_price", "volume", "turnover", "daily_return"
                ]
                update_columns = [
                    "close_price", "open_price", "high_price", "low_price",
                    "volume", "turnover", "daily_return"
                ]

                upsert_sql = self.adapter.get_upsert_syntax(
                    "benchmark_history", columns, update_columns
                )

                params = (
                    history.index_code,
                    history.trade_date,
                    history.close_price,
                    history.open_price,
                    history.high_price,
                    history.low_price,
                    history.volume,
                    history.turnover,
                    history.daily_return,
                )

                cursor.execute(upsert_sql, params)
                conn.commit()

                logger.debug(f"Inserted history for {history.index_code} on {history.trade_date}")
                return True

        except Exception as e:
            logger.error(f"Failed to insert history for {history.index_code}: {e}")
            return False

    def bulk_insert_history(self, history_data: list[BenchmarkHistory]) -> dict[str, int]:
        """
        Bulk insert historical data (1000 records at a time).

        Args:
            history_data: List of BenchmarkHistory instances

        Returns:
            Dictionary with statistics: total, success, failed
        """
        if not history_data:
            logger.warning("No history data to insert")
            return {"total": 0, "success": 0, "failed": 0}

        stats = {"total": len(history_data), "success": 0, "failed": 0}

        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                # Generate UPSERT SQL
                columns = [
                    "index_code", "trade_date", "close_price", "open_price",
                    "high_price", "low_price", "volume", "turnover", "daily_return"
                ]
                update_columns = [
                    "close_price", "open_price", "high_price", "low_price",
                    "volume", "turnover", "daily_return"
                ]

                upsert_sql = self.adapter.get_upsert_syntax(
                    "benchmark_history", columns, update_columns
                )

                # Batch insert
                for i in range(0, len(history_data), BATCH_SIZE):
                    batch = history_data[i:i + BATCH_SIZE]
                    batch_params = [
                        (
                            h.index_code, h.trade_date, h.close_price,
                            h.open_price, h.high_price, h.low_price,
                            h.volume, h.turnover, h.daily_return,
                        )
                        for h in batch
                    ]

                    cursor.executemany(upsert_sql, batch_params)
                    stats["success"] += len(batch)
                    logger.debug(f"Inserted batch {i // BATCH_SIZE + 1} for benchmark history")

                conn.commit()
                logger.info(f"Bulk inserted {stats['success']} benchmark history records")

        except Exception as e:
            logger.error(f"Failed to bulk insert benchmark history: {e}")
            stats["failed"] = stats["total"]

        return stats

    def get_history(
        self,
        index_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Retrieve historical data as DataFrame.

        Args:
            index_code: Benchmark index code
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
            limit: Optional maximum number of records

        Returns:
            DataFrame with columns:
            - trade_date
            - close_price
            - daily_return
            - (optional: open_price, high_price, low_price, volume, turnover)

            Empty DataFrame if no data found
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                # Build query with optional filters
                sql = """
                    SELECT trade_date, close_price, open_price, high_price,
                           low_price, volume, turnover, daily_return
                    FROM benchmark_history
                    WHERE index_code = %s
                """
                params = [index_code]

                if start_date:
                    sql += " AND trade_date >= %s"
                    params.append(start_date)

                if end_date:
                    sql += " AND trade_date <= %s"
                    params.append(end_date)

                sql += " ORDER BY trade_date ASC"

                if limit:
                    sql += " LIMIT %s"
                    params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                if not rows:
                    logger.warning(f"No history found for benchmark {index_code}")
                    return pd.DataFrame()

                df = pd.DataFrame(rows)

                # Ensure date column is datetime
                df["trade_date"] = pd.to_datetime(df["trade_date"])

                logger.debug(f"Retrieved {len(df)} history records for {index_code}")
                return df

        except Exception as e:
            logger.error(f"Failed to get history for benchmark {index_code}: {e}")
            return pd.DataFrame()

    def get_latest_price(self, index_code: str) -> float | None:
        """
        Get the latest closing price for an index.

        Args:
            index_code: Benchmark index code

        Returns:
            Latest closing price or None if not found
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT close_price
                    FROM benchmark_history
                    WHERE index_code = %s
                    ORDER BY trade_date DESC
                    LIMIT 1
                """

                cursor.execute(sql, [index_code])
                row = cursor.fetchone()

                if not row:
                    logger.warning(f"No price data found for benchmark {index_code}")
                    return None

                price = float(row["close_price"])
                logger.debug(f"Latest price for {index_code}: {price}")
                return price

        except Exception as e:
            logger.error(f"Failed to get latest price for {index_code}: {e}")
            return None

    def get_benchmark_for_fund(
        self,
        fund_category: str,
        fund_sector: str | None = None,
    ) -> BenchmarkIndex | None:
        """
        Get the appropriate benchmark for a fund.

        Selection logic:
        1. Try exact match on fund_category in suitable_for_categories
        2. Try match on fund_sector if provided
        3. Fall back to default broad market index (CSI 300)

        Args:
            fund_category: Fund category (e.g., '宽基', '科技', '债券')
            fund_sector: Optional fund sector for more specific matching

        Returns:
            BenchmarkIndex instance or None if no match found
        """
        try:
            # Try exact match on fund category
            benchmarks = self.list_benchmarks()
            for benchmark in benchmarks:
                if fund_category in benchmark.suitable_for_categories:
                    # If sector provided, check if there's a better match
                    if fund_sector:
                        for candidate in benchmarks:
                            if fund_sector in candidate.suitable_for_categories:
                                logger.debug(
                                    f"Matched benchmark {candidate.index_code} "
                                    f"for fund category {fund_category}, sector {fund_sector}"
                                )
                                return candidate

                    logger.debug(
                        f"Matched benchmark {benchmark.index_code} "
                        f"for fund category {fund_category}"
                    )
                    return benchmark

            # Fall back to CSI 300 (broad market)
            default_benchmark = self.get_benchmark("000300.SH")
            if default_benchmark:
                logger.info(
                    f"Using default benchmark CSI 300 for fund category {fund_category}"
                )
                return default_benchmark

            logger.warning(f"No benchmark found for fund category {fund_category}")
            return None

        except Exception as e:
            logger.error(f"Failed to get benchmark for fund: {e}")
            return None

    def delete_history(
        self,
        index_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """
        Delete historical data for an index.

        Args:
            index_code: Benchmark index code
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)

        Returns:
            Number of records deleted
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                sql = "DELETE FROM benchmark_history WHERE index_code = %s"
                params = [index_code]

                if start_date:
                    sql += " AND trade_date >= %s"
                    params.append(start_date)

                if end_date:
                    sql += " AND trade_date <= %s"
                    params.append(end_date)

                cursor.execute(sql, params)
                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"Deleted {deleted_count} history records for {index_code}")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete history for {index_code}: {e}")
            return 0

    def get_history_date_range(
        self,
        index_code: str,
    ) -> tuple[date | None, date | None]:
        """
        Get the date range of available historical data.

        Args:
            index_code: Benchmark index code

        Returns:
            Tuple of (min_date, max_date) or (None, None) if no data
        """
        try:
            with self.adapter.connection_context() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
                    FROM benchmark_history
                    WHERE index_code = %s
                """

                cursor.execute(sql, [index_code])
                row = cursor.fetchone()

                if not row or row["min_date"] is None:
                    return None, None

                min_date = row["min_date"]
                max_date = row["max_date"]

                logger.debug(f"Date range for {index_code}: {min_date} to {max_date}")
                return min_date, max_date

        except Exception as e:
            logger.error(f"Failed to get date range for {index_code}: {e}")
            return None, None
