-- Migration 003: Add Market Quotes History Table
-- This migration adds historical market data tracking
-- Applied: 2026-03-30

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
        ON DELETE CASCADE
);

CREATE INDEX idx_quotes_history_fund_code ON market_quotes_history(fund_code);
CREATE INDEX idx_quotes_history_quote_time ON market_quotes_history(quote_time);
CREATE INDEX idx_quotes_history_fund_time ON market_quotes_history(fund_code, quote_time);
CREATE INDEX idx_quotes_history_source ON market_quotes_history(source);
