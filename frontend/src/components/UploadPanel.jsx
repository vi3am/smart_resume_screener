import { useRef, useState } from "react";
import client from "../api/client";
import { getErrorMessage } from "../api/errorMessage";
import { MAX_RESUME_UPLOAD_FILES } from "../utils/uploadLimits";
import { markScoringStale } from "../utils/scoringState";

export default function UploadPanel({ jobId, onUploadSuccess }) {
  const fileInput = useRef(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [outcomes, setOutcomes] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploaded, setUploaded] = useState(false);

  const selectFiles = (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    setError("");
    setUploaded(false);

    if (files.length > MAX_RESUME_UPLOAD_FILES) {
      setSelectedFiles([]);
      setError(`Choose no more than ${MAX_RESUME_UPLOAD_FILES} files per selection. No files were uploaded.`);
      return;
    }

    setSelectedFiles(files);
  };

  const uploadFiles = async () => {
    setBusy(true);
    setError("");
    setUploaded(false);
    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append("files", file));

    try {
      const { data } = await client.post(`/jobs/${jobId}/resumes/batch`, formData);
      setOutcomes(data.results.map((result, index) => ({ ...result, key: `${result.filename}:${index}` })));
      if (data.done > 0) {
        markScoringStale(jobId);
        onUploadSuccess();
        setUploaded(true);
      }
      setSelectedFiles([]);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Upload failed."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel upload-panel">
      <p className="eyebrow">BUILD YOUR SHORTLIST</p><h2>Upload resumes</h2>
      <p className="panel-lede">Choose up to {MAX_RESUME_UPLOAD_FILES} PDF or DOCX files, 5 MB each.</p>

      <label htmlFor="resume-files" className="field-label">
        Resume files
      </label>
      <input
        ref={fileInput}
        id="resume-files"
        type="file"
        multiple
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={selectFiles}
        disabled={busy}
        className="upload-input"
      />

      {selectedFiles.length > 0 && (
        <p className="selected-files" aria-live="polite">
          Selected: {selectedFiles.map((file) => file.name).join(", ")}
        </p>
      )}
      <button
        type="button"
        onClick={uploadFiles}
        disabled={busy || selectedFiles.length === 0}
        className="button button-primary"
      >
        {busy ? "Uploading and parsing..." : "Upload selected files"}
      </button>

      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {busy && (
        <p className="scoring-message" role="status">
          Uploading and parsing {selectedFiles.length} file{selectedFiles.length === 1 ? "" : "s"}...
        </p>
      )}
      {uploaded && (
        <p className="alert alert-success" role="status">
          Upload complete. Run scoring again to include the new resume.
        </p>
      )}

      {outcomes.length > 0 && (
        <ul className="upload-outcomes">
          {outcomes.map((outcome) => (
            <li key={outcome.key} className={outcome.status === "failed" ? "failed" : ""}>
              <span>{outcome.filename}</span>
              <strong className={outcome.status === "done" ? "ready" : "failed-status"}>
                {outcome.status}
              </strong>
              <small>Failure reason: {outcome.failure_reason || "None"}</small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
