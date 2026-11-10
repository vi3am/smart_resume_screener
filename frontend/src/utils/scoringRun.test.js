import assert from "node:assert/strict";
import test from "node:test";

import { hasUnscoredResumes } from "./scoringRun.js";

test("a run is stale when more completed resumes exist than it scored", () => {
  const run = { results: [{ resume_id: 1 }, { resume_id: 2 }] };

  assert.equal(hasUnscoredResumes(run, 3), true);
  assert.equal(hasUnscoredResumes(run, 2), false);
  assert.equal(hasUnscoredResumes(run, 1), false);
  assert.equal(hasUnscoredResumes(null, 3), false);
});
