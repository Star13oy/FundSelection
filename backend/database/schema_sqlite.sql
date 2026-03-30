-- SQLite Database Schema for Fund Selection Application
-- This file contains all table definitions for SQLite backend
-- SQLite-specific syntax used (AUTOINCREMENT, datetime('now'), etc.)

-- Funds table: Core fund information with factor metrics and policy scores
CREATE TABLE IF NOT EXISTS funds (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    category TEXT NOT NULL,
    fund_type TEXT NOT NULL,
    years REAL NOT NULL,
    scale_billion REAL NOT NULL,
    fee REAL NOT NULL,
    risk_level TEXT NOT NULL,
    one_year_return REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    tracking_error REAL,
    liquidity_label TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    factor_returns REAL NOT NULL,
    factor_risk_control REAL NOT NULL,
    factor_risk_adjusted REAL NOT NULL,
    factor_stability REAL NOT NULL,
    factor_cost_efficiency REAL NOT NULL,
    factor_liquidity REAL NOT NULL,
    factor_survival_quality REAL NOT NULL,
    policy_support REAL NOT NULL,
    policy_execution REAL NOT NULL,
    policy_regulation_safety REAL NOT NULL
);

-- Indexes for funds table
CREATE INDEX IF NOT EXISTS idx_funds_channel ON funds(channel);
CREATE INDEX IF NOT EXISTS idx_funds_category ON funds(category);
CREATE INDEX IF NOT EXISTS idx_funds_risk_level ON funds(risk_level);
CREATE INDEX IF NOT EXISTS idx_funds_years ON funds(years);
CREATE INDEX IF NOT EXISTS idx_funds_scale ON funds(scale_billion);
CREATE INDEX IF NOT EXISTS idx_funds_fee ON funds(fee);
CREATE INDEX IF NOT EXISTS idx_funds_one_year_return ON funds(one_year_return);
CREATE INDEX IF NOT EXISTS idx_funds_max_drawdown ON funds(max_drawdown);
CREATE INDEX IF NOT EXISTS idx_funds_liquidity_label ON funds(liquidity_label);
CREATE INDEX IF NOT EXISTS idx_funds_updated_at ON funds(updated_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_funds_channel_category ON funds(channel, category);
CREATE INDEX IF NOT EXISTS idx_funds_risk_years ON funds(risk_level, years);
CREATE INDEX IF NOT EXISTS idx_funds_category_return ON funds(category, one_year_return);

-- Factor indexes for sorting and filtering
CREATE INDEX IF NOT EXISTS idx_funds_factor_returns ON funds(factor_returns);
CREATE INDEX IF NOT EXISTS idx_funds_factor_risk_control ON funds(factor_risk_control);
CREATE INDEX IF NOT EXISTS idx_funds_factor_risk_adjusted ON funds(factor_risk_adjusted);
CREATE INDEX IF NOT EXISTS idx_funds_factor_stability ON funds(factor_stability);
CREATE INDEX IF NOT EXISTS idx_funds_factor_cost_efficiency ON funds(factor_cost_efficiency);
CREATE INDEX IF NOT EXISTS idx_funds_factor_liquidity ON funds(factor_liquidity);
CREATE INDEX IF NOT EXISTS idx_funds_factor_survival ON funds(factor_survival_quality);

-- Policy indexes
CREATE INDEX IF NOT EXISTS idx_funds_policy_support ON funds(policy_support);
CREATE INDEX IF NOT EXISTS idx_funds_policy_execution ON funds(policy_execution);
CREATE INDEX IF NOT EXISTS idx_funds_policy_regulation ON funds(policy_regulation_safety);

-- Market quotes table: Real-time and delayed market data
CREATE TABLE IF NOT EXISTS market_quotes (
    fund_code TEXT PRIMARY KEY,
    current_price REAL,
    previous_close REAL,
    intraday_high REAL,
    intraday_low REAL,
    open_price REAL,
    price_change_pct REAL,
    price_change_value REAL,
    nav REAL,
    nav_date TEXT,
    nav_estimate REAL,
    nav_estimate_change_pct REAL,
    volume REAL,
    turnover REAL,
    quote_time TEXT,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    source TEXT,
    raw_payload TEXT,
    FOREIGN KEY (fund_code) REFERENCES funds(code) ON DELETE CASCADE
);

-- Indexes for market_quotes
CREATE INDEX IF NOT EXISTS idx_market_quotes_fetched_at ON market_quotes(fetched_at);
CREATE INDEX IF NOT EXISTS idx_market_quotes_source ON market_quotes(source);
CREATE INDEX IF NOT EXISTS idx_market_quotes_quote_time ON market_quotes(quote_time);

-- Fund NAV history table: Historical net asset value data
CREATE TABLE IF NOT EXISTS fund_nav_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    date TEXT NOT NULL,
    unit_nav REAL NOT NULL,
    accumulated_nav REAL NOT NULL,
    daily_return REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_code) REFERENCES funds(code) ON DELETE CASCADE,
    UNIQUE(fund_code, date)
);

