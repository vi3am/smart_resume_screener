import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import ScoringPanel from "../components/ScoringPanel";
import UploadPanel from "../components/UploadPanel";
import client from "../api/client";
import { getErrorMessage } from "../api/errorMessage";

const educationLabel = {
  high_school: "High school",
  associate: "Associate",
  bachelor: "Bachelor's",
  master: "Master's",
  phd: "PhD",
};

export default function JobResultsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");
  const [uploadVersion, setUploadVersion] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setJob(null);
    setError("");
    setNotFound(false);
    client.get(`/jobs/${jobId}`)
      .then(({ data }) => {
        if (active) setJob(data);
      })
      .catch((requestError) => {
        if (!active) return;
        setNotFound(requestError.response?.status === 404);
        setError(getErrorMessage(requestError, "Could not load this job."));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [jobId]);

  if (loading) {
    return <AppShell><div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-slate-600">Loading job...</div></AppShell>;
  }

  if (!job) {
    return (
      <AppShell>
        <section className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <h1 className="text-xl font-semibold text-slate-900">{notFound ? "Job not found" : "Could not load job"}</h1>
          <p className="mt-2 text-sm text-slate-600">{error || "This job is unavailable."}</p>
          <Link to="/" className="mt-5 inline-flex rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">Back to jobs</Link>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Link to={`/jobs/${jobId}`} className="mb-5 inline-flex text-sm font-medium text-emerald-800 hover:underline">← Back to job</Link>
      <header className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Job results</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{job.title}</h1>
        <p className="mt-4 text-sm text-slate-700">
          <span className="font-semibold">Required skills:</span>{" "}
          {job.required_skills?.length ? job.required_skills.join(", ") : "None"}
        </p>
        <dl className="mt-3 flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <div><dt className="inline font-semibold text-slate-800">Minimum experience: </dt><dd className="inline text-slate-700">{job.min_years_experience} years</dd></div>
          <div><dt className="inline font-semibold text-slate-800">Minimum education: </dt><dd className="inline text-slate-700">{educationLabel[job.min_education_level] || job.min_education_level}</dd></div>
        </dl>
      </header>

      <div className="space-y-6">
        <UploadPanel jobId={jobId} onUploadSuccess={() => setUploadVersion((version) => version + 1)} />
        <ScoringPanel jobId={jobId} uploadVersion={uploadVersion} />
      </div>
    </AppShell>
  );
}
