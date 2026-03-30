-- MySQL Database Schema for Fund Selection Application
-- This file contains all table definitions for MySQL backend
-- MySQL-specific syntax used (AUTO_INCREMENT, NOW(), JSON, etc.)

-- Funds table: Core fund information with factor metrics and policy scores
CREATE TABLE IF NOT EXISTS funds (
    code VARCHAR(16) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    category VARCHAR(32) NOT NULL,
    fund_type VARCHAR(32) NOT NULL,
    years DOUBLE NOT NULL,
    scale_billion DOUBLE NOT NULL,
    fee DOUBLE NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    one_year_return DOUBLE NOT NULL,
    max_drawdown DOUBLE NOT NULL,
    tracking_error DOUBLE NULL,
    liquidity_label VARCHAR(32) NOT NULL,
    updated_at VARCHAR(32) NOT NULL,
    factor_returns DOUBLE NOT NULL,
    factor_risk_control DOUBLE NOT NULL,
    factor_risk_adjusted DOUBLE NOT NULL,
    factor_stability DOUBLE NOT NULL,
    factor_cost_efficiency DOUBLE NOT NULL,
    factor_liquidity DOUBLE NOT NULL,
    factor_survival_quality DOUBLE NOT NULL,
    policy_support DOUBLE NOT NULL,
    policy_execution DOUBLE NOT NULL,
    policy_regulation_safety DOUBLE NOT NULL,
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Indexes for funds table
CREATE INDEX idx_funds_channel ON funds(channel);
CREATE INDEX idx_funds_category ON funds(category);
CREATE INDEX idx_funds_risk_level ON funds(risk_level);
CREATE INDEX idx_funds_years ON funds(years);
CREATE INDEX idx_funds_scale ON funds(scale_billion);
CREATE INDEX idx_funds_fee ON funds(fee);
CREATE INDEX idx_funds_one_year_return ON funds(one_year_return);
CREATE INDEX idx_funds_max_drawdown ON funds(max_drawdown);
CREATE INDEX idx_funds_liquidity_label ON funds(liquidity_label);
CREATE INDEX idx_funds_updated_at ON funds(updated_at);

-- Composite indexes for common query patterns
CREATE INDEX idx_funds_channel_category ON funds(channel, category);
CREATE INDEX idx_funds_risk_years ON funds(risk_level, years);
CREATE INDEX idx_funds_category_return ON funds(category, one_year_return);

-- Factor indexes for sorting and filtering
CREATE INDEX idx_funds_factor_returns ON funds(factor_returns);
CREATE INDEX idx_funds_factor_risk_control ON funds(factor_risk_control);
CREATE INDEX idx_funds_factor_risk_adjusted ON funds(factor_risk_adjusted);
CREATE INDEX idx_funds_factor_stability ON funds(factor_stability);
CREATE INDEX idx_funds_factor_cost_efficiency ON funds(factor_cost_efficiency);
CREATE INDEX idx_funds_factor_liquidity ON funds(factor_liquidity);
CREATE INDEX idx_funds_factor_survival ON funds(factor_survival_quality);

-- Policy indexes
CREATE INDEX idx_funds_policy_support ON funds(policy_support);
CREATE INDEX idx_funds_policy_execution ON funds(policy_execution);
CREATE INDEX idx_funds_policy_regulation ON funds(policy_regulation_safety);

-- Market quotes table: Real-time and delayed market data
CREATE TABLE IF NOT EXISTS market_quotes (
    fund_code VARCHAR(16) PRIMARY KEY,
    current_price DOUBLE NULL,
    previous_close DOUBLE NULL,
    intraday_high DOUBLE NULL,
    intraday_low DOUBLE NULL,
    open_price DOUBLE NULL,
    price_change_pct DOUBLE NULL,
    price_change_value DOUBLE NULL,
    nav DOUBLE NULL,
    nav_date VARCHAR(32) NULL,
    nav_estimate DOUBLE NULL,
    nav_estimate_change_pct DOUBLE NULL,
    volume DOUBLE NULL,
    turnover DOUBLE NULL,
    quote_time VARCHAR(32) NULL,
    fetched_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(64) NULL,
    raw_payload JSON NULL,
    CONSTRAINT fk_market_quotes_fund
        FOREIGN KEY (fund_code) REFERENCES funds(code)
        ON DELETE CASCADE,
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Indexes for market_quotes
CREATE INDEX idx_market_quotes_fetched_at ON market_quotes(fetched_at);
CREATE INDEX idx_market_quotes_source ON market_quotes(source);
CREATE INDEX idx_market_quotes_quote_time ON market_quotes(quote_time);

-- Fund NAV history table: Historical net asset value data
CREATE TABLE IF NOT EXISTS fund_nav_history (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    fund_code VARCHAR(16) NOT NULL,
    date DATE NOT NULL,
    unit_nav DOUBLE NOT NULL,
    accumulated_nav DOUBLE NOT NULL,
    daily_return DOUBLE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_nav_history_fund
        FOREIGN KEY (fund_code) REFERENCES funds(code)
        ON DELETE CASCADE,
    UNIQUE KEY uk_nav_fund_date (fund_code, date),
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Indexes for fund_nav_history
CREATE INDEX idx_nav_history_fund_code ON fund_nav_history(fund_code);
CREATE INDEX idx_nav_history_date ON fund_nav_history(date);
CREATE INDEX idx_nav_history_fund_date ON fund_nav_history(fund_code, date);
CREATE INDEX idx_nav_history_daily_return ON fund_nav_history(daily_return);

-- Market quotes history table: Historical market data for analysis
CREATE TABLE IF NOT EXISTS market_quotes_history (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    fund_code VARCHAR(16) NOT NULL,
    quote_time DATETIME NOT NULL,
    price DOUBLE NULL,
    volume DOUBLE NULL,
    source VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_quotes_history_fund
        FOREIGN KEY (fund_code) REFERENCES funds(code)
        ON DELETE CASCADE,
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Indexes for market_quotes_history
CREATE INDEX idx_quotes_history_fund_code ON market_quotes_history(fund_code);
CREATE INDEX idx_quotes_history_quote_time ON market_quotes_history(quote_time);
CREATE INDEX idx_quotes_history_fund_time ON market_quotes_history(fund_code, quote_time);
CREATE INDEX idx_quotes_history_source ON market_quotes_history(source);

-- Policy events table: Government policy and regulatory events
CREATE TABLE IF NOT EXISTS policy_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    policy_id VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(256) NOT NULL,
    published_at DATETIME NOT NULL,
    effective_from DATETIME NULL,
    expires_at DATETIME NULL,
    related_sectors JSON,  -- JSON array of sector names
    intensity_level INT NOT NULL CHECK (intensity_level >= 1 AND intensity_level <= 5),
    execution_status ENUM('announced', 'detailed', 'implementing', 'completed', 'cancelled') NOT NULL,
    impact_direction ENUM('positive', 'negative', 'neutral') NOT NULL,
    policy_type ENUM('fiscal', 'monetary', 'industrial', 'regulatory', 'reform') NOT NULL,
    support_amount_billion DOUBLE NULL,
    tax_incentive_rate DOUBLE NULL,
    source_url VARCHAR(512) NULL,
    description TEXT,
    key_points JSON,  -- JSON array of key policy points
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Indexes for policy_events
CREATE INDEX idx_policy_events_published_at ON policy_events(published_at);
CREATE INDEX idx_policy_events_intensity ON policy_events(intensity_level);
CREATE INDEX idx_policy_events_status ON policy_events(execution_status);
CREATE INDEX idx_policy_events_direction ON policy_events(impact_direction);
CREATE INDEX idx_policy_events_sectors ON policy_events(related_sectors(255));

-- Data change log table: Audit trail for all data modifications
CREATE TABLE IF NOT EXISTS data_change_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    action ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_fields JSON,  -- JSON object with field names and old/new values
    changed_by VARCHAR(64),  -- User or system identifier
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Indexes for data_change_log
CREATE INDEX idx_change_log_table ON data_change_log(table_name);
CREATE INDEX idx_change_log_record ON data_change_log(table_name, record_id);
CREATE INDEX idx_change_log_action ON data_change_log(action);
CREATE INDEX idx_change_log_changed_at ON data_change_log(changed_at);

-- Watchlist table: User watchlist for funds
CREATE TABLE IF NOT EXISTS watchlist (
    code VARCHAR(16) PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_watchlist_fund
        FOREIGN KEY (code) REFERENCES funds(code)
        ON DELETE CASCADE,
    ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
);

-- Index for watchlist
CREATE INDEX idx_watchlist_created_at ON watchlist(created_at);
