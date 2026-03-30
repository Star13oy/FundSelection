from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

from app.database_adapter import get_adapter

logger = logging.getLogger(__name__)

# Global adapter instance
_adapter = get_adapter()


@lru_cache(maxsize=1)
def settings() -> dict[str, str]:
    """Return database connection settings from environment variables."""
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": os.getenv("MYSQL_PORT", "3306"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DATABASE", "fund_selection"),
        "db_type": os.getenv("DB_TYPE", "sqlite"),  # 默认使用SQLite
    }


def connect(with_database: bool = True):
    """
    Create a database connection using the configured adapter.

    Args:
        with_database: If True, connect to the specific database.
                     If False, connect without selecting a database (MySQL only).

    Returns:
        Database connection object
    """
    return _adapter.connect(with_database=with_database)


def init_db() -> None:
    """
    Initialize the database schema.

    This function creates the database (if needed) and all tables using
    the configured database adapter. It handles both MySQL and SQLite.
    """
    try:
        _adapter.init_database()
        logger.info(f"Database initialized successfully using {settings()['db_type']}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_upsert_syntax(table: str, columns: list[str], update_columns: list[str]) -> str:
    """
    Generate UPSERT syntax for the current database backend.

    Args:
        table: Table name
        columns: All columns being inserted
        update_columns: Columns to update on conflict

    Returns:
        Complete UPSERT SQL statement

    Example:
        sql = get_upsert_syntax("funds", ["code", "name"], ["name"])
        # MySQL: INSERT INTO funds (code, name) VALUES (%s, %s)
        #        ON DUPLICATE KEY UPDATE name=VALUES(name)
        # SQLite: INSERT INTO funds (code, name) VALUES (?, ?)
        #         ON CONFLICT(code) DO UPDATE SET name=excluded.name
    """
    return _adapter.get_upsert_syntax(table, columns, update_columns)


def get_insert_ignore_syntax(table: str, columns: list[str]) -> str:
    """
    Generate INSERT IGNORE syntax for the current database backend.

    Args:
        table: Table name
        columns: Columns to insert

    Returns:
        Complete INSERT IGNORE SQL statement

    Example:
        sql = get_insert_ignore_syntax("watchlist", ["code"])
        # MySQL: INSERT IGNORE INTO watchlist (code) VALUES (%s)
        # SQLite: INSERT OR IGNORE INTO watchlist (code) VALUES (?)
    """
    return _adapter.get_insert_ignore_syntax(table, columns)


def get_current_timestamp() -> str:
    """
    Return the current timestamp function for the current database backend.

    Returns:
        Timestamp function (e.g., "NOW()" for MySQL, "datetime('now')" for SQLite)
    """
    return _adapter.get_current_timestamp()


def get_json_column_type() -> str:
    """
    Return the JSON column type for the current database backend.

    Returns:
        JSON column type (e.g., "JSON" for MySQL, "TEXT" for SQLite)
    """
    return _adapter.get_json_column_type()
