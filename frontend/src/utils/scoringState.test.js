import assert from "node:assert/strict";
import test from "node:test";

import {
  clearScoringStale,
  isScoringStale,
  markScoringStale,
} from "./scoringState.js";

test("scoring staleness persists per job until a successful rerun clears it", () => {
  const values = new Map();
  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  };

  try {
    assert.equal(isScoringStale(12), false);
    markScoringStale(12);
    assert.equal(isScoringStale(12), true);
    assert.equal(isScoringStale(13), false);
    clearScoringStale(12);
    assert.equal(isScoringStale(12), false);
  } finally {
    delete globalThis.localStorage;
  }
});
