import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import client from "../api/client";
import { getErrorMessage } from "../api/errorMessage";
import { MAX_RESUME_UPLOAD_FILES } from "../utils/uploadLimits";
import { markScoringStale } from "../utils/scoringState";

const educationLabel = (value) => ({ high_school: "High school", associate: "Associate", bachelor: "Bachelor’s", master: "Master’s", phd: "PhD" }[value] || value || "Not detected");
const jobFormValues = (value) => ({
  title: value.title,
  description: value.description,
  required_skills: value.required_skills || [],
  min_years_experience: value.min_years_experience,
  min_education_level: value.min_education_level,
});

const educationSummary = (parsed) => {
  const completed = educationLabel(parsed.education_level);
  const inProgress = parsed.education_in_progress;
  if (!inProgress) return completed;
  const progressLabel = `${educationLabel(inProgress)} in progress`;
  return parsed.education_level ? `${completed} · ${progressLabel}` : progressLabel;
};

function ResumeCard({ resume }) {
  const parsed = resume.parsed_data || {};
  return (
    <article className="candidate-card">
      <div className="candidate-avatar">{(parsed.name || resume.filename || "?").slice(0, 1).toUpperCase()}</div>
      <div className="candidate-main">
        <div className="candidate-heading"><div><h3>{parsed.name || resume.filename}</h3><p>{resume.filename}</p></div></div>
        {(parsed.email || parsed.phone) && <div className="candidate-contact">{parsed.email && <span>✉ {parsed.email}</span>}{parsed.phone && <span>⌕ {parsed.phone}</span>}</div>}
        <div className="candidate-facts"><span>{parsed.years_experience != null ? `${parsed.years_experience} yrs experience` : "Experience not detected"}</span><span>{educationSummary(parsed)}</span></div>
        {Array.isArray(parsed.skills) && parsed.skills.length > 0 && <div className="skill-list">{parsed.skills.slice(0, 6).map((skill) => <span className="skill-chip" key={skill}>{skill}</span>)}{parsed.skills.length > 6 && <span className="skill-more">+{parsed.skills.length - 6}</span>}</div>}
        {resume.failure_reason && <p className="candidate-failure">{resume.failure_reason}</p>}
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
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState("");
  const [uploadResults, setUploadResults] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editingJob, setEditingJob] = useState(false);
  const [savingJob, setSavingJob] = useState(false);
  const [jobForm, setJobForm] = useState(null);
  const [resumeActionId, setResumeActionId] = useState(null);
  const [deletingJob, setDeletingJob] = useState(false);
  const navigate = useNavigate();

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
    setUploadResults([]);
    const accepted = [];
    const rejected = [];
    for (const file of files) {
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (!["pdf", "docx"].includes(extension)) rejected.push(`${file.name}: choose a PDF or DOCX file.`);
      else if (file.size > 5 * 1024 * 1024) rejected.push(`${file.name}: larger than the 5 MB limit.`);
      else accepted.push({ file, selected: true });
    }
    const known = new Set(selectedFiles.map(({ file }) => `${file.name}:${file.size}:${file.lastModified}`));
    const additions = accepted.filter(({ file }) => {
      const key = `${file.name}:${file.size}:${file.lastModified}`;
      if (known.has(key)) return false;
      known.add(key);
      return true;
    });
    const remainingSlots = MAX_RESUME_UPLOAD_FILES - selectedFiles.length;
    const additionsToQueue = additions.slice(0, remainingSlots);
    if (additions.length > remainingSlots) {
      rejected.push(`Choose no more than ${MAX_RESUME_UPLOAD_FILES} files at a time.`);
    }
    if (additionsToQueue.length) {
      setSelectedFiles((current) => [...current, ...additionsToQueue]);
    }
    setError(rejected.join(" "));
    event.target.value = "";
  };

  const uploadSelected = async () => {
    const filesToUpload = selectedFiles.filter(({ selected }) => selected).map(({ file }) => file);
    if (filesToUpload.length === 0) return;
    setError("");
    setNotice("");
    setUploading(true);
    setUploadProgress(`Uploading ${filesToUpload.length} file${filesToUpload.length === 1 ? "" : "s"}…`);
    const body = new FormData();
    filesToUpload.forEach((file) => body.append("files", file));
    try {
      const response = await client.post(`/jobs/${jobId}/resumes/batch`, body);
      const { done, failed, results } = response.data;
      setUploadResults(results);
      setSelectedFiles((current) => current.filter(({ file }) => !filesToUpload.includes(file)));
      if (done > 0) {
        markScoringStale(jobId);
        setNotice(`${done} resume${done === 1 ? " was" : "s were"} uploaded successfully${failed ? `; ${failed} failed` : ""}.`);
      }
      try {
        const resumeResponse = await client.get(`/jobs/${jobId}/resumes/`);
        setResumes(resumeResponse.data);
      } catch {
        setError("Uploads completed, but the resume list could not be refreshed.");
      }
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not upload the selected resumes.");
    } finally {
      setUploading(false);
      setUploadProgress("");
    }
  };

  const toggleFile = (file, selected) => setSelectedFiles((current) => current.map((item) => item.file === file ? { ...item, selected } : item));
  const allFilesSelected = selectedFiles.length > 0 && selectedFiles.every(({ selected }) => selected);

  const saveJob = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    setSavingJob(true);
    try {
      const { data } = await client.put(`/jobs/${jobId}`, {
        ...jobForm,
        title: jobForm.title.trim(),
        description: jobForm.description.trim(),
        required_skills: jobForm.required_skills.split(",").map((skill) => skill.trim()).filter(Boolean),
        min_years_experience: Number(jobForm.min_years_experience),
      });
      setJob(data);
      setEditingJob(false);
      markScoringStale(jobId);
      setNotice("Job requirements updated. Run scoring again to refresh the ranking.");
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not update this role."));
    } finally {
      setSavingJob(false);
    }
  };

  const reparseResume = async (resume) => {
    if (!window.confirm(`Reparse ${resume.filename}? The current ranking will need to be refreshed.`)) return;
    setError("");
    setNotice("");
    setResumeActionId(resume.id);
    try {
      const { data: reparsed } = await client.post(`/jobs/${jobId}/resumes/${resume.id}/reparse`);
      setResumes((current) => current.map((item) => item.id === resume.id ? reparsed : item));
      markScoringStale(jobId);
      setNotice(`${resume.filename} was reparsed. Run scoring again to refresh the ranking.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, `Could not reparse ${resume.filename}.`));
    } finally {
      setResumeActionId(null);
    }
  };

  const deleteResume = async (resume) => {
    if (!window.confirm(`Permanently delete ${resume.filename} and its extracted data?`)) return;
    setError("");
    setNotice("");
    setResumeActionId(resume.id);
    try {
      await client.delete(`/jobs/${jobId}/resumes/${resume.id}`);
      setResumes((current) => current.filter((item) => item.id !== resume.id));
      markScoringStale(jobId);
      setNotice(`${resume.filename} and its extracted data were deleted.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, `Could not delete ${resume.filename}.`));
    } finally {
      setResumeActionId(null);
    }
  };

  const deleteJob = async () => {
    if (!window.confirm(`Delete the job "${job.title}"? This action cannot be undone.`)) return;
    setError("");
    setDeletingJob(true);
    try {
      await client.delete(`/jobs/${jobId}`);
      localStorage.removeItem(`scoring-stale:${jobId}`);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Could not delete this job. Delete its resumes first."));
    } finally {
      setDeletingJob(false);
    }
  };

  if (loading) return <AppShell><div className="loading-card"><span className="spinner" />Loading role…</div></AppShell>;
  if (!job) return <AppShell><div className="empty-state compact"><h2>Role not found</h2><p>{error || "This job posting may have been removed."}</p><Link className="button button-secondary" to="/">Back to workspace</Link></div></AppShell>;

  const completed = resumes.filter((resume) => resume.status === "done").length;
  return (
    <AppShell>
      <Link to="/" className="back-link">← All roles</Link>
      <section className="job-hero">
        <div className="job-hero-content"><div className="job-title-line"><span className="role-icon large">{job.title.slice(0, 1).toUpperCase()}</span><div><p className="eyebrow">OPEN ROLE <span className="green-dot" /> ACTIVE</p><h1>{job.title}</h1></div><button
          type="button"
          className="button button-secondary job-edit-button"
          onClick={() => {
            setJobForm({ ...jobFormValues(job), required_skills: (job.required_skills || []).join(", ") });
            setEditingJob(true);
          }}
        >
          Edit role
        </button></div><p className="job-description">{job.description}</p><div className="job-requirements"><span>◷ {job.min_years_experience}+ years</span><span>⌂ {educationLabel(job.min_education_level)}</span>{job.required_skills?.length > 0 && <span>✳ {job.required_skills.length} required skills</span>}</div>{job.required_skills?.length > 0 && <div className="skill-list job-skills">{job.required_skills.map((skill) => <span className="skill-chip" key={skill}>{skill}</span>)}</div>}</div>
        <div className="job-stats"><div><strong>{resumes.length}</strong><span>Resumes</span></div><div><strong>{completed}</strong><span>Ready to review</span></div></div>
      </section>

      {editingJob && (
        <form className="panel job-form" onSubmit={saveJob}>
          <div className="panel-heading"><div><p className="eyebrow">EDIT ROLE</p><h2>Update job requirements</h2></div></div>
          <div className="form-grid">
            <label className="field-label field-span">Job title<input required maxLength={160} value={jobForm.title} onChange={(event) => setJobForm({ ...jobForm, title: event.target.value })} /></label>
            <label className="field-label field-span">Job description<textarea required rows={5} value={jobForm.description} onChange={(event) => setJobForm({ ...jobForm, description: event.target.value })} /></label>
            <label className="field-label field-span">Required skills <span className="optional">comma separated</span><input value={jobForm.required_skills} onChange={(event) => setJobForm({ ...jobForm, required_skills: event.target.value })} /></label>
            <label className="field-label">Minimum experience <span className="optional">years</span><input type="number" min="0" max="50" value={jobForm.min_years_experience} onChange={(event) => setJobForm({ ...jobForm, min_years_experience: event.target.value })} /></label>
            <label className="field-label">Minimum education<select value={jobForm.min_education_level} onChange={(event) => setJobForm({ ...jobForm, min_education_level: event.target.value })}><option value="high_school">High school</option><option value="associate">Associate</option><option value="bachelor">Bachelor’s</option><option value="master">Master’s</option><option value="phd">PhD</option></select></label>
          </div>
          <div className="form-actions"><button type="button" className="button button-secondary" onClick={() => setEditingJob(false)} disabled={savingJob}>Cancel</button><button type="submit" className="button button-primary" disabled={savingJob}>{savingJob ? "Saving…" : "Save role"}</button></div>
        </form>
      )}

      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {notice && <div className="alert alert-success" role="status">{notice}<button className="alert-close" aria-label="Dismiss message" onClick={() => setNotice("")}>×</button></div>}

      <section className="candidate-section">
        <div className="section-heading candidate-section-heading"><div><p className="eyebrow">CANDIDATE PIPELINE</p><h2>Resumes</h2><p>Upload CVs and see how they compare with this role.</p></div><div className="candidate-actions"><input ref={fileInput} className="visually-hidden" type="file" multiple accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={addFiles} disabled={uploading} /><button className="button button-secondary" onClick={() => fileInput.current?.click()} disabled={uploading}>＋ Choose resumes</button><button className="button button-primary" onClick={uploadSelected} disabled={uploading || !selectedFiles.some(({ selected }) => selected)}>{uploading ? <><span className="spinner small light-spinner" /> Uploading…</> : <>↑ Upload selected{selectedFiles.some(({ selected }) => selected) ? ` (${selectedFiles.filter(({ selected }) => selected).length})` : ""}</>}</button><Link className="button button-secondary" to={`/jobs/${jobId}/results`}>View ranking <span aria-hidden="true">→</span></Link><button type="button" className="button button-danger" onClick={deleteJob} disabled={deletingJob}>{deletingJob ? "Deleting…" : "Delete role"}</button></div></div>
        {selectedFiles.length > 0 && <div className="upload-queue" aria-label="Files selected for upload"><div className="upload-queue-heading"><strong>{selectedFiles.length} file{selectedFiles.length === 1 ? "" : "s"} ready</strong><label><input type="checkbox" checked={allFilesSelected} onChange={(event) => setSelectedFiles((current) => current.map((item) => ({ ...item, selected: event.target.checked })))} disabled={uploading} /> Select all</label></div>{selectedFiles.map(({ file, selected }) => <label className="upload-file-row" key={`${file.name}:${file.size}:${file.lastModified}`}><input type="checkbox" checked={selected} onChange={(event) => toggleFile(file, event.target.checked)} disabled={uploading} /><span className="upload-file-name">{file.name}</span><span className="upload-file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</span></label>)}{uploadProgress && <p className="upload-progress" role="status">{uploadProgress}</p>}</div>}
        {uploadResults.length > 0 && <ul className="upload-results" aria-label="Upload results">{uploadResults.map((result, index) => <li className={result.status === "failed" ? "upload-result upload-result-failed" : "upload-result"} key={`${result.filename}:${result.resume_id ?? index}`}><span className="upload-result-filename">{result.filename}</span><strong>{result.status}</strong><span>Failure reason: {result.failure_reason || "None"}</span></li>)}</ul>}
        <div className="ranking-note"><span>ⓘ</span><span>Matches compare resume text with the job description. Use them as a review aid alongside your requirements and judgment.</span></div>
        {resumes.length === 0 ? <div className="empty-state resume-empty"><div className="upload-illustration">↑</div><h3>No resumes yet</h3><p>Add PDF or DOCX resumes up to 5 MB. We’ll extract candidate details for your review.</p><button className="button button-primary" onClick={() => fileInput.current?.click()}>Choose resumes <span aria-hidden="true">→</span></button></div> : (
          <div className="candidate-list">{resumes.map((resume) => (
            <div className="candidate-card-wrap" key={resume.id}>
              <ResumeCard resume={resume} />
              <div className="candidate-card-actions">
                {resume.status === "done" && (
                  <button
                    type="button"
                    className="button button-secondary button-small"
                    onClick={() => reparseResume(resume)}
                    disabled={resumeActionId !== null}
                  >
                    {resumeActionId === resume.id ? "Working…" : "Reparse"}
                  </button>
                )}
                <button
                  type="button"
                  className="button button-danger button-small"
                  onClick={() => deleteResume(resume)}
                  disabled={resumeActionId !== null}
                >
                  {resumeActionId === resume.id ? "Working…" : "Delete"}
                </button>
              </div>
            </div>
          ))}</div>
        )}
      </section>
    </AppShell>
  );
}
