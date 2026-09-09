from pathlib import Path


def test_alembic_env_defines_context_config_before_setting_url():
    env_path = Path("alembic/env.py")
    content = env_path.read_text()

    config_assignment_index = content.index("config = context.config")
    config_set_index = content.index('config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)')

    assert config_assignment_index < config_set_index
