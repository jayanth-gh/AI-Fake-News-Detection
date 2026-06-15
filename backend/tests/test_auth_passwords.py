from app.core.security import normalize_password_for_hashing, get_password_hash, verify_password


def test_long_password_is_truncated_before_hashing_and_verifying():
    password = "a" * 100
    normalized = normalize_password_for_hashing(password)

    assert len(normalized.encode("utf-8")) <= 72

    hashed = get_password_hash(normalized)
    assert verify_password(normalized, hashed) is True
