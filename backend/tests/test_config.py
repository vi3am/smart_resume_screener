from app.config import Settings


def test_google_oauth_settings_are_optional():
    settings = Settings(
        _env_file=None,
        JWT_SECRET_KEY="test-secret",
        DATABASE_URL="postgresql://localhost/resume_screener_test",
    )

    assert settings.GOOGLE_CLIENT_ID is None
    assert settings.GOOGLE_CLIENT_SECRET is None
