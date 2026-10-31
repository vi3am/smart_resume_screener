from app.services.fields import education_levels
from app.services.parser import parse_resume


def test_parser_keeps_unlisted_skills_when_known_skills_are_present():
    parsed = parse_resume(
        "Skills\nPython\nCybersecurity\nStakeholder Management\nExcel\n"
        "Education\nBSc in Information Technology"
    )

    assert parsed["skills"] == [
        "python",
        "excel",
        "Cybersecurity",
        "Stakeholder Management",
    ]
    assert parsed["education_level"] == "bachelor"


def test_parser_extracts_inline_technical_skills_heading():
    parsed = parse_resume(
        "Technical Skills: Python, Kubernetes, Go\n"
        "Experience\nBackend Engineer\n"
    )

    assert parsed["skills"] == ["python", "Kubernetes", "Go"]


def test_parser_stops_skills_at_professional_experience_heading():
    parsed = parse_resume(
        "Skills\nPython\nCybersecurity\n"
        "Professional Experience\n"
        "Security Analyst — investigated incidents\n"
    )

    assert parsed["skills"] == ["python", "Cybersecurity"]


def test_parser_filters_prose_and_placeholder_text_from_skill_sections():
    parsed = parse_resume(
        "Skills\n"
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        "Project Management\n"
        "Developed integrated strategy across digital and offline channels.\n"
        "About me\n"
        "Created a game-based learning activity."
    )

    assert parsed["skills"] == ["project management"]


def test_parser_splits_bullet_separated_skill_items():
    parsed = parse_resume(
        "Skills\n"
        "Customer Service • Sales & Product Recommendations • Beauty Advising • "
        "Content Creation"
    )

    assert parsed["skills"] == [
        "customer service",
        "Sales & Product Recommendations",
        "Beauty Advising",
        "Content Creation",
    ]


def test_parser_does_not_read_year_range_as_phone_number():
    parsed = parse_resume(
        "Alex Morgan\n"
        "Experience\n"
        "2022 - 2035\n"
        "Phone: +1 (202) 555-0142"
    )

    assert parsed["phone"] == "+1 (202) 555-0142"


def test_education_recognizes_common_abbreviated_degrees_and_progress():
    text = (
        "Education\n"
        "B.Tech in Information Technology\n"
        "M.Tech in Computer Science — Expected 2027"
    )

    assert education_levels(text) == ("bachelor", "master")
