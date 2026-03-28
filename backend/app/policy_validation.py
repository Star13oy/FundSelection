from __future__ import annotations

from datetime import datetime


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def validate_policy_timestamps(
    published_at: str,
    effective_from: str,
    observed_at: str,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    try:
        published = parse_iso(published_at)
        effective = parse_iso(effective_from)
        observed = parse_iso(observed_at)
    except ValueError:
        return False, ["时间格式无效，需使用ISO-8601"]

    if effective < published:
        errors.append("生效时间不能早于发布时间")
    if observed < published:
        errors.append("观测时间不能早于发布时间（防未来函数）")
    if observed < effective:
        errors.append("观测时间不能早于生效时间")

    return len(errors) == 0, errors
