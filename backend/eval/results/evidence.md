# Test evidence (generated)

Generated 2026-11-09T11:15:00+00:00 at commit 2465e66.

## 1. Parsing on varied layouts (20 anonymized CVs)

Names, emails and phones were redacted from these CVs, so this table covers experience, education and skills only.

| CV | chars | years | education | in progress | skills found |
|---|---|---|---|---|---|
| cv_01 | 1840 | 2.8 | master | - | 6 |
| cv_02 | 1570 | 5.8 | master | - | 0 |
| cv_03 | 2220 | 6.8 | - | - | 1 |
| cv_04 | 1369 | 7.1 | - | - | 9 |
| cv_05 | 1544 | 13.8 | bachelor | - | 2 |
| cv_06 | 1386 | 0.0 | master | - | 0 |
| cv_07 | 1480 | 1.8 | master | - | 10 |
| cv_08 | 1888 | 7.0 | master | - | 0 |
| cv_09 | 1467 | 12.8 | master | - | 2 |
| cv_10 | 1343 | 7.6 | - | - | 14 |
| cv_11 | 1468 | 0.0 | bachelor | - | 5 |
| cv_12 | 1530 | 4.0 | - | - | 1 |
| cv_13 | 1942 | 8.4 | bachelor | - | 2 |
| cv_14 | 773 | 3.0 | - | - | 5 |
| cv_15 | 1243 | 6.0 | bachelor | bachelor | 2 |
| cv_16 | 4482 | 3.8 | associate | bachelor | 21 |
| cv_17 | 1609 | 0.0 | master | - | 14 |
| cv_18 | 1295 | 4.0 | - | - | 0 |
| cv_19 | 5037 | 0.9 | high_school | associate | 41 |
| cv_20 | 1731 | 0.6 | high_school | bachelor | 11 |

Of 20 CVs: 3 with 0 years of experience found, 6 with no education level, 4 with no skills found. These are measured limitations (multi-column layouts, template placeholder dates, unrecognized headings).

## 2. Scoring consistency

Scored 5 CVs twice against dev posting p1 with a fixed reference date (2026-10-20).
Largest difference between the two runs, over the four components and the overall score: 0.000000

## 3. Automated API and failure-case tests

```
tests/test_auth_security.py::test_refresh_rotation_reuse_detection_and_logout_revocation
  /Users/macbook/develop/projects/smart-resume-screener/backend/.venv/lib/python3.14/site-packages/starlette/testclient.py:455: DeprecationWarning: Setting per-request cookies=<...> is being deprecated, because the expected behaviour on cookie persistence is ambiguous. Set cookies directly on the client instance instead.
    return super().request(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_resume_batch.py::test_batch_rejects_six_files - assert 200 ...
1 failed, 92 passed, 23 warnings in 10.00s
```
