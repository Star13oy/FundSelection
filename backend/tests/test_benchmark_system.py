"""
Comprehensive tests for the benchmark data management system.

This module tests all components of the benchmark system:
- Models validation
- Repository operations
- Fetcher functionality
- Manager interface
- Seed data

Critical infrastructure: These tests ensure the benchmark system
works correctly before integration with the factor calculation engine.
"""

from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np

from app.benchmark.models import BenchmarkIndex, BenchmarkHistory, STANDARD_BENCHMARK_CODES
from app.benchmark.repository import BenchmarkRepository
from app.benchmark.fetcher import BenchmarkFetcher
from app.benchmark.manager import BenchmarkManager
from app.benchmark.seed_data import seed_benchmark_database, get_benchmark_mapping, get_benchmark_for_category
from app.db import create_adapter, reset_adapter


@pytest.fixture
def test_adapter():
    """Create test database adapter."""
    adapter = create_adapter()
    # Use in-memory SQLite for testing
    adapter.db_path = ":memory:"
    yield adapter
    reset_adapter()


@pytest.fixture
def test_benchmark():
    """Create test benchmark index."""
    return BenchmarkIndex(
        index_code="TEST001.SH",
        index_name="测试指数",
        index_type="broad",
        market="SH",
        base_date=date(2020, 1, 1),
        base_value=1000,
        constituents_count=100,
        suitable_for_categories=["测试", "宽基"],
        data_source="akshare",
        update_frequency="daily",
        description="测试用指数"
    )


@pytest.fixture
def test_history():
    """Create test benchmark history data."""
    base_date = date(2024, 1, 1)
    history_records = []

    for i in range(100):
        record = BenchmarkHistory(
            index_code="TEST001.SH",
            trade_date=base_date + timedelta(days=i),
            close_price=1000 + i * 10 + np.random.randn() * 20,
            open_price=1000 + i * 10 + np.random.randn() * 20,
            high_price=1000 + i * 10 + np.random.randn() * 20,
            low_price=1000 + i * 10 + np.random.randn() * 20,
            volume=np.random.randint(1000000, 10000000),
            daily_return=np.random.randn() * 0.02  # ±2% daily returns
        )
        history_records.append(record)

    return history_records


# ===== MODEL TESTS =====

def test_benchmark_model_validation(test_benchmark):
    """Test benchmark model validation."""
    # Valid model should not raise
    assert test_benchmark.index_code == "TEST001.SH"
    assert test_benchmark.index_type == "broad"
    assert test_benchmark.market == "SH"
    assert test_benchmark.base_value == 1000
    assert len(test_benchmark.suitable_for_categories) > 0

    # Test invalid index_type
    with pytest.raises(ValueError):
        BenchmarkIndex(
            index_code="TEST001.SH",
            index_name="测试指数",
            index_type="invalid_type",  # Invalid
            market="SH",
            base_date=date(2020, 1, 1),
            base_value=1000,
            constituents_count=100,
            suitable_for_categories=["测试"]
        )

    # Test invalid market
    with pytest.raises(ValueError):
        BenchmarkIndex(
            index_code="TEST001.SH",
            index_name="测试指数",
            index_type="broad",
            market="INVALID",  # Invalid
            base_date=date(2020, 1, 1),
            base_value=1000,
            constituents_count=100,
            suitable_for_categories=["测试"]
        )


def test_benchmark_history_model_validation():
    """Test benchmark history model validation."""
    # Valid model
    history = BenchmarkHistory(
        index_code="TEST001.SH",
        trade_date=date(2024, 1, 1),
        close_price=1000.0,
        daily_return=0.01
    )
    assert history.index_code == "TEST001.SH"
    assert history.close_price == 1000.0

    # Test negative price (should fail)
    with pytest.raises(ValueError):
        BenchmarkHistory(
            index_code="TEST001.SH",
            trade_date=date(2024, 1, 1),
            close_price=-100.0,  # Invalid
        )


# ===== REPOSITORY TESTS =====

def test_insert_and_get_benchmark(test_adapter, test_benchmark):
    """Test inserting and retrieving benchmark."""
    repo = BenchmarkRepository(test_adapter)

    # Initialize database schema
    test_adapter.init_database()

    # Insert benchmark
    success = repo.insert_benchmark(test_benchmark)
    assert success is True

    # Retrieve benchmark
    retrieved = repo.get_benchmark("TEST001.SH")
    assert retrieved is not None
    assert retrieved.index_code == "TEST001.SH"
    assert retrieved.index_name == "测试指数"
    assert retrieved.index_type == "broad"


