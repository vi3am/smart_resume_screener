from datetime import date

from app.services.fields import education_levels, years_of_experience

NOW = date(2026, 10, 18)


def yrs(text):
    return years_of_experience(text, as_of=NOW)


def test_months_are_counted():
    assert yrs("Experience\nJan 2024 - July 2024") == 0.5


def test_year_only_range():
    assert yrs("Work Experience\nDeveloper\n2022 - 2024") == 2.0


def test_present_uses_as_of_date():
    assert yrs("Experience\nOct 2025 - Present") == 1.0


def test_overlapping_jobs_are_merged():
    assert yrs("Experience\n2020 - 2023\n2022 - 2024") == 4.0


def test_education_dates_are_not_experience():
    text = "Education\nBachelor of Arts\n2019 - 2023\nWork Experience\nDeveloper\n2023 - 2025"
    assert yrs(text) == 2.0


def test_future_dates_are_ignored():
    assert yrs("Experience\n2040 - 2043") == 0.0


def test_cv_without_headings_uses_all_non_education_lines():
    assert yrs("Designer 2018 - 2020") == 2.0
    assert yrs("University of Arts 2018 - 2022") == 0.0


def test_headings_but_no_experience_section_gives_zero():
    assert yrs("Skills\nPython\n2018 - 2020") == 0.0


def test_in_progress_degree_is_reported_separately():
    text = ("Associate Degree, Software Development — IT STEP Cambodia 2024 – Present\n"
            "Baccalaureate Degree — Cheasimsamaki High School 2017 – 2023")
    assert education_levels(text) == ("high_school", "associate")


def test_in_progress_bachelor():
    assert education_levels("Bachelor's Degree, Economics (In Progress)") == (None, "bachelor")


def test_scrum_master_is_not_a_degree():
    assert education_levels("Scrum Master") == (None, None)


def test_standalone_level_lines():
    text = ("Master\n2013 - 2016 | BORCELLE UNIVERSITY\n"
            "Bachelor\n2010 - 2013 | BORCELLE UNIVERSITY\nHigh School Diploma")
    assert education_levels(text) == ("master", None)


def test_masters_in():
    assert education_levels("Masters in Product Design\nBA in Product Design") == ("master", None)


def test_education_ignores_degree_like_phrases_outside_education_section():
    text = (
        "Professional Summary\n"
        "Master of customer experience with a Bachelor of Arts degree.\n"
        "Education\n"
        "Bachelor of Arts, Communications\n"
        "Work Experience\n"
        "Master of Ceremonies at community events."
    )

    assert education_levels(text) == ("bachelor", None)


def test_education_section_still_reports_completed_and_in_progress_degrees():
    text = (
        "Experience\n"
        "Master of Customer Experience\n"
        "Education\n"
        "High School Diploma\n"
        "Bachelor's Degree — Expected 2027\n"
        "Skills\n"
        "Master of Arts"
    )

    assert education_levels(text) == ("high_school", "bachelor")