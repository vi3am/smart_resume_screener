import assert from "node:assert/strict";
import test from "node:test";

import { filterScoredCandidates, shortlistToCsv } from "./candidateResults.js";

const candidates = [
  {
    resume_id: 1,
    rank: 1,
    candidate_name: "Alex Doe",
    filename: "alex.pdf",
    overall_score: 82,
    skills_score: 75,
    experience_score: 100,
    education_score: 50,
    semantic_score: 80,
    matched_skills: ["Python", "SQL"],
    missing_skills: ["Docker"],
  },
  {
    resume_id: 2,
    rank: 2,
    candidate_name: "Sam Lee",
    filename: "sam.csv",
    overall_score: 48,
    skills_score: 40,
    experience_score: 50,
    education_score: 50,
    semantic_score: 55,
    matched_skills: ["Excel"],
    missing_skills: [],
  },
];

test("candidate filters search names, filenames, and skills with a score floor", () => {
  assert.deepEqual(filterScoredCandidates(candidates, "python", "50"), [candidates[0]]);
  assert.deepEqual(filterScoredCandidates(candidates, "SAM", "0"), [candidates[1]]);
  assert.deepEqual(filterScoredCandidates(candidates, "", "75"), [candidates[0]]);
});

test("shortlist CSV contains only selected candidates and escapes CSV formulas", () => {
  const shortlisted = [{ ...candidates[0], candidate_name: "=IMPORTDATA()" }];
  const csv = shortlistToCsv(shortlisted);
  const rows = csv.split("\r\n");

  assert.equal(rows.length, 2);
  assert.match(rows[1], /"'=IMPORTDATA\(\)"/);
  assert.match(rows[1], /"Python; SQL"/);
  assert.doesNotMatch(csv, /Sam Lee/);
});
