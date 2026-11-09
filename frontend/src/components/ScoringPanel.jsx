import { useEffect, useState } from "react";
import client from "../api/client";
import { getErrorMessage } from "../api/errorMessage";

function ScoreBar({ label, value }) {
  const score = Number(value) || 0;
  const width = Math.min(100, Math.max(0, score));

  return (
    <div className="min-w-24">
      <div className="mb-1 flex justify-between gap-2 text-xs text-slate-600">
        <span>{label}</span>
        <span>{score.toFixed(1)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-emerald-700" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function SkillChips({ skills, matched }) {
  if (!skills?.length) return <span className="text-sm text-slate-500">none</span>;

  return (
    <div className="flex min-w-32 flex-wrap gap-1">
      {skills.map((skill) => (
        <span
          key={skill}
          className={matched
            ? "rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-800"
            : "rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600"}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

export default function ScoringPanel({ jobId, uploadVersion }) {
  const [run, setRun] = useState(null);
  const [loadingRun, setLoadingRun] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [stale, setStale] = useState(false);

  useEffect(() => {
    let active = true;
    setLoadingRun(true);
    setError("");
    client.get(`/jobs/${jobId}/scoring-runs/latest`)
      .then(({ data }) => {
        if (active) setRun(data);
      })
      .catch((requestError) => {
        if (!active) return;
        if (requestError.response?.status === 404) {
          setRun(null);
          return;
        }
        setError(getErrorMessage(requestError, "Could not load the latest scoring run."));
      })
      .finally(() => {
        if (active) setLoadingRun(false);
      });

    return () => { active = false; };
  }, [jobId]);

  useEffect(() => {
    if (uploadVersion > 0) setStale(true);
  }, [uploadVersion]);

  const runScoring = async () => {
    setError("");
    setRunning(true);
    try {
      const { data } = await client.post(`/jobs/${jobId}/scoring-runs/`, undefined, { timeout: 120000 });
      setRun(data);
      setStale(false);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not run scoring."));
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Scoring results</h2>
          <p className="mt-1 text-sm text-slate-600">Compare each processed resume against this role.</p>
        </div>
        <button
          type="button"
          onClick={runScoring}
          disabled={loadingRun || running}
          className="rounded-md bg-emerald-800 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? "Scoring..." : run ? "Re-run scoring" : "Run scoring"}
        </button>
      </div>

      {loadingRun && <p className="mt-5 text-sm text-slate-600" role="status">Loading the latest scoring run...</p>}
      {running && (
        <p className="mt-5 text-sm text-slate-600" role="status">
          Scoring resumes now. The first run may take up to a minute while the model loads.
        </p>
      )}
      {error && <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-800" role="alert">{error}</p>}
      {stale && (
        <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-900" role="status">
          New resumes were uploaded. Run scoring again to include them.
        </p>
      )}

      {!loadingRun && !error && !run && (
        <p className="mt-5 rounded-md bg-slate-50 p-4 text-sm text-slate-600">
          No scoring run yet. Upload a resume, then run scoring to create a ranking.
        </p>
      )}

      {run && (
        <div className="mt-5">
          <dl className="grid gap-3 rounded-lg bg-slate-50 p-4 text-sm sm:grid-cols-3">
            <div><dt className="text-slate-500">Run ID</dt><dd className="font-medium text-slate-900">{run.id}</dd></div>
            <div><dt className="text-slate-500">Created</dt><dd className="font-medium text-slate-900">{new Date(run.created_at).toLocaleString()}</dd></div>
            <div>
              <dt className="text-slate-500">Weights used</dt>
              <dd className="mt-1 flex flex-wrap gap-x-3 gap-y-1 font-medium text-slate-900">
                {Object.entries(run.weights || {}).map(([name, value]) => (
                  <span key={name}>{name}: {value}</span>
                ))}
              </dd>
            </div>
          </dl>

          {run.results.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">This run has no candidate results.</p>
          ) : (
            <div className="mt-5 overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-[940px] w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
                  <tr>
                    <th scope="col" className="px-3 py-3">Rank</th>
                    <th scope="col" className="px-3 py-3">Candidate</th>
                    <th scope="col" className="px-3 py-3">Overall</th>
                    <th scope="col" className="px-3 py-3">Skills</th>
                    <th scope="col" className="px-3 py-3">Experience</th>
                    <th scope="col" className="px-3 py-3">Education</th>
                    <th scope="col" className="px-3 py-3">Semantic</th>
                    <th scope="col" className="px-3 py-3">Matched skills</th>
                    <th scope="col" className="px-3 py-3">Missing skills</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {run.results.map((result) => (
                    <tr key={result.resume_id} className="align-top">
                      <td className="px-3 py-4 font-semibold text-slate-900">{result.rank}</td>
                      <td className="max-w-56 px-3 py-4">
                        <div className="font-medium text-slate-900">{result.candidate_name || result.filename}</div>
                        <div className="mt-1 break-all text-xs text-slate-500">{result.filename}</div>
                      </td>
                      <td className="px-3 py-4 font-semibold text-slate-900">{Number(result.overall_score).toFixed(1)}</td>
                      <td className="px-3 py-4"><ScoreBar label="Skills" value={result.skills_score} /></td>
                      <td className="px-3 py-4"><ScoreBar label="Experience" value={result.experience_score} /></td>
                      <td className="px-3 py-4"><ScoreBar label="Education" value={result.education_score} /></td>
                      <td className="px-3 py-4"><ScoreBar label="Semantic" value={result.semantic_score} /></td>
                      <td className="px-3 py-4"><SkillChips skills={result.matched_skills} matched /></td>
                      <td className="px-3 py-4"><SkillChips skills={result.missing_skills} matched={false} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
