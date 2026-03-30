-- Migration 004: Add Policy Events Table
-- This migration adds policy and regulatory event tracking
-- Applied: 2026-03-30

CREATE TABLE IF NOT EXISTS policy_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    policy_id VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(256) NOT NULL,
    published_at DATETIME NOT NULL,
    related_sectors JSON,
    intensity_level ENUM('high', 'medium', 'low'),
    execution_status ENUM('announced', 'implemented', 'cancelled'),
    impact_direction ENUM('positive', 'negative', 'neutral'),
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_policy_events_published_at ON policy_events(published_at);
CREATE INDEX idx_policy_events_intensity ON policy_events(intensity_level);
CREATE INDEX idx_policy_events_status ON policy_events(execution_status);
CREATE INDEX idx_policy_events_direction ON policy_events(impact_direction);
CREATE INDEX idx_policy_events_sectors ON policy_events(related_sectors(255));
