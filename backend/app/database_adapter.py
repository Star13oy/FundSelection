"""
Database adapter layer supporting both SQLite and MySQL.

This module provides a unified interface for database operations across different
database backends, handling SQL dialect differences transparently.

Environment Variables:
    DB_TYPE: Database type - "sqlite" or "mysql" (default: "mysql")
    MYSQL_HOST: MySQL host (default: 127.0.0.1)
    MYSQL_PORT: MySQL port (default: 3306)
    MYSQL_USER: MySQL user (default: root)
    MYSQL_PASSWORD: MySQL password (default: root)
    MYSQL_DATABASE: MySQL database name (default: fund_selection)
    SQLITE_PATH: Path to SQLite database file (default: ./fund_selection.db)
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator

import pymysql
from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.

    All database-specific implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def connect(self, **kwargs: Any) -> Any:
        """Create and return a database connection."""

    @abstractmethod
    def init_database(self) -> None:
        """Initialize database schema and create tables."""

    @abstractmethod
    def get_upsert_syntax(self, table: str, columns: list[str], update_columns: list[str]) -> str:
        """
        Generate UPSERT syntax (INSERT ... ON CONFLICT/ON DUPLICATE KEY).

        Args:
            table: Table name
            columns: All columns being inserted
            update_columns: Columns to update on conflict

        Returns:
            Complete UPSERT SQL statement
        """

    @abstractmethod
    def get_insert_ignore_syntax(self, table: str, columns: list[str]) -> str:
        """
        Generate INSERT IGNORE syntax.

        Args:
            table: Table name
            columns: Columns to insert

        Returns:
            Complete INSERT IGNORE SQL statement
        """

    @abstractmethod
    def get_auto_increment(self) -> str:
        """Return AUTO_INCREMENT/AUTOINCREMENT keyword for this database."""

    @abstractmethod
    def get_current_timestamp(self) -> str:
        """Return current timestamp function (e.g., NOW() or datetime('now'))."""

    @abstractmethod
    def get_datetime_literal(self, dt: datetime) -> str:
        """Return datetime as SQL literal string."""

    @abstractmethod
    def get_json_column_type(self) -> str:
        """Return JSON column type for this database."""

    @abstractmethod
    def execute_sql_file(self, connection: Any, file_path: str) -> None:
        """Execute SQL commands from a file."""

    @contextmanager
    @abstractmethod
    def connection_context(self) -> Generator[Any, None, None]:
        """Context manager for database connections with automatic cleanup."""


class SQLiteCursorWrapper:
    """Wrapper for SQLite cursor to support context manager protocol and MySQL compatibility."""

    def __init__(self, cursor: Any) -> None:
        self.cursor = cursor

    def __enter__(self) -> Any:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # No explicit close needed for SQLite cursor
        pass

    def _convert_params(self, sql: str, params: Any) -> tuple[str, Any]:
        """
        Convert MySQL-style parameters to SQLite-style parameters.

        Handles both positional (%s) and named (%(name)s) parameters.
        """
        import re

        # Check if using named parameters
        if re.search(r'%\(\w+\)s', sql):
            # Convert %(name)s to :name
            sql_sqlite = re.sub(r'%\((\w+)\)s', r':\1', sql)
            return sql_sqlite, params
        else:
            # Convert %s to ?
            sql_sqlite = sql.replace('%s', '?')
            return sql_sqlite, params

    def execute(self, sql: str, params: Any = None) -> Any:
        """Execute SQL query and return self for chaining."""
        sql_sqlite, params_sqlite = self._convert_params(sql, params or ())
        self.cursor.execute(sql_sqlite, params_sqlite)
        return self

    def executemany(self, sql: str, params: list[Any] = None) -> Any:
        """Execute many SQL queries."""
        if not params:
            return self

        sql_sqlite, _ = self._convert_params(sql, params[0])
        self.cursor.executemany(sql_sqlite, params)
        return self

    def fetchone(self) -> dict[str, Any] | None:
        """Fetch one row and convert to dict."""
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row) if row else None

    def fetchall(self) -> list[dict[str, Any]]:
        """Fetch all rows and convert to dicts."""
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attribute access to the underlying cursor."""
        return getattr(self.cursor, name)


