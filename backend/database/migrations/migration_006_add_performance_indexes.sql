-- Migration 006: Add Performance Indexes
-- This migration adds additional indexes for query performance
-- Applied: 2026-03-30

-- Funds table indexes
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

-- Composite indexes
CREATE INDEX idx_funds_channel_category ON funds(channel, category);
CREATE INDEX idx_funds_risk_years ON funds(risk_level, years);
CREATE INDEX idx_funds_category_return ON funds(category, one_year_return);

-- Factor indexes
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

-- Market quotes indexes
CREATE INDEX idx_market_quotes_fetched_at ON market_quotes(fetched_at);
CREATE INDEX idx_market_quotes_source ON market_quotes(source);
CREATE INDEX idx_market_quotes_quote_time ON market_quotes(quote_time);

-- Watchlist index
CREATE INDEX idx_watchlist_created_at ON watchlist(created_at);
