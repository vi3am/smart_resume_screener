import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import client from "../api/client";

const educationLabel = (value) => ({ high_school: "High school", associate: "Associate", bachelor: "Bachelor’s", master: "Master’s", phd: "PhD" }[value] || value || "Not detected");

const educationSummary = (parsed) => {
  const completed = educationLabel(parsed.education_level);
  const inProgress = parsed.education_in_progress;
  if (!inProgress) return completed;
  const progressLabel = `${educationLabel(inProgress)} in progress`;
  return parsed.education_level ? `${completed} · ${progressLabel}` : progressLabel;
};

function ResumeCard({ resume, ranking }) {
  const parsed = resume.parsed_data || {};
  const score = ranking?.overall_score;
  return (
    <article className="candidate-card">
      <div className="candidate-avatar">{(parsed.name || resume.filename || "?").slice(0, 1).toUpperCase()}</div>
      <div className="candidate-main">
        <div className="candidate-heading"><div><h3>{parsed.name || resume.filename}</h3><p>{resume.filename}</p></div>{ranking && <div className="score-badge"><strong>{Number(score).toFixed(1)}%</strong><span>match</span></div>}</div>
        {(parsed.email || parsed.phone) && <div className="candidate-contact">{parsed.email && <span>✉ {parsed.email}</span>}{parsed.phone && <span>⌕ {parsed.phone}</span>}</div>}
        <div className="candidate-facts"><span>{parsed.years_experience != null ? `${parsed.years_experience} yrs experience` : "Experience not detected"}</span><span>{educationSummary(parsed)}</span></div>
        {Array.isArray(parsed.skills) && parsed.skills.length > 0 && <div className="skill-list">{parsed.skills.slice(0, 6).map((skill) => <span className="skill-chip" key={skill}>{skill}</span>)}{parsed.skills.length > 6 && <span className="skill-more">+{parsed.skills.length - 6}</span>}</div>}
        {ranking && <div className="score-track" aria-label={`Semantic match ${Number(score).toFixed(1)} percent`}><span style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div>}
      </div>
      <span className={`status-pill status-${resume.status}`}>{resume.status === "done" ? "Ready" : resume.status === "failed" ? "Needs attention" : "Processing"}</span>
    </article>
  );
}

