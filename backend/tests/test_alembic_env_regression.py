import os
from pathlib import Path

from app.services.file_utils import build_stored_filename
from app.services.parser import parse_resume


def test_alembic_env_defines_context_config_before_setting_url():
    env_path = Path("alembic/env.py")
    content = env_path.read_text()

    config_assignment_index = content.index("config = context.config")
    config_set_index = content.index('config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)')

    assert config_assignment_index < config_set_index


def test_parse_resume_rejects_title_as_candidate_name():
    text = (
        "Accounting Executive\n"
        "hello@reallygreatsite.com\n"
        "+123-456-7890\n"
        "data analysis time management customer service"
    )

    parsed = parse_resume(text)

    assert parsed["name"] is None
    assert parsed["email"] == "hello@reallygreatsite.com"
    assert parsed["phone"] == "+123-456-7890"


def test_parse_resume_rejects_url_domain_text_as_candidate_name():
    text = (
        "www.reallygreatsite.com\n"
        "hello@reallygreatsite.com\n"
        "+123-456-7890\n"
        "data analysis time management customer service"
    )

    parsed = parse_resume(text)

    assert parsed["name"] is None
    assert parsed["email"] == "hello@reallygreatsite.com"
    assert parsed["phone"] == "+123-456-7890"


def test_build_stored_filename_returns_safe_upload_name():
    result = build_stored_filename(None, "../Bad CV John Smith (final).pdf")

    stored_filename = result["stored_filename"]
    assert stored_filename.endswith(".pdf")
    assert os.path.basename(stored_filename) == stored_filename
    assert "/" not in stored_filename
    assert ".." not in stored_filename
    assert "bad_cv_john_smith_final" in stored_filename


def test_parse_resume_rejects_summary_experience_as_candidate_name():
    text = (
        "SUMMARY EXPERIENCE\n"
        "hello@reallygreatsite.com\n"
        "+123-456-7890\n"
        "git teamwork time management communication leadership"
    )

    parsed = parse_resume(text)

    assert parsed["name"] is None
    assert parsed["email"] == "hello@reallygreatsite.com"
    assert parsed["phone"] == "+123-456-7890"


def test_parse_resume_rejects_detail_section_label_as_candidate_name():
    text = (
        "Detail\n"
        "hello@reallygreatsite.com\n"
        "+123-456-7890\n"
        "git teamwork time management communication leadership"
    )

    parsed = parse_resume(text)

    assert parsed["name"] is None
    assert parsed["email"] == "hello@reallygreatsite.com"
    assert parsed["phone"] == "+123-456-7890"


def test_parse_resume_rejects_placeholder_text_as_candidate_name():
    text = (
        "dolore magna aliqua\n"
        "hello@reallygreatsite.com\n"
        "+123-456-7890\n"
        "git teamwork time management communication leadership"
    )

    parsed = parse_resume(text)

    assert parsed["name"] is None
