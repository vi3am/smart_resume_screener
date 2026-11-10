export function hasUnscoredResumes(run, completedResumeCount) {
  return Boolean(run && completedResumeCount > (run.results?.length ?? 0));
}
