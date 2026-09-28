from typing import Literal, get_args

EducationLevel = Literal["high_school", "associate", "bachelor", "master", "phd"]

EDUCATION_LEVELS: list[str] = list(get_args(EducationLevel))
EDUCATION_RANK: dict[str, int] = {level: i for i, level in enumerate(EDUCATION_LEVELS)}