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
  return <JobResultsContent key={jobId} jobId={jobId} />;
}

function JobResultsContent({ jobId }) {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");
  const [uploadVersion, setUploadVersion] = useState(0);
  const [completedResumeCount, setCompletedResumeCount] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.all([
      client.get(`/jobs/${jobId}`),
      client.get(`/jobs/${jobId}/resumes/`),
    ])
      .then(([{ data: jobData }, { data: resumes }]) => {
        if (active) {
          setJob(jobData);
          setCompletedResumeCount(resumes.filter((resume) => resume.status === "done").length);
        }
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
    return <AppShell><div className="loading-card"><span className="spinner" />Loading job…</div></AppShell>;
  }

  if (!job) {
    return (
      <AppShell>
        <section className="empty-state compact">
          <h2>{notFound ? "Job not found" : "Could not load job"}</h2>
          <p>{error || "This job is unavailable."}</p>
          <Link to="/" className="button button-secondary">Back to jobs</Link>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <Link to={`/jobs/${jobId}`} className="back-link">← Back to role</Link>
      <header className="results-hero">
        <div className="results-hero-title"><span className="role-icon large">{job.title.slice(0, 1).toUpperCase()}</span><div><p className="eyebrow">CANDIDATE INTELLIGENCE</p><h1>{job.title}</h1><p>Review the latest match scores for this role.</p></div></div>
        <div className="results-hero-details"><div><span>MINIMUM EXPERIENCE</span><strong>{job.min_years_experience} years</strong></div><div><span>EDUCATION</span><strong>{educationLabel[job.min_education_level] || job.min_education_level}</strong></div><div><span>REQUIRED SKILLS</span><strong>{job.required_skills?.length || 0} skills</strong></div></div>
      </header>

      <div className="results-stack">
        <UploadPanel jobId={jobId} onUploadSuccess={() => setUploadVersion((version) => version + 1)} />
        <ScoringPanel
          jobId={jobId}
          uploadVersion={uploadVersion}
          completedResumeCount={completedResumeCount}
        />
      </div>
    </AppShell>
  );
}
