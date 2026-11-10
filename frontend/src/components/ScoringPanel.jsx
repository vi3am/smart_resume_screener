import { useEffect, useState } from "react";
import client from "../api/client";
import { getErrorMessage } from "../api/errorMessage";
import { filterScoredCandidates, shortlistToCsv } from "../utils/candidateResults";
import { hasUnscoredResumes } from "../utils/scoringRun";
import { clearScoringStale, isScoringStale } from "../utils/scoringState";

function ScoreBar({ label, value }) {
  const score = Number(value) || 0;
  const width = Math.min(100, Math.max(0, score));

  return (
    <div className="score-cell">
      <div className="score-label">
        <span>{label}</span>
        <span>{score.toFixed(1)}</span>
      </div>
      <div className="score-track">
        <div style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function SkillChips({ skills, matched }) {
  if (!skills?.length) return <span className="none-label">None</span>;

  return (
    <div className="result-skills">
      {skills.map((skill) => (
        <span
          key={skill}
          className={matched ? "result-skill matched" : "result-skill missing"}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

export default function ScoringPanel({ jobId, uploadVersion, completedResumeCount }) {
  const [run, setRun] = useState(null);
  const [loadingRun, setLoadingRun] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [runNotice, setRunNotice] = useState("");
  const [scoringStale, setScoringStale] = useState(() => isScoringStale(jobId));
  const [scoredUploadVersion, setScoredUploadVersion] = useState(uploadVersion);
  const [search, setSearch] = useState("");
  const [minimumScore, setMinimumScore] = useState("0");
  const [selectedResumeIds, setSelectedResumeIds] = useState(() => new Set());
  const stale = scoringStale || uploadVersion > scoredUploadVersion || hasUnscoredResumes(run, completedResumeCount);

  useEffect(() => {
    let active = true;
    client.get(`/jobs/${jobId}/scoring-runs/latest`)
      .then(({ data }) => {
        if (active) setRun(data);
      })
      .catch((requestError) => {
        if (!active) return;
        if (requestError.response?.status === 404) {
          setRun(null);
          const detail = requestError.response.data?.detail;
          setRunNotice(
            detail === "Job requirements changed. Run scoring again." ? detail : "",
          );
          return;
        }
        setError(getErrorMessage(requestError, "Could not load the latest scoring run."));
      })
      .finally(() => {
        if (active) setLoadingRun(false);
      });

    return () => { active = false; };
  }, [jobId]);

  const runScoring = async () => {
    setError("");
    setRunNotice("");
    setRunning(true);
    try {
      const { data } = await client.post(`/jobs/${jobId}/scoring-runs/`, undefined, { timeout: 120000 });
      setRun(data);
      setScoredUploadVersion(uploadVersion);
      clearScoringStale(jobId);
      setScoringStale(false);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not run scoring."));
    } finally {
      setRunning(false);
    }
  };

  const visibleResults = filterScoredCandidates(run?.results || [], search, minimumScore);
  const shortlist = (run?.results || []).filter((result) => selectedResumeIds.has(result.resume_id));

  const toggleShortlist = (resumeId, checked) => {
    setSelectedResumeIds((current) => {
      const next = new Set(current);
      if (checked) next.add(resumeId);
      else next.delete(resumeId);
      return next;
    });
  };

  const exportShortlist = () => {
    const blob = new Blob(["\uFEFF", shortlistToCsv(shortlist)], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `job-${jobId}-shortlist.csv`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <section className="panel scoring-panel">
      <div className="scoring-heading">
        <div>
          <p className="eyebrow">MATCH ANALYSIS</p><h2>Scoring results</h2>
          <p>Compare each processed resume against this role.</p>
        </div>
        <button
          type="button"
          onClick={runScoring}
          disabled={loadingRun || running}
          className="button button-primary"
        >
          {running ? "Scoring..." : run ? "Re-run scoring" : "Run scoring"}
        </button>
      </div>

      {loadingRun && <p className="scoring-message" role="status">Loading the latest scoring run…</p>}
      {running && (
        <p className="scoring-message" role="status">
          Scoring resumes now. The first run may take up to a minute while the model loads.
        </p>
      )}
      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {runNotice && <p className="alert alert-warning" role="status">{runNotice}</p>}
      {stale && (
        <p className="alert alert-warning" role="status">
          Candidate data changed. Run scoring again to refresh the ranking.
        </p>
      )}

      {!loadingRun && !error && !run && (
        <p className="scoring-empty">
          No scoring run yet. Upload a resume, then run scoring to create a ranking.
        </p>
      )}

      {run && (
        <div className="mt-5">
          <dl className="run-metadata">
            <div><dt>Run ID</dt><dd>{run.id}</dd></div>
            <div><dt>Created</dt><dd>{new Date(run.created_at).toLocaleString()}</dd></div>
            <div>
              <dt>Weights used</dt>
              <dd className="run-weights">
                {Object.entries(run.weights || {}).map(([name, value]) => (
                  <span key={name}>{name}: {value}</span>
                ))}
              </dd>
            </div>
          </dl>

          {run.results.length === 0 ? (
            <p className="scoring-empty">This run has no candidate results.</p>
          ) : (
            <>
              <div className="candidate-filters">
                <label>
                  Search candidates
                  <input
                    type="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Name, filename, or skill"
                  />
                </label>
                <label>
                  Minimum match score
                  <select value={minimumScore} onChange={(event) => setMinimumScore(event.target.value)}>
                    <option value="0">Any score</option>
                    <option value="50">50 and above</option>
                    <option value="75">75 and above</option>
                  </select>
                </label>
                <div className="shortlist-actions">
                  <span>{shortlist.length} shortlisted</span>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={exportShortlist}
                    disabled={shortlist.length === 0}
                  >
                    Export shortlist CSV
                  </button>
                </div>
              </div>
              {visibleResults.length === 0 ? (
                <p className="scoring-empty">No candidates match these filters.</p>
              ) : (
                <div className="results-table-wrap">
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th scope="col">Shortlist</th>
                        <th scope="col">Rank</th>
                        <th scope="col">Candidate</th>
                        <th scope="col">Overall</th>
                        <th scope="col">Skills</th>
                        <th scope="col">Experience</th>
                        <th scope="col">Education</th>
                        <th scope="col">Semantic</th>
                        <th scope="col">Matched skills</th>
                        <th scope="col">Missing skills</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleResults.map((result) => (
                        <tr key={result.resume_id}>
                          <td>
                            <input
                              type="checkbox"
                              aria-label={`Add ${result.candidate_name || result.filename} to shortlist`}
                              checked={selectedResumeIds.has(result.resume_id)}
                              onChange={(event) => toggleShortlist(result.resume_id, event.target.checked)}
                            />
                          </td>
                          <td><span className="rank-number">{result.rank}</span></td>
                          <td className="result-candidate">
                            <div>{result.candidate_name || result.filename}</div>
                            <span>{result.filename}</span>
                          </td>
                          <td><strong className="overall-score">{Number(result.overall_score).toFixed(1)}<small>/100</small></strong></td>
                          <td><ScoreBar label="Skills" value={result.skills_score} /></td>
                          <td><ScoreBar label="Experience" value={result.experience_score} /></td>
                          <td><ScoreBar label="Education" value={result.education_score} /></td>
                          <td><ScoreBar label="Semantic" value={result.semantic_score} /></td>
                          <td><SkillChips skills={result.matched_skills} matched /></td>
                          <td><SkillChips skills={result.missing_skills} matched={false} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}
