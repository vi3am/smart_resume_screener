import re
import zlib

import numpy as np
import pytest

from app.services.scoring import (
    education_score, experience_score, match_skills, score_cv,
    semantic_score, skills_score, split_sections,
)


def fake_embed(texts):
    vecs = []
    for t in texts:
        v = np.zeros(64)
        for w in re.findall(r"[a-z]+", t.lower()):
            v[zlib.crc32(w.encode()) % 64] += 1.0
        vecs.append(v)
    return vecs


def test_skill_match_with_plural_and_missing():
    matched, missing = match_skills(["Kotlin", "REST API", "Git"],
                                    "Built apps in Kotlin using REST APIs.")
    assert matched == ["Kotlin", "REST API"] and missing == ["Git"]
    assert skills_score(matched, missing) == 66.67


def test_skill_aliases():
    matched, _ = match_skills(["PostgreSQL", "JavaScript"], "I use postgres and JS daily")
    assert matched == ["PostgreSQL", "JavaScript"]


def test_skill_match_needs_whole_words():
    _, missing = match_skills(["Git"], "digital marketing")
    assert missing == ["Git"]


def test_no_required_skills_scores_100():
    assert skills_score(*match_skills([], "anything")) == 100.0


def test_experience_score():
    assert experience_score(1, 2) == 50.0
    assert experience_score(3, 2) == 100.0
    assert experience_score(0, 0) == 100.0


def test_education_score():
    assert education_score("bachelor", None, "associate") == 100.0
    assert education_score(None, "bachelor", "bachelor") == 70.0
    assert education_score("high_school", None, "associate") == 50.0
    assert education_score(None, None, "bachelor") == 0.0
    assert education_score("high_school", None, "high_school") == 100.0


def test_split_sections():
    text = "Summary\nAbout me line one is long enough\nSkills\nPython and SQL and git"
    assert len(split_sections(text)) == 2


def test_semantic_prefers_relevant_cv():
    job = "android kotlin mobile developer"
    relevant = "Experience\nBuilt android mobile apps with kotlin for clients"
    other = "Experience\nServed customers and managed the restaurant cashier desk daily"
    assert (semantic_score(job, relevant, fake_embed, k=1, lo=0.0, hi=1.0)
            > semantic_score(job, other, fake_embed, k=1, lo=0.0, hi=1.0))


def test_one_relevant_section_is_enough_for_top_k():
    job = "android kotlin mobile developer"
    mixed = ("Summary\nloves cooking and travel often\n"
             "Experience\nBuilt android mobile apps with kotlin")
    other = "Summary\nloves cooking and travel often\nExperience\nserved customers at the restaurant"
    assert (semantic_score(job, mixed, fake_embed, k=1, lo=0.0, hi=1.0)
            > semantic_score(job, other, fake_embed, k=1, lo=0.0, hi=1.0))


POSTING = {"title": "Dev", "description": "x", "required_skills": ["Kotlin", "Git"],
           "min_years_experience": 2, "min_education_level": "associate"}
FIELDS = {"years_experience": 3.0, "education_level": "bachelor", "education_in_progress": None}


def test_overall_is_weighted_average():
    r = score_cv(POSTING, "I know Kotlin", fields=FIELDS, embed=fake_embed,
                weights={"skills": 0.5, "experience": 0.5, "education": 0.0, "semantic": 0.0})
    assert (r.skills, r.experience, r.education) == (50.0, 100.0, 100.0)
    assert r.overall == 75.0
    assert r.matched_skills == ["Kotlin"] and r.missing_skills == ["Git"]


def test_bad_weights_are_rejected():
    with pytest.raises(ValueError):
        score_cv(POSTING, "x", fields=FIELDS, embed=fake_embed, weights={"skills": 1.0})