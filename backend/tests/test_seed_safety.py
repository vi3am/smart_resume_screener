import pytest

from app.config import settings
from app.seed import reset_data


def test_seed_refuses_to_clear_non_test_database(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://localhost/resume_screener")

    with pytest.raises(RuntimeError, match="Refusing to clear a non-test database"):
        reset_data(None)