export default function JobDetailPage() {
  const { jobId } = useParams();
  const fileInput = useRef(null);
  const [job, setJob] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [rankings, setRankings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([client.get(`/jobs/${jobId}`), client.get(`/jobs/${jobId}/resumes/`)])
      .then(([jobResponse, resumeResponse]) => {
        if (!active) return;
        setJob(jobResponse.data);
        setResumes(resumeResponse.data);
        setError("");
      })
      .catch((requestError) => {
        const detail = requestError.response?.data?.detail;
        if (active) setError(typeof detail === "string" ? detail : "Could not load this role.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [jobId]);

  const addFiles = (event) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;
    setError("");
    setNotice("");
    const accepted = [];
    const rejected = [];
    for (const file of files) {
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (!["pdf", "docx"].includes(extension)) rejected.push(`${file.name}: choose a PDF or DOCX file.`);
      else if (file.size > 5 * 1024 * 1024) rejected.push(`${file.name}: larger than the 5 MB limit.`);
      else accepted.push({ file, selected: true });
    }
    if (accepted.length) {
      setRankings(null);
      setSelectedFiles((current) => {
        const known = new Set(current.map(({ file }) => `${file.name}:${file.size}:${file.lastModified}`));
        const additions = accepted.filter(({ file }) => {
          const key = `${file.name}:${file.size}:${file.lastModified}`;
          if (known.has(key)) return false;
          known.add(key);
          return true;
        });
        return [...current, ...additions];
      });
    }
    setError(rejected.join(" "));
    event.target.value = "";
  };

  const uploadSelected = async () => {
    const filesToUpload = selectedFiles.filter(({ selected }) => selected).map(({ file }) => file);
    if (filesToUpload.length === 0) return;
    setError("");
    setNotice("");
    setRankings(null);
    setUploading(true);
    const succeeded = [];
    const failures = [];
    for (const [index, file] of filesToUpload.entries()) {
      setUploadProgress(`Uploading ${index + 1} of ${filesToUpload.length}: ${file.name}`);
      const body = new FormData();
      body.append("file", file);
      try {
        const response = await client.post(`/jobs/${jobId}/resumes/`, body);
        succeeded.push(file);
        setResumes((current) => [response.data, ...current.filter((resume) => resume.id !== response.data.id)]);
      } catch (requestError) {
        failures.push(`${file.name}: ${requestError.response?.data?.detail || "upload failed."}`);
      }
    }
    setSelectedFiles((current) => current.filter(({ file }) => !succeeded.includes(file)));
    setUploading(false);
    setUploadProgress("");
    if (succeeded.length) setNotice(`${succeeded.length} resume${succeeded.length === 1 ? " was" : "s were"} uploaded and parsed successfully.`);
    if (failures.length) setError(failures.join(" "));
  };

  const toggleFile = (file, selected) => setSelectedFiles((current) => current.map((item) => item.file === file ? { ...item, selected } : item));
  const allFilesSelected = selectedFiles.length > 0 && selectedFiles.every(({ selected }) => selected);

  const viewRankings = async () => {
    setError("");
    setRankingLoading(true);
    try {
      const response = await client.get(`/jobs/${jobId}/resumes/rankings`);
      setRankings(response.data);
      if (response.data.length === 0) setNotice("Upload a completed resume to see candidate matches.");
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not calculate candidate matches.");
    } finally {
      setRankingLoading(false);
    }
  };

  if (loading) return <AppShell><div className="loading-card"><span className="spinner" />Loading role…</div></AppShell>;
  if (!job) return <AppShell><div className="empty-state compact"><h2>Role not found</h2><p>{error || "This job posting may have been removed."}</p><Link className="button button-secondary" to="/">Back to workspace</Link></div></AppShell>;

  const completed = resumes.filter((resume) => resume.status === "done").length;
  const rankingById = new Map((rankings || []).map((item) => [item.resume_id, item]));

  return (
    <AppShell>
      <Link to="/" className="back-link">← All roles</Link>
      <section className="job-hero">
        <div className="job-hero-content"><div className="job-title-line"><span className="role-icon large">{job.title.slice(0, 1).toUpperCase()}</span><div><p className="eyebrow">OPEN ROLE <span className="green-dot" /> ACTIVE</p><h1>{job.title}</h1></div></div><p className="job-description">{job.description}</p><div className="job-requirements"><span>◷ {job.min_years_experience}+ years</span><span>⌂ {educationLabel(job.min_education_level)}</span>{job.required_skills?.length > 0 && <span>✳ {job.required_skills.length} required skills</span>}</div>{job.required_skills?.length > 0 && <div className="skill-list job-skills">{job.required_skills.map((skill) => <span className="skill-chip" key={skill}>{skill}</span>)}</div>}</div>
        <div className="job-stats"><div><strong>{resumes.length}</strong><span>Resumes</span></div><div><strong>{completed}</strong><span>Ready to review</span></div></div>
      </section>

      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {notice && <div className="alert alert-success" role="status">{notice}<button className="alert-close" aria-label="Dismiss message" onClick={() => setNotice("")}>×</button></div>}

      <section className="candidate-section">
        <div className="section-heading candidate-section-heading"><div><p className="eyebrow">CANDIDATE PIPELINE</p><h2>Resumes</h2><p>Upload CVs and see how they compare with this role.</p></div><div className="candidate-actions"><input ref={fileInput} className="visually-hidden" type="file" multiple accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={addFiles} disabled={uploading} /><button className="button button-secondary" onClick={() => fileInput.current?.click()} disabled={uploading}>＋ Choose resumes</button><button className="button button-primary" onClick={uploadSelected} disabled={uploading || !selectedFiles.some(({ selected }) => selected)}>{uploading ? <><span className="spinner small light-spinner" /> Uploading…</> : <>↑ Upload selected{selectedFiles.some(({ selected }) => selected) ? ` (${selectedFiles.filter(({ selected }) => selected).length})` : ""}</>}</button><button className="button button-secondary" onClick={viewRankings} disabled={rankingLoading || completed === 0}>{rankingLoading ? <><span className="spinner small" /> Matching…</> : <>✦ Rank candidates</>}</button></div></div>
        {selectedFiles.length > 0 && <div className="upload-queue" aria-label="Files selected for upload"><div className="upload-queue-heading"><strong>{selectedFiles.length} file{selectedFiles.length === 1 ? "" : "s"} ready</strong><label><input type="checkbox" checked={allFilesSelected} onChange={(event) => setSelectedFiles((current) => current.map((item) => ({ ...item, selected: event.target.checked })))} disabled={uploading} /> Select all</label></div>{selectedFiles.map(({ file, selected }) => <label className="upload-file-row" key={`${file.name}:${file.size}:${file.lastModified}`}><input type="checkbox" checked={selected} onChange={(event) => toggleFile(file, event.target.checked)} disabled={uploading} /><span className="upload-file-name">{file.name}</span><span className="upload-file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</span></label>)}{uploadProgress && <p className="upload-progress" role="status">{uploadProgress}</p>}</div>}
        <div className="ranking-note"><span>ⓘ</span><span>Matches compare resume text with the job description. Use them as a review aid alongside your requirements and judgment.</span></div>
        {resumes.length === 0 ? <div className="empty-state resume-empty"><div className="upload-illustration">↑</div><h3>No resumes yet</h3><p>Add PDF or DOCX resumes up to 5 MB. We’ll extract candidate details for your review.</p><button className="button button-primary" onClick={() => fileInput.current?.click()}>Choose resumes <span aria-hidden="true">→</span></button></div> : (
          <div className="candidate-list">{[...resumes].sort((a, b) => (rankingById.get(b.id)?.overall_score ?? -Infinity) - (rankingById.get(a.id)?.overall_score ?? -Infinity)).map((resume) => <ResumeCard key={resume.id} resume={resume} ranking={rankingById.get(resume.id)} />)}</div>
        )}
      </section>
    </AppShell>
  );
}
