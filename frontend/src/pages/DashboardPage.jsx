import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import client from "../api/client";

const initialJob = { title: "", description: "", skills: "", min_years_experience: 0, min_education_level: "high_school" };

function JobForm({ onCancel, onCreated }) {
  const [form, setForm] = useState(initialJob);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const change = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const response = await client.post("/jobs/", {
        title: form.title.trim(),
        description: form.description.trim(),
        required_skills: form.skills.split(",").map((skill) => skill.trim()).filter(Boolean),
        min_years_experience: Number(form.min_years_experience),
        min_education_level: form.min_education_level,
      });
      onCreated(response.data);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not create this role. Try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="panel job-form" onSubmit={submit}>
      <div className="panel-heading"><div><p className="eyebrow">NEW ROLE</p><h2>Set up a job posting</h2></div><button type="button" className="icon-button" aria-label="Close form" onClick={onCancel}>×</button></div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      <div className="form-grid">
        <label className="field-label field-span">Job title<input name="title" value={form.title} onChange={change} placeholder="e.g. Product Designer" required maxLength={160} /></label>
        <label className="field-label field-span">Job description<textarea name="description" value={form.description} onChange={change} placeholder="What will this person work on? Include the experience and skills that matter." rows={5} required /></label>
        <label className="field-label field-span">Required skills <span className="optional">comma separated</span><input name="skills" value={form.skills} onChange={change} placeholder="Figma, research, prototyping" /></label>
        <label className="field-label">Minimum experience <span className="optional">years</span><input name="min_years_experience" type="number" min="0" max="50" value={form.min_years_experience} onChange={change} /></label>
        <label className="field-label">Minimum education<select name="min_education_level" value={form.min_education_level} onChange={change}><option value="high_school">High school</option><option value="associate">Associate</option><option value="bachelor">Bachelor’s</option><option value="master">Master’s</option><option value="phd">PhD</option></select></label>
      </div>
      <div className="form-actions"><button type="button" className="button button-secondary" onClick={onCancel}>Cancel</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? "Creating…" : "Create role"}<span aria-hidden="true">→</span></button></div>
    </form>
  );
}

export default function DashboardPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    client.get("/jobs/")
      .then(({ data }) => { if (active) setJobs(data); })
      .catch((requestError) => {
        const detail = requestError.response?.data?.detail;
        if (active) setError(typeof detail === "string" ? detail : "Could not load your roles.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const addJob = (job) => {
    setJobs((current) => [job, ...current]);
    setShowForm(false);
    navigate(`/jobs/${job.id}`);
  };

  return (
    <AppShell>
      <section className="welcome-row">
        <div><p className="eyebrow">YOUR WORKSPACE</p><h1>Good hiring starts with a clear view.</h1><p className="page-lede">Manage open roles and review the candidates who fit.</p></div>
        <button className="button button-primary create-button" onClick={() => setShowForm((shown) => !shown)}><span className="plus">＋</span> Create a role</button>
      </section>
      {showForm && <JobForm onCancel={() => setShowForm(false)} onCreated={addJob} />}
      {error && <div className="alert alert-error" role="alert">{error}<button className="alert-retry" onClick={() => window.location.reload()}>Reload</button></div>}
      <section className="roles-section">
        <div className="section-heading"><div><h2>Open roles</h2><p>Your job postings and candidate pipelines</p></div><span className="count-pill">{jobs.length} {jobs.length === 1 ? "role" : "roles"}</span></div>
        {loading ? <div className="loading-card"><span className="spinner" />Loading your workspace…</div> : jobs.length === 0 ? (
          <div className="empty-state"><div className="empty-illustration"><span>▤</span><i>✦</i></div><h3>Your first shortlist starts with a role</h3><p>Create a job posting to upload resumes and compare candidates against what matters.</p><button className="button button-primary" onClick={() => setShowForm(true)}>Create your first role <span aria-hidden="true">→</span></button></div>
        ) : (
          <div className="role-grid">{jobs.map((job) => <Link className="role-card" to={`/jobs/${job.id}`} key={job.id}><div className="role-card-top"><span className="role-icon">{job.title.slice(0, 1).toUpperCase()}</span><span className="role-arrow" aria-hidden="true">↗</span></div><h3>{job.title}</h3><p className="role-description">{job.description}</p><div className="role-meta"><span><span className="meta-dot" />Active role</span><span>{job.required_skills?.length || 0} skills</span></div></Link>)}</div>
        )}
      </section>
      <section className="tip-banner"><div className="tip-mark">✳</div><div><strong>Make every requirement count.</strong><p>Add the skills and experience that matter to help organize your candidate review.</p></div></section>
    </AppShell>
  );
}
