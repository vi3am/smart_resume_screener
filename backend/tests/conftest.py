import os

import pytest
from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine import make_url


def pytest_configure() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        raise pytest.UsageError(
            "Set TEST_DATABASE_URL to a dedicated PostgreSQL database whose name "
            "ends in '_test' before running backend tests."
        )

    try:
        database_url = make_url(test_database_url)
    except ArgumentError as exc:
        raise pytest.UsageError("TEST_DATABASE_URL is not a valid SQLAlchemy URL.") from exc

    if (
        database_url.get_backend_name() != "postgresql"
        or not (database_url.database or "").endswith("_test")
    ):
        raise pytest.UsageError(
            "Backend tests require a PostgreSQL TEST_DATABASE_URL whose database "
            "name ends in '_test'; refusing to use any other database."
        )

    # Settings reads DATABASE_URL from the environment before backend/.env.
    os.environ["DATABASE_URL"] = test_database_url