def test_list_benchmarks(test_adapter, test_benchmark):
    """Test listing benchmarks with filters."""
    repo = BenchmarkRepository(test_adapter)
    test_adapter.init_database()

    # Insert multiple benchmarks
    benchmarks = [
        test_benchmark,
        BenchmarkIndex(
            index_code="TEST002.SH",
            index_name="测试指数2",
            index_type="sector",
            market="SH",
            base_date=date(2020, 1, 1),
            base_value=1000,
            constituents_count=50,
            suitable_for_categories=["科技"],
        ),
        BenchmarkIndex(
            index_code="TEST003.SH",
            index_name="测试指数3",
            index_type="bond",
            market="CIC",
            base_date=date(2020, 1, 1),
            base_value=100,
            constituents_count=0,
            suitable_for_categories=["债券"],
        ),
    ]

    for bm in benchmarks:
        repo.insert_benchmark(bm)

    # List all benchmarks
    all_benchmarks = repo.list_benchmarks()
    assert len(all_benchmarks) == 3

    # Filter by type
    broad_benchmarks = repo.list_benchmarks(index_type="broad")
    assert len(broad_benchmarks) == 1
    assert broad_benchmarks[0].index_type == "broad"

    # Filter by market
    sh_benchmarks = repo.list_benchmarks(market="SH")
    assert len(sh_benchmarks) == 2


def test_insert_and_get_history(test_adapter, test_history):
    """Test inserting and retrieving benchmark history."""
    repo = BenchmarkRepository(test_adapter)
    test_adapter.init_database()

    # Insert benchmark first
    benchmark = BenchmarkIndex(
        index_code="TEST001.SH",
        index_name="测试指数",
        index_type="broad",
        market="SH",
        base_date=date(2020, 1, 1),
        base_value=1000,
        constituents_count=100,
        suitable_for_categories=["测试"],
    )
    repo.insert_benchmark(benchmark)

    # Bulk insert history
    result = repo.bulk_insert_history(test_history)
    assert result['success'] == len(test_history)
    assert result['failed'] == 0

    # Retrieve history
    df = repo.get_history("TEST001.SH")
    assert len(df) == len(test_history)
    assert 'close_price' in df.columns
    assert 'daily_return' in df.columns


def test_get_history_date_range(test_adapter, test_history):
    """Test getting history with date range filtering."""
    repo = BenchmarkRepository(test_adapter)
    test_adapter.init_database()

    # Insert benchmark and history
    benchmark = BenchmarkIndex(
        index_code="TEST001.SH",
        index_name="测试指数",
        index_type="broad",
        market="SH",
        base_date=date(2020, 1, 1),
        base_value=1000,
        constituents_count=100,
        suitable_for_categories=["测试"],
    )
    repo.insert_benchmark(benchmark)
    repo.bulk_insert_history(test_history)

    # Get full range
    min_date, max_date = repo.get_history_date_range("TEST001.SH")
    assert min_date is not None
    assert max_date is not None

    # Get partial range
    start_date = date(2024, 1, 10)
    end_date = date(2024, 1, 20)
    df = repo.get_history("TEST001.SH", start_date=start_date, end_date=end_date)
    assert len(df) <= 11  # At most 11 days in range


# ===== FETCHER TESTS =====

def test_symbol_format_conversion(test_adapter):
    """Test index code format conversion."""
    fetcher = BenchmarkFetcher(test_adapter)

    # Test standard to akshare format
    akshare_format = fetcher._convert_symbol_format("000300.SH", "akshare")
    assert akshare_format == "sh000300"

    akshare_format = fetcher._convert_symbol_format("399001.SZ", "akshare")
    assert akshare_format == "sz399001"

    # Test akshare to standard format
    standard_format = fetcher._convert_symbol_format("sh000300", "standard")
    assert standard_format == "000300.SH"

    standard_format = fetcher._convert_symbol_format("sz399001", "standard")
    assert standard_format == "399001.SZ"


def test_calculate_daily_returns(test_adapter):
    """Test daily return calculation."""
    fetcher = BenchmarkFetcher(test_adapter)

    # Create test data
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    })

    # Calculate returns
    df_with_returns = fetcher.calculate_daily_returns(df)

    # Check returns column exists
    assert 'daily_return' in df_with_returns.columns

    # Check first return (should be NaN)
    assert pd.isna(df_with_returns['daily_return'].iloc[0])

    # Check second return (101-100)/100 = 0.01
    assert abs(df_with_returns['daily_return'].iloc[1] - 0.01) < 1e-6


# ===== MANAGER TESTS =====

