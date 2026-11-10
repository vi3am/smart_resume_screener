const staleKey = (jobId) => `scoring-stale:${jobId}`;

export function markScoringStale(jobId) {
  localStorage.setItem(staleKey(jobId), "true");
}

export function isScoringStale(jobId) {
  return localStorage.getItem(staleKey(jobId)) === "true";
}

export function clearScoringStale(jobId) {
  localStorage.removeItem(staleKey(jobId));
}
