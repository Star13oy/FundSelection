-- Migration 002: Add Fund NAV History Table
-- This migration adds historical NAV tracking for funds
-- Applied: 2026-03-30

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
    UNIQUE KEY uk_nav_fund_date (fund_code, date)
);

CREATE INDEX idx_nav_history_fund_code ON fund_nav_history(fund_code);
CREATE INDEX idx_nav_history_date ON fund_nav_history(date);
CREATE INDEX idx_nav_history_fund_date ON fund_nav_history(fund_code, date);
CREATE INDEX idx_nav_history_daily_return ON fund_nav_history(daily_return);