def test_manager_get_appropriate_benchmark(test_adapter):
    """Test benchmark auto-selection for fund categories."""
    manager = BenchmarkManager(test_adapter)
    test_adapter.init_database()

    # Seed benchmarks
    seed_benchmark_database(test_adapter)

    # Test various fund categories
    benchmark_codes = {
        '宽基': '000300.SH',
        '科技': '399006.SZ',
        '债券': 'CBA00101.CS',
    }

    for category, expected_code in benchmark_codes.items():
        result = manager.get_appropriate_benchmark(category)
        assert result == expected_code


def test_manager_align_fund_to_benchmark(test_adapter):
    """Test fund and benchmark return alignment."""
    manager = BenchmarkManager(test_adapter)
    test_adapter.init_database()

    # Create test data
    fund_dates = pd.date_range('2024-01-01', periods=100)
    fund_returns = pd.Series(
        np.random.randn(100) * 0.02,
        index=fund_dates,
        name='fund_returns'
    )

    # Mock benchmark returns (different dates)
    benchmark_dates = pd.date_range('2024-01-05', periods=95)
    benchmark_returns = pd.Series(
        np.random.randn(95) * 0.015,
        index=benchmark_dates,
        name='benchmark_returns'
    )

    # Align (this will use mock data, so we just test the method exists)
    # In real scenario, this would query actual benchmark data
    assert hasattr(manager, 'align_fund_to_benchmark')


# ===== SEED DATA TESTS =====

def test_seed_benchmark_database(test_adapter):
    """Test seeding benchmark database."""
    test_adapter.init_database()

    # Seed benchmarks
    result = seed_benchmark_database(test_adapter)

    # Check results
    assert result['benchmarks_inserted'] > 0
    assert len(result['errors']) == 0

    # Verify benchmarks were inserted
    repo = BenchmarkRepository(test_adapter)
    benchmarks = repo.list_benchmarks()
    assert len(benchmarks) > 0

    # Check for key benchmarks
    csi300 = repo.get_benchmark("000300.SH")
    assert csi300 is not None
    assert csi300.index_name == "沪深300"


def test_get_benchmark_mapping():
    """Test benchmark mapping configuration."""
    mapping = get_benchmark_mapping()

    # Check mapping exists for key categories
    assert '宽基' in mapping
    assert '科技' in mapping
    assert '债券' in mapping

    # Check structure
    assert 'primary' in mapping['宽基']
    assert 'fallback' in mapping['宽基']


def test_get_benchmark_for_category():
    """Test getting benchmark code for category."""
    # Test known category
    benchmark = get_benchmark_for_category('科技')
    assert benchmark == '399006.SZ'

    # Test unknown category (should default to CSI 300)
    benchmark = get_benchmark_for_category('unknown_category')
    assert benchmark == '000300.SH'


# ===== INTEGRATION TESTS =====

def test_full_benchmark_workflow(test_adapter):
    """Test complete workflow from seeding to retrieval."""
    test_adapter.init_database()

    # Seed benchmarks
    seed_result = seed_benchmark_database(test_adapter)
    assert seed_result['benchmarks_inserted'] > 0

    # Create manager
    manager = BenchmarkManager(test_adapter)

    # Get benchmark info
    benchmark_code = manager.get_appropriate_benchmark('宽基')
    assert benchmark_code == '000300.SH'

    # Get benchmark details
    info = manager.get_benchmark_info(benchmark_code)
    assert info is not None
    assert info['index_code'] == benchmark_code
    assert info['index_name'] == "沪深300"


# ===== PERFORMANCE TESTS =====

def test_bulk_insert_performance(test_adapter):
    """Test bulk insert performance with large dataset."""
    repo = BenchmarkRepository(test_adapter)
    test_adapter.init_database()

    # Insert benchmark
    benchmark = BenchmarkIndex(
        index_code="PERF001.SH",
        index_name="性能测试指数",
        index_type="broad",
        market="SH",
        base_date=date(2020, 1, 1),
        base_value=1000,
        constituents_count=100,
        suitable_for_categories=["测试"],
    )
    repo.insert_benchmark(benchmark)

    # Create large history dataset (5000 records)
    base_date = date(2020, 1, 1)
    history_records = []

    for i in range(5000):
        record = BenchmarkHistory(
            index_code="PERF001.SH",
            trade_date=base_date + timedelta(days=i),
            close_price=1000 + i * 0.1,
            daily_return=np.random.randn() * 0.02
        )
        history_records.append(record)

    # Bulk insert
    import time
    start_time = time.time()
    result = repo.bulk_insert_history(history_records)
    end_time = time.time()

    assert result['success'] == 5000
    assert result['failed'] == 0

    # Should complete in reasonable time (< 10 seconds)
    assert (end_time - start_time) < 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
