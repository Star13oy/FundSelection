"""
Benchmark data management system for Chinese A-share markets.

This package provides comprehensive benchmark index data management for
calculating Information Ratio, tracking error, and up/down capture ratios.

Main Components:
- BenchmarkIndex: Model for benchmark indices
- BenchmarkHistory: Model for historical price data
- BenchmarkRepository: Database operations
- BenchmarkFetcher: Data fetching from akshare
- BenchmarkManager: High-level interface
- seed_benchmark_database(): Initialize standard benchmarks

Usage:
    >>> from app.benchmark import BenchmarkManager, seed_benchmark_database
    >>> from app.db import get_adapter
    >>>
    >>> # Initialize database with standard benchmarks
    >>> adapter = get_adapter()
    >>> seed_benchmark_database(adapter)
    >>>
    >>> # Create manager
    >>> manager = BenchmarkManager(adapter)
    >>>
    >>> # Get benchmark returns
    >>> returns = manager.get_benchmark_return_series("000300.SH", start_date, end_date)
    >>>
    >>> # Calculate Information Ratio
    >>> ir = manager.get_information_ratio(fund_returns, "000300.SH")

Standard Benchmark Codes:
    - 000300.SH: CSI 300 (沪深300) - Broad market
    - 000905.SH: CSI 500 (中证500) - Mid-cap
    - 399406.SZ: CSI 1000 (中证1000) - Small-cap
    - 399006.SZ: CSI Tech (中证科技) - Technology
    - 399412.SZ: CSI New Energy (中证新能源) - New energy
    - CBA00101.CS: China Bond Composite (中债综合) - Bonds
"""

from app.benchmark.models import (
    BenchmarkIndex,
    BenchmarkHistory,
    BenchmarkMapping,
    STANDARD_BENCHMARK_CODES,
)
from app.benchmark.repository import BenchmarkRepository
from app.benchmark.fetcher import BenchmarkFetcher
from app.benchmark.manager import BenchmarkManager
from app.benchmark.seed_data import (
    seed_benchmark_database,
    get_benchmark_mapping,
    get_benchmark_for_category,
    STANDARD_BENCHMARKS,
)

__all__ = [
    # Models
    "BenchmarkIndex",
    "BenchmarkHistory",
    "BenchmarkMapping",
    "STANDARD_BENCHMARK_CODES",

    # Repository
    "BenchmarkRepository",

    # Fetcher
    "BenchmarkFetcher",

    # Manager
    "BenchmarkManager",

    # Seed data
    "seed_benchmark_database",
    "get_benchmark_mapping",
    "get_benchmark_for_category",
    "STANDARD_BENCHMARKS",
]

__version__ = "1.0.0"
__author__ = "Fund Selection System"
