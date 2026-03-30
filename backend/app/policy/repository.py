"""
Policy repository for database operations on policy events.

This module provides data access layer for policy events and sector mappings,
supporting both MySQL and SQLite databases through the adapter pattern.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from app.db import get_upsert_syntax
from app.policy.models import PolicyEvent, SectorPolicyMapping

logger = logging.getLogger(__name__)


class PolicyRepository:
    """Database operations for policy events.

    This repository handles CRUD operations for policy events and sector mappings,
    abstracting database-specific SQL differences.
    """

    def __init__(self, db_adapter: Any):
        """
        Initialize policy repository.

        Args:
            db_adapter: Database adapter instance (MySQLAdapter or SQLiteAdapter)
        """
        self.db = db_adapter

    def insert_policy(self, policy: PolicyEvent) -> bool:
        """
        Insert or update a policy event.

        Args:
            policy: PolicyEvent instance to insert/update

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db.connection_context() as conn:
                cursor = conn.cursor()

                # Serialize related_sectors and key_points as JSON
                sectors_json = json.dumps(policy.related_sectors, ensure_ascii=False)
                key_points_json = json.dumps(policy.key_points, ensure_ascii=False)

                sql = get_upsert_syntax(
                    table="policy_events",
                    columns=[
                        "policy_id",
                        "title",
                        "published_at",
                        "effective_from",
                        "expires_at",
                        "related_sectors",
                        "intensity_level",
                        "execution_status",
                        "impact_direction",
                        "policy_type",
                        "support_amount_billion",
                        "tax_incentive_rate",
                        "source_url",
                        "description",
                        "key_points",
                        "created_at",
                        "updated_at",
                    ],
                    update_columns=[
                        "title",
                        "effective_from",
                        "expires_at",
                        "related_sectors",
                        "intensity_level",
                        "execution_status",
                        "impact_direction",
                        "policy_type",
                        "support_amount_billion",
                        "tax_incentive_rate",
                        "source_url",
                        "description",
                        "key_points",
                        "updated_at",
                    ],
                )

                cursor.execute(
                    sql,
                    (
                        policy.policy_id,
                        policy.title,
                        policy.published_at,
                        policy.effective_from,
                        policy.expires_at,
                        sectors_json,
                        policy.intensity_level,
                        policy.execution_status,
                        policy.impact_direction,
                        policy.policy_type,
                        policy.support_amount_billion,
                        policy.tax_incentive_rate,
                        policy.source_url,
                        policy.description,
                        key_points_json,
                        policy.created_at,
                        policy.updated_at,
                    ),
                )

                logger.info(f"Inserted/updated policy: {policy.policy_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to insert policy {policy.policy_id}: {e}")
            return False

    def get_policy(self, policy_id: str) -> PolicyEvent | None:
        """
        Fetch a policy by ID.

        Args:
            policy_id: Policy identifier

        Returns:
            PolicyEvent if found, None otherwise
        """
        try:
            with self.db.connection_context() as conn:
                cursor = conn.cursor()

                sql = "SELECT * FROM policy_events WHERE policy_id = %s"
                cursor.execute(sql, (policy_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return self._row_to_policy_event(row)

        except Exception as e:
            logger.error(f"Failed to get policy {policy_id}: {e}")
            return None

    def list_policies(
        self,
        sector: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        intensity_min: int | None = None,
        execution_status: list[str] | None = None,
        limit: int = 100,
    ) -> list[PolicyEvent]:
        """
        List policies with optional filters.

        Args:
            sector: Filter by sector name
            start_date: Filter by published_at >= start_date
            end_date: Filter by published_at <= end_date
            intensity_min: Minimum intensity level
            execution_status: Filter by execution status list
            limit: Maximum number of results

        Returns:
            List of PolicyEvent objects sorted by published_at DESC
        """
        try:
            with self.db.connection_context() as conn:
                cursor = conn.cursor()

                # Build query with filters
                conditions = []
                params = []

                if sector:
                    # Use LIKE for SQLite compatibility (JSON_CONTAINS is MySQL-only)
                    conditions.append("related_sectors LIKE %s")
                    params.append(f'%"{sector}"%')

                if start_date:
                    conditions.append("published_at >= %s")
                    params.append(start_date)

                if end_date:
                    conditions.append("published_at <= %s")
                    params.append(end_date)

                if intensity_min is not None:
                    conditions.append("intensity_level >= %s")
                    params.append(intensity_min)

                if execution_status:
                    placeholders = ", ".join(["%s"] * len(execution_status))
                    conditions.append(f"execution_status IN ({placeholders})")
                    params.extend(execution_status)

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                sql = f"""
                    SELECT * FROM policy_events
                    WHERE {where_clause}
                    ORDER BY published_at DESC
                    LIMIT %s
                """

                cursor.execute(sql, params + [limit])
                rows = cursor.fetchall()

                return [self._row_to_policy_event(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list policies: {e}")
            return []

    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a policy by ID.

        Args:
            policy_id: Policy identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            with self.db.connection_context() as conn:
                cursor = conn.cursor()

                sql = "DELETE FROM policy_events WHERE policy_id = %s"
                cursor.execute(sql, (policy_id,))

                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted policy: {policy_id}")

                return deleted

        except Exception as e:
            logger.error(f"Failed to delete policy {policy_id}: {e}")
            return False

    def update_policy_status(self, policy_id: str, new_status: str) -> bool:
        """
        Update execution status of a policy.

        Args:
            policy_id: Policy identifier
            new_status: New execution status

        Returns:
            True if updated, False otherwise
        """
        try:
            with self.db.connection_context() as conn:
                cursor = conn.cursor()

                sql = """
                    UPDATE policy_events
                    SET execution_status = %s, updated_at = %s
                    WHERE policy_id = %s
                """

                cursor.execute(sql, (new_status, datetime.now(), policy_id))
                updated = cursor.rowcount > 0

                if updated:
                    logger.info(f"Updated policy {policy_id} status to {new_status}")

                return updated

        except Exception as e:
            logger.error(f"Failed to update policy status for {policy_id}: {e}")
            return False

    def get_sector_mapping(self, sector: str) -> SectorPolicyMapping | None:
        """
        Get sector-policy mapping (placeholder for future implementation).

        Args:
            sector: Sector name

        Returns:
            SectorPolicyMapping if found, None otherwise
        """
        # This is a placeholder - in a full implementation, this would
        # query a sector_mappings table. For now, we return None.
        logger.warning(f"Sector mapping not implemented for sector: {sector}")
        return None

    def _row_to_policy_event(self, row: dict[str, Any]) -> PolicyEvent:
        """
        Convert database row to PolicyEvent object.

        Args:
            row: Database row as dictionary

        Returns:
            PolicyEvent instance
        """
        # Parse JSON fields
        related_sectors = json.loads(row["related_sectors"]) if row.get("related_sectors") else []
        key_points = json.loads(row["key_points"]) if row.get("key_points") else []

        return PolicyEvent(
            policy_id=row["policy_id"],
            title=row["title"],
            published_at=row["published_at"],
            effective_from=row.get("effective_from"),
            expires_at=row.get("expires_at"),
            related_sectors=related_sectors,
            intensity_level=row["intensity_level"],
            execution_status=row["execution_status"],
            impact_direction=row["impact_direction"],
            policy_type=row["policy_type"],
            support_amount_billion=row.get("support_amount_billion"),
            tax_incentive_rate=row.get("tax_incentive_rate"),
            source_url=row.get("source_url"),
            description=row.get("description"),
            key_points=key_points,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
