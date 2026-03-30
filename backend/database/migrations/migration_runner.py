"""
Migration runner for database schema version control.

This module provides functionality to track and execute database migrations
in a version-controlled manner with rollback support.

Usage:
    python -m database.migrations.migration_runner upgrade
    python -m database.migrations.migration_runner downgrade
    python -m database.migrations.migration_runner status
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Any

from app.database_adapter import create_adapter

logger = logging.getLogger(__name__)

# Migration tracking table
MIGRATION_TABLE = "schema_migrations"


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: int, name: str, up_sql: str, down_sql: str | None = None):
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql

    @property
    def filename(self) -> str:
        """Generate migration filename from version and name."""
        return f"migration_{self.version:03d}_{self.name}.sql"


def create_migration_table(adapter: Any) -> None:
    """Create the migration tracking table if it doesn't exist."""
    with adapter.connection_context() as conn:
        cursor = conn.cursor()
        db_type = os.getenv("DB_TYPE", "mysql").lower()

        if db_type == "sqlite":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
        else:  # MySQL
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version BIGINT UNSIGNED PRIMARY KEY,
                    name VARCHAR(256) NOT NULL,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
        conn.commit()


def get_applied_migrations(adapter: Any) -> set[int]:
    """Get set of applied migration versions."""
    with adapter.connection_context() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT version FROM schema_migrations")
            return {row["version"] for row in cursor.fetchall()}
        except Exception:
            # Table doesn't exist yet
            return set()


def get_available_migrations() -> list[Migration]:
    """Load all available migration files from the migrations directory."""
    migrations_dir = os.path.join(
        os.path.dirname(__file__), "migrations"
    )

    if not os.path.exists(migrations_dir):
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return []

    migrations = []
    pattern = re.compile(r"migration_(\d+)_([^\.]+)\.sql")

    for filename in sorted(os.listdir(migrations_dir)):
        match = pattern.match(filename)
        if not match:
            continue

        version = int(match.group(1))
        name = match.group(2)

        filepath = os.path.join(migrations_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Split up and down migrations
        parts = sql_content.split("-- @DOWN")
        up_sql = parts[0].strip()
        down_sql = parts[1].strip() if len(parts) > 1 else None

        migrations.append(Migration(version, name, up_sql, down_sql))

    return sorted(migrations, key=lambda m: m.version)


def apply_migration(adapter: Any, migration: Migration) -> None:
    """Apply a single migration."""
    logger.info(f"Applying migration {migration.version}: {migration.name}")

    with adapter.connection_context() as conn:
        cursor = conn.cursor()

        # Execute migration SQL
        try:
            cursor.execute(migration.up_sql)
        except Exception as e:
            logger.error(f"Error applying migration {migration.version}: {e}")
            conn.rollback()
            raise

        # Record migration
        db_type = os.getenv("DB_TYPE", "mysql").lower()
        if db_type == "sqlite":
            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, datetime.now().isoformat())
            )
        else:  # MySQL
            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (%s, %s, NOW())",
                (migration.version, migration.name)
            )

        conn.commit()
    logger.info(f"Successfully applied migration {migration.version}")


def rollback_migration(adapter: Any, migration: Migration) -> None:
    """Rollback a single migration."""
    if not migration.down_sql:
        logger.warning(f"Migration {migration.version} has no rollback defined")
        return

    logger.info(f"Rolling back migration {migration.version}: {migration.name}")

    with adapter.connection_context() as conn:
        cursor = conn.cursor()

        # Execute rollback SQL
        try:
            cursor.execute(migration.down_sql)
        except Exception as e:
            logger.error(f"Error rolling back migration {migration.version}: {e}")
            conn.rollback()
            raise

        # Remove migration record
        db_type = os.getenv("DB_TYPE", "mysql").lower()
        if db_type == "sqlite":
            cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (migration.version,))
        else:  # MySQL
            cursor.execute("DELETE FROM schema_migrations WHERE version = %s", (migration.version,))

        conn.commit()
    logger.info(f"Successfully rolled back migration {migration.version}")


def upgrade(target_version: int | None = None) -> None:
    """
    Upgrade database to the latest version or a specific version.

    Args:
        target_version: If specified, upgrade only to this version.
                       Otherwise, upgrade to the latest available.
    """
    adapter = create_adapter()
    create_migration_table(adapter)

    applied = get_applied_migrations(adapter)
    available = get_available_migrations()

    if not available:
        logger.info("No migrations available")
        return

    # Filter migrations to apply
    to_apply = [m for m in available if m.version not in applied]
    if target_version is not None:
        to_apply = [m for m in to_apply if m.version <= target_version]

    if not to_apply:
        logger.info("Database is already up to date")
        return

    logger.info(f"Found {len(to_apply)} migration(s) to apply")

    for migration in to_apply:
        apply_migration(adapter, migration)

    logger.info("Upgrade complete")


def downgrade(target_version: int) -> None:
    """
    Downgrade database to a specific version.

    Args:
        target_version: Version to downgrade to. All migrations newer than
                       this version will be rolled back.
    """
    adapter = create_adapter()
    create_migration_table(adapter)

    applied = get_applied_migrations(adapter)
    available = get_available_migrations()

    # Filter migrations to rollback
    to_rollback = [m for m in available if m.version in applied and m.version > target_version]
    to_rollback = sorted(to_rollback, key=lambda m: m.version, reverse=True)

    if not to_rollback:
        logger.info(f"Database is already at version {target_version} or lower")
        return

    logger.info(f"Found {len(to_rollback)} migration(s) to rollback")

    for migration in to_rollback:
        rollback_migration(adapter, migration)

    logger.info("Downgrade complete")


def status() -> None:
    """Show current migration status."""
    adapter = create_adapter()
    create_migration_table(adapter)

    applied = get_applied_migrations(adapter)
    available = get_available_migrations()

    print("\n=== Migration Status ===\n")

    if not available:
        print("No migrations available")
        return

    latest_version = max(m.version for m in available)
    current_version = max(applied) if applied else 0

    print(f"Current version: {current_version}")
    print(f"Latest version: {latest_version}")
    print(f"Applied migrations: {len(applied)}")
    print(f"Pending migrations: {len(available) - len(applied)}")

    print("\nMigration History:")
    for migration in available:
        status_symbol = "✓" if migration.version in applied else " "
        print(f"  [{status_symbol}] {migration.version:03d} - {migration.name}")

    print()


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) < 2:
        print("Usage: python migration_runner.py [upgrade|downgrade|status] [version]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "upgrade":
        version = int(sys.argv[2]) if len(sys.argv) > 2 else None
        upgrade(version)
    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("Error: downgrade requires a target version")
            sys.exit(1)
        version = int(sys.argv[2])
        downgrade(version)
    elif command == "status":
        status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
