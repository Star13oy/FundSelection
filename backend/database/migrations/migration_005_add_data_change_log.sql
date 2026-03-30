-- Migration 005: Add Data Change Log Table
-- This migration adds audit trail for data modifications
-- Applied: 2026-03-30

CREATE TABLE IF NOT EXISTS data_change_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(64) NOT NULL,
    action ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_fields JSON,
    changed_by VARCHAR(64)
);

CREATE INDEX idx_change_log_table ON data_change_log(table_name);
CREATE INDEX idx_change_log_record ON data_change_log(table_name, record_id);
CREATE INDEX idx_change_log_action ON data_change_log(action);
CREATE INDEX idx_change_log_changed_at ON data_change_log(changed_at);
