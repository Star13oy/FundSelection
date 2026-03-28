from app.policy_validation import validate_policy_timestamps


def test_validate_policy_timestamps_valid() -> None:
    valid, errors = validate_policy_timestamps(
        published_at="2026-03-01T09:00:00Z",
        effective_from="2026-03-02T09:00:00Z",
        observed_at="2026-03-05T09:00:00Z",
    )
    assert valid is True
    assert errors == []


def test_validate_policy_timestamps_invalid_order() -> None:
    valid, errors = validate_policy_timestamps(
        published_at="2026-03-05T09:00:00Z",
        effective_from="2026-03-01T09:00:00Z",
        observed_at="2026-03-02T09:00:00Z",
    )
    assert valid is False
    assert "生效时间不能早于发布时间" in errors
    assert "观测时间不能早于发布时间（防未来函数）" in errors


def test_validate_policy_timestamps_invalid_format() -> None:
    valid, errors = validate_policy_timestamps(
        published_at="invalid",
        effective_from="2026-03-01T09:00:00Z",
        observed_at="2026-03-02T09:00:00Z",
    )
    assert valid is False
    assert errors == ["时间格式无效，需使用ISO-8601"]