class SQLiteConnectionWrapper:
    """Wrapper for SQLite connection to provide MySQL-compatible cursor method."""

    def __init__(self, conn: Any) -> None:
        self.conn = conn

    def cursor(self, *args: Any, **kwargs: Any) -> SQLiteCursorWrapper:
        """Return a wrapped cursor that supports context managers."""
        return SQLiteCursorWrapper(self.conn.cursor(*args, **kwargs))

    def __enter__(self) -> Any:
        self.conn.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.conn.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attribute access to the underlying connection."""
        return getattr(self.conn, name)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter implementation."""

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize SQLite adapter.

        Args:
            db_path: Path to SQLite database file. If None, uses SQLITE_PATH env var
                     or defaults to './fund_selection.db'
        """
        self.db_path = db_path or os.getenv("SQLITE_PATH", "./fund_selection.db")
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for the database file exists."""
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def connect(self, with_database: bool = True, **kwargs: Any) -> Any:
        """
        Create SQLite connection.

        Args:
            with_database: Ignored for SQLite (always uses the database file)
            **kwargs: Additional connection parameters
        """
        import sqlite3

        # Remove with_database from kwargs if present
        kwargs.pop('with_database', None)

        conn = sqlite3.connect(self.db_path, **kwargs)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return SQLiteConnectionWrapper(conn)

    def init_database(self) -> None:
        """Initialize SQLite database schema."""
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "database", "schema_sqlite.sql"
        )
        if not os.path.exists(schema_path):
            logger.warning(f"SQLite schema file not found: {schema_path}")
            return

        with self.connection_context() as conn:
            self.execute_sql_file(conn, schema_path)

    def get_upsert_syntax(
        self, table: str, columns: list[str], update_columns: list[str]
    ) -> str:
        """
        Generate SQLite UPSERT syntax (INSERT ... ON CONFLICT DO UPDATE).

        Example:
            adapter.get_upsert_syntax("funds", ["code", "name"], ["name"])
            Returns: "INSERT INTO funds (code, name) VALUES (?, ?)
                      ON CONFLICT(code) DO UPDATE SET name=excluded.name"
        """
        placeholders = ", ".join([":{}".format(col) for col in columns])
        column_list = ", ".join(columns)
        conflict_target = columns[0]  # First column is typically primary key

        update_clauses = []
        for col in update_columns:
            update_clauses.append(f"{col}=excluded.{col}")

        return f"""
            INSERT INTO {table} ({column_list})
            VALUES ({placeholders})
            ON CONFLICT({conflict_target}) DO UPDATE SET
                {', '.join(update_clauses)}
        """.strip()

    def get_insert_ignore_syntax(self, table: str, columns: list[str]) -> str:
        """Generate SQLite INSERT OR IGNORE syntax."""
        placeholders = ", ".join([":{}".format(col) for col in columns])
        column_list = ", ".join(columns)
        return f"INSERT OR IGNORE INTO {table} ({column_list}) VALUES ({placeholders})"

    def get_auto_increment(self) -> str:
        """Return AUTOINCREMENT keyword for SQLite."""
        return "AUTOINCREMENT"

    def get_current_timestamp(self) -> str:
        """Return SQLite current timestamp function."""
        return "datetime('now')"

    def get_datetime_literal(self, dt: datetime) -> str:
        """Return datetime as SQLite literal string."""
        return f"'{dt.isoformat()}'"

    def get_json_column_type(self) -> str:
        """Return JSON column type for SQLite (TEXT with JSON validation)."""
        return "TEXT"

    def execute_sql_file(self, connection: Any, file_path: str) -> None:
        """Execute SQL commands from a file in SQLite."""
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        cursor = connection.cursor()

        for statement in statements:
            try:
                cursor.execute(statement)
            except Exception as e:
                logger.error(f"Error executing SQL statement: {e}\nStatement: {statement[:200]}")
                raise

        connection.commit()

    @contextmanager
    def connection_context(self) -> Generator[Any, None, None]:
        """Context manager for SQLite connections."""
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter implementation with connection pooling."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ) -> None:
        """
        Initialize MySQL adapter.

        Args:
            host: MySQL host. If None, uses MYSQL_HOST env var or default 127.0.0.1
            port: MySQL port. If None, uses MYSQL_PORT env var or default 3306
            user: MySQL user. If None, uses MYSQL_USER env var or default root
            password: MySQL password. If None, uses MYSQL_PASSWORD env var or default root
            database: MySQL database name. If None, uses MYSQL_DATABASE env var
                     or default fund_selection
        """
        self.host = host or os.getenv("MYSQL_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("MYSQL_PORT", "3306"))
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "root")
        self.database = database or os.getenv("MYSQL_DATABASE", "fund_selection")
        self._connection_pool: list[Any] = []
        self._max_pool_size = 10

    def connect(self, with_database: bool = True, **kwargs: Any) -> Any:
        """
        Create MySQL connection.

        Args:
            with_database: If True, connect to the specific database.
                         If False, connect without selecting a database.
        """
        params = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "autocommit": False,
            "connect_timeout": 10,
        }

        if with_database:
            params["database"] = self.database

        try:
            conn = pymysql.connect(**params)
            return conn
        except pymysql.Error as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def init_database(self) -> None:
        """Initialize MySQL database schema."""
        # Create database if not exists
        with self.connect(with_database=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                conn.commit()

        # Execute schema file
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "database", "schema_mysql.sql"
        )
        if not os.path.exists(schema_path):
            logger.warning(f"MySQL schema file not found: {schema_path}")
            return

        with self.connection_context() as conn:
            self.execute_sql_file(conn, schema_path)

    def get_upsert_syntax(
        self, table: str, columns: list[str], update_columns: list[str]
    ) -> str:
        """
        Generate MySQL UPSERT syntax (INSERT ... ON DUPLICATE KEY UPDATE).

        Example:
            adapter.get_upsert_syntax("funds", ["code", "name"], ["name"])
            Returns: "INSERT INTO funds (code, name) VALUES (%s, %s)
                      ON DUPLICATE KEY UPDATE name=VALUES(name)"
        """
        placeholders = ", ".join(["%s" for _ in columns])
        column_list = ", ".join(columns)

        update_clauses = []
        for col in update_columns:
            update_clauses.append(f"{col}=VALUES({col})")

        return f"""
            INSERT INTO {table} ({column_list})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
                {', '.join(update_clauses)}
        """

    def get_insert_ignore_syntax(self, table: str, columns: list[str]) -> str:
        """Generate MySQL INSERT IGNORE syntax."""
        placeholders = ", ".join(["%s" for _ in columns])
        column_list = ", ".join(columns)
        return f"INSERT IGNORE INTO {table} ({column_list}) VALUES ({placeholders})"

    def get_auto_increment(self) -> str:
        """Return AUTO_INCREMENT keyword for MySQL."""
        return "AUTO_INCREMENT"

    def get_current_timestamp(self) -> str:
        """Return MySQL current timestamp function."""
        return "NOW()"

    def get_datetime_literal(self, dt: datetime) -> str:
        """Return datetime as MySQL literal string."""
        return f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'"

    def get_json_column_type(self) -> str:
        """Return JSON column type for MySQL."""
        return "JSON"

    def execute_sql_file(self, connection: Any, file_path: str) -> None:
        """Execute SQL commands from a file in MySQL."""
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        cursor = connection.cursor()

        for statement in statements:
            try:
                cursor.execute(statement)
            except Exception as e:
                logger.error(f"Error executing SQL statement: {e}\nStatement: {statement[:200]}")
                connection.rollback()
                raise

        connection.commit()

    @contextmanager
    def connection_context(self) -> Generator[Any, None, None]:
        """Context manager for MySQL connections with automatic reconnection."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except pymysql.Error as e:
            logger.error(f"MySQL error: {e}")
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing MySQL connection: {e}")


def create_adapter() -> DatabaseAdapter:
    """
    Factory function to create the appropriate database adapter.

    Reads the DB_TYPE environment variable to determine which adapter to create.
    Defaults to SQLite if DB_TYPE is not set.

    Returns:
        DatabaseAdapter instance (SQLiteAdapter or MySQLAdapter)

    Raises:
        ValueError: If DB_TYPE is neither "sqlite" nor "mysql"
    """
    db_type = os.getenv("DB_TYPE", "sqlite").lower()

    if db_type == "sqlite":
        logger.info("Initializing SQLite database adapter")
        return SQLiteAdapter()
    elif db_type == "mysql":
        logger.info("Initializing MySQL database adapter")
        return MySQLAdapter()
    else:
        raise ValueError(
            f"Unsupported DB_TYPE: {db_type}. Must be 'sqlite' or 'mysql'"
        )


# Global adapter instance
_adapter: DatabaseAdapter | None = None


def get_adapter() -> DatabaseAdapter:
    """
    Get or create the global database adapter instance.

    Returns:
        DatabaseAdapter singleton instance
    """
    global _adapter
    if _adapter is None:
        _adapter = create_adapter()
    return _adapter


def reset_adapter() -> None:
    """Reset the global adapter instance (useful for testing)."""
    global _adapter
    _adapter = None
