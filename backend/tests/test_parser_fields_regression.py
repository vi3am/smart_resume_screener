from docx import Document

from app.services.fields import education_levels
from app.services.parser import extract_text, parse_resume


def test_docx_upload_extracts_skills_from_tables(tmp_path):
    document = Document()
    document.add_paragraph("Skills")
    table = document.add_table(rows=2, cols=1)
    table.cell(0, 0).text = "Kubernetes"
    table.cell(1, 0).text = "Stakeholder Management"
    document.add_paragraph("Experience")
    path = tmp_path / "resume.docx"
    document.save(path)

    parsed = parse_resume(extract_text(str(path)))

    assert parsed["skills"] == ["Kubernetes", "Stakeholder Management"]


def test_parser_extracts_column_skills_and_education_from_cv():
    parsed = parse_resume(
        "Harper Russo\n"
        "Skills & Expertise\n"
        "Web Design\tDesign Thinking\tWireframe Creation\tFront End Coding\t"
        "Backend Tech\tProblem-Solving\tComputer Literacy\t"
        "Project Management Tools\tStrong Communication\n"
        "Education\n"
        "Bachelor of Arts"
    )

    assert parsed["skills"] == [
        "Web Design",
        "Design Thinking",
        "Wireframe Creation",
        "Front End Coding",
        "Backend Tech",
        "Problem-Solving",
        "Computer Literacy",
        "Project Management Tools",
        "Strong Communication",
    ]
    assert parsed["education_level"] == "bachelor"


def test_parser_keeps_unlisted_skills_when_known_skills_are_present():
    parsed = parse_resume(
        "Skills\nPython\nCybersecurity\nStakeholder Management\nExcel\n"
        "Education\nBSc in Information Technology"
    )

    assert parsed["skills"] == [
        "Python",
        "Cybersecurity",
        "Stakeholder Management",
        "Excel",
    ]
    assert parsed["education_level"] == "bachelor"


def test_parser_extracts_inline_technical_skills_heading():
    parsed = parse_resume(
        "Technical Skills: Python, Kubernetes, Go\n"
        "Experience\nBackend Engineer\n"
    )

    assert parsed["skills"] == ["Python", "Kubernetes", "Go"]


def test_parser_stops_skills_at_professional_experience_heading():
    parsed = parse_resume(
        "Skills\nPython\nCybersecurity\n"
        "Professional Experience\n"
        "Security Analyst — investigated incidents\n"
    )

    assert parsed["skills"] == ["Python", "Cybersecurity"]


def test_parser_filters_prose_and_placeholder_text_from_skill_sections():
    parsed = parse_resume(
        "Skills\n"
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        "Project Management\n"
        "Developed integrated strategy across digital and offline channels.\n"
        "About me\n"
        "Created a game-based learning activity."
    )

    assert parsed["skills"] == ["Project Management"]


def test_parser_splits_bullet_separated_skill_items():
    parsed = parse_resume(
        "Skills\n"
        "Customer Service • Sales & Product Recommendations • Beauty Advising • "
        "Content Creation"
    )

    assert parsed["skills"] == [
        "Customer Service",
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