-- Indexes for fund_nav_history
CREATE INDEX IF NOT EXISTS idx_nav_history_fund_code ON fund_nav_history(fund_code);
CREATE INDEX IF NOT EXISTS idx_nav_history_date ON fund_nav_history(date);
CREATE INDEX IF NOT EXISTS idx_nav_history_fund_date ON fund_nav_history(fund_code, date);
CREATE INDEX IF NOT EXISTS idx_nav_history_daily_return ON fund_nav_history(daily_return);

-- Market quotes history table: Historical market data for analysis
CREATE TABLE IF NOT EXISTS market_quotes_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    quote_time TEXT NOT NULL,
    price REAL,
    volume REAL,
    source TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fund_code) REFERENCES funds(code) ON DELETE CASCADE
);

-- Indexes for market_quotes_history
CREATE INDEX IF NOT EXISTS idx_quotes_history_fund_code ON market_quotes_history(fund_code);
CREATE INDEX IF NOT EXISTS idx_quotes_history_quote_time ON market_quotes_history(quote_time);
CREATE INDEX IF NOT EXISTS idx_quotes_history_fund_time ON market_quotes_history(fund_code, quote_time);
CREATE INDEX IF NOT EXISTS idx_quotes_history_source ON market_quotes_history(source);

-- Policy events table: Government policy and regulatory events
CREATE TABLE IF NOT EXISTS policy_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    published_at TEXT NOT NULL,
    effective_from TEXT,
    expires_at TEXT,
    related_sectors TEXT,  -- JSON array of sector names
    intensity_level INTEGER NOT NULL CHECK (intensity_level >= 1 AND intensity_level <= 5),
    execution_status TEXT NOT NULL CHECK (execution_status IN ('announced', 'detailed', 'implementing', 'completed', 'cancelled')),
    impact_direction TEXT NOT NULL CHECK (impact_direction IN ('positive', 'negative', 'neutral')),
    policy_type TEXT NOT NULL CHECK (policy_type IN ('fiscal', 'monetary', 'industrial', 'regulatory', 'reform')),
    support_amount_billion REAL,
    tax_incentive_rate REAL,
    source_url TEXT,
    description TEXT,
    key_points TEXT,  -- JSON array of key policy points
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for policy_events
CREATE INDEX IF NOT EXISTS idx_policy_events_published_at ON policy_events(published_at);
CREATE INDEX IF NOT EXISTS idx_policy_events_intensity ON policy_events(intensity_level);
CREATE INDEX IF NOT EXISTS idx_policy_events_status ON policy_events(execution_status);
CREATE INDEX IF NOT EXISTS idx_policy_events_direction ON policy_events(impact_direction);
CREATE INDEX IF NOT EXISTS idx_policy_events_sectors ON policy_events(related_sectors);

-- Data change log table: Audit trail for all data modifications
CREATE TABLE IF NOT EXISTS data_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    changed_fields TEXT,   -- JSON object with field names and old/new values
    changed_by TEXT,       -- User or system identifier
    CONSTRAINT valid_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'))
);

-- Indexes for data_change_log
CREATE INDEX IF NOT EXISTS idx_change_log_table ON data_change_log(table_name);
CREATE INDEX IF NOT EXISTS idx_change_log_record ON data_change_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_change_log_action ON data_change_log(action);
CREATE INDEX IF NOT EXISTS idx_change_log_changed_at ON data_change_log(changed_at);

-- Watchlist table: User watchlist for funds
CREATE TABLE IF NOT EXISTS watchlist (
    code TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (code) REFERENCES funds(code) ON DELETE CASCADE
);

-- Index for watchlist
CREATE INDEX IF NOT EXISTS idx_watchlist_created_at ON watchlist(created_at);
