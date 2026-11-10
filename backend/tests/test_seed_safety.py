import pytest

from app.config import settings
from app.seed import reset_data, validate_seed_password


def test_seed_refuses_to_clear_non_test_database(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://localhost/resume_screener")

    with pytest.raises(RuntimeError, match="Refusing to clear a non-test database"):
        reset_data(None)


def test_seed_password_must_be_unique_length_range():
    with pytest.raises(ValueError, match="at least 16"):
        validate_seed_password("too-short")
    with pytest.raises(ValueError, match="at most 72"):
        validate_seed_password("x" * 73)

    validate_seed_password("a unique seed password")
