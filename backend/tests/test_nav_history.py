"""
Unit tests for NAV history management system.

Tests cover:
- Fetching NAV history for ETFs and open-end funds
- Data validation
- Storage with duplicate handling
- Retrieval with date filtering
- Backfill operations
- Incremental updates
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import pytest

from app.data.nav_history import (
    MAX_DAILY_RETURN,
    MAX_WORKERS,
    MIN_DAILY_RETURN,
    MIN_RECORDS,
    NAVHistoryManager,
    adjust_to_trading_days,
    validate_nav_data,
)


@pytest.fixture
def nav_manager() -> NAVHistoryManager:
    """Create NAVHistoryManager instance for testing."""
    return NAVHistoryManager()


@pytest.fixture
def sample_nav_data() -> pd.DataFrame:
    """Create sample NAV data for testing."""
    dates = [date(2024, 1, i) for i in range(1, 6)]  # Jan 1-5, 2024
    return pd.DataFrame(
        {
            "date": dates,
            "unit_nav": [1.0, 1.01, 1.02, 1.015, 1.025],
            "accumulated_nav": [1.0, 1.01, 1.02, 1.015, 1.025],
            "daily_return": [0.0, 0.01, 0.0099, -0.0049, 0.0098],
        }
    )


class TestValidateNavData:
    """Tests for validate_nav_data function."""

    def test_valid_nav_data(self, sample_nav_data):
        """Test validation of valid NAV data."""
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert is_valid
        assert len(errors) == 0

    def test_empty_dataframe(self):
        """Test validation fails for empty DataFrame."""
        df = pd.DataFrame()
        is_valid, errors = validate_nav_data(df)
        assert not is_valid
        assert "DataFrame is empty" in errors

    def test_missing_required_columns(self):
        """Test validation fails with missing columns."""
        df = pd.DataFrame({"date": [date(2024, 1, 1)]})
        is_valid, errors = validate_nav_data(df)
        assert not is_valid
        assert any("Missing required columns" in err for err in errors)

    def test_negative_nav_values(self, sample_nav_data):
        """Test validation fails for negative NAV values."""
        sample_nav_data.loc[0, "unit_nav"] = -1.0
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert not is_valid
        assert any("unit_nav values must be > 0" in err for err in errors)

    def test_zero_nav_values(self, sample_nav_data):
        """Test validation fails for zero NAV values."""
        sample_nav_data.loc[0, "accumulated_nav"] = 0.0
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert not is_valid
        assert any("accumulated_nav values must be > 0" in err for err in errors)

    def test_daily_return_out_of_range(self, sample_nav_data):
        """Test validation fails for daily_return outside [-20%, +20%]."""
        sample_nav_data.loc[0, "daily_return"] = 0.25  # 25% exceeds limit
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert not is_valid
        assert any("daily_return out of range" in err for err in errors)

    def test_negative_daily_return_out_of_range(self, sample_nav_data):
        """Test validation fails for daily_return below -20%."""
        sample_nav_data.loc[0, "daily_return"] = -0.25  # -25% exceeds limit
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert not is_valid
        assert any("daily_return out of range" in err for err in errors)

    def test_duplicate_dates(self, sample_nav_data):
        """Test validation fails for duplicate dates."""
        sample_nav_data.loc[1, "date"] = sample_nav_data.loc[0, "date"]
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert not is_valid
        assert any("Duplicate dates" in err for err in errors)

    def test_non_chronological_order(self, sample_nav_data):
        """Test validation fails for non-chronological dates."""
        # Swap two dates
        temp = sample_nav_data.loc[0, "date"]
        sample_nav_data.loc[0, "date"] = sample_nav_data.loc[1, "date"]
        sample_nav_data.loc[1, "date"] = temp
        is_valid, errors = validate_nav_data(sample_nav_data)
        assert not is_valid
        assert any("chronological order" in err for err in errors)

    def test_insufficient_records(self, caplog):
        """Test validation warning for insufficient records."""
        # Only 10 records instead of 252
        dates = [date(2024, 1, i) for i in range(1, 11)]
        df = pd.DataFrame(
            {
                "date": dates,
                "unit_nav": [1.0 + i * 0.01 for i in range(10)],
                "accumulated_nav": [1.0 + i * 0.01 for i in range(10)],
            }
        )
        # Should still be valid, but log a warning
        is_valid, errors = validate_nav_data(df)
        assert is_valid  # Data is valid, just insufficient records
        assert len(errors) == 0  # No errors returned

        # Check that warning was logged
        assert any("Insufficient records" in record.message for record in caplog.records)


class TestAdjustToTradingDays:
    """Tests for adjust_to_trading_days function."""

    def test_filter_weekends(self):
        """Test weekend filtering."""
        # Create date range including weekends
        dates = pd.Series(
            [
                date(2024, 1, 1),  # Monday
                date(2024, 1, 6),  # Saturday
                date(2024, 1, 7),  # Sunday
                date(2024, 1, 8),  # Monday
            ]
        )
        trading_days = adjust_to_trading_days(dates)
        assert len(trading_days) == 2  # Only 2 Mondays
        assert all(d.weekday() < 5 for d in trading_days)

    def test_empty_series(self):
        """Test handling of empty series."""
        dates = pd.Series([], dtype=object)
        trading_days = adjust_to_trading_days(dates)
        assert len(trading_days) == 0

    def test_all_weekdays(self):
        """Test no filtering needed for all weekdays."""
        dates = pd.Series([date(2024, 1, i) for i in range(1, 6)])  # Mon-Fri
        trading_days = adjust_to_trading_days(dates)
        assert len(trading_days) == 5


class TestNAVHistoryManager:
    """Tests for NAVHistoryManager class."""

    def test_initialization(self, nav_manager):
        """Test manager initializes correctly."""
        assert nav_manager.adapter is not None
        assert nav_manager._cache == {}

    def test_fetch_invalid_fund_type(self, nav_manager):
        """Test fetch fails with invalid fund type."""
        with pytest.raises(ValueError, match="Invalid fund_type"):
            nav_manager.fetch_historical_nav("510300", "invalid_type")

    def test_store_empty_nav_data(self, nav_manager):
        """Test storing empty DataFrame returns False."""
        empty_df = pd.DataFrame()
        result = nav_manager.store_nav_history("510300", empty_df)
        assert result is False

    def test_store_missing_required_columns(self, nav_manager):
        """Test storing with missing columns returns False."""
        incomplete_df = pd.DataFrame({"date": [date(2024, 1, 1)]})
        result = nav_manager.store_nav_history("510300", incomplete_df)
        assert result is False

    def test_get_nav_history_empty_database(self, nav_manager):
        """Test retrieving from empty database returns empty DataFrame."""
        df = nav_manager.get_nav_history("NONEXISTENT")
        assert df.empty

    def test_get_nav_history_with_date_range(self, nav_manager, sample_nav_data):
        """Test retrieving with date range filtering."""
        # First store some data
        # Note: This test assumes database is empty or the fund doesn't exist
        # In real test, you'd mock the database adapter
        start_date = date(2024, 1, 2)
        end_date = date(2024, 1, 4)
        df = nav_manager.get_nav_history("510300", start_date, end_date)
        # Should return empty or filtered data depending on database state
        assert isinstance(df, pd.DataFrame)

    def test_backfill_all_funds_returns_stats(self, nav_manager):
        """Test backfill returns statistics dictionary."""
        # This test may take time if akshare is available
        # In real test, you'd mock load_fund_universe and fetch methods
        stats = nav_manager.backfill_all_funds(max_age_days=7)
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "success" in stats
        assert "failed" in stats
        assert "skipped" in stats

    def test_incremental_update_returns_stats(self, nav_manager):
        """Test incremental update returns statistics dictionary."""
        stats = nav_manager.incremental_update()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "success" in stats
        assert "failed" in stats
        assert "added" in stats


class TestIntegration:
    """Integration tests (require database and akshare)."""

    @pytest.mark.skipif(
        True,  # Skip by default as it requires akshare and network
        reason="Requires akshare installation and network access",
    )
    def test_fetch_etf_nav_real(self, nav_manager):
        """Test fetching real ETF NAV data from akshare."""
        df = nav_manager.fetch_historical_nav("510300", "equity")
        assert not df.empty
        assert "date" in df.columns
        assert "unit_nav" in df.columns

    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires akshare installation and network access",
    )
    def test_fetch_open_fund_nav_real(self, nav_manager):
        """Test fetching real open-end fund NAV data from akshare."""
        df = nav_manager.fetch_historical_nav("000001", "bond")
        assert not df.empty
        assert "date" in df.columns
        assert "unit_nav" in df.columns
        assert "accumulated_nav" in df.columns

    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires database connection",
    )
    def test_store_and_retrieve_nav_data(self, nav_manager, sample_nav_data):
        """Test storing and retrieving NAV data."""
        fund_code = "TEST001"
        # Store
        store_result = nav_manager.store_nav_history(fund_code, sample_nav_data)
        assert store_result is True

        # Retrieve
        retrieved_df = nav_manager.get_nav_history(fund_code)
        assert not retrieved_df.empty
        assert len(retrieved_df) == len(sample_nav_data)


class TestConstants:
    """Tests for module constants."""

    def test_max_daily_return(self):
        """Test MAX_DAILY_RETURN is 20%."""
        assert MAX_DAILY_RETURN == 0.20

    def test_min_daily_return(self):
        """Test MIN_DAILY_RETURN is -20%."""
        assert MIN_DAILY_RETURN == -0.20

    def test_min_records(self):
        """Test MIN_RECORDS is 252 (1 year)."""
        assert MIN_RECORDS == 252

    def test_max_workers(self):
        """Test MAX_WORKERS is 5."""
        assert MAX_WORKERS == 5


@pytest.mark.parametrize(
    "fund_code,fund_type,should_raise",
    [
        ("510300", "equity", False),
        ("000001", "bond", False),
        ("510300", "invalid", True),
    ],
)
def test_fetch_historical_nav_params(fund_code, fund_type, should_raise, nav_manager):
    """Test fetch_historical_nav with various parameters."""
    if should_raise:
        with pytest.raises(ValueError):
            nav_manager.fetch_historical_nav(fund_code, fund_type)
    else:
        # Should not raise, but may return empty DataFrame if akshare not available
        df = nav_manager.fetch_historical_nav(fund_code, fund_type)
        assert isinstance(df, pd.DataFrame)
