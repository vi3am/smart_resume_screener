import { useRef, useState } from "react";
import client from "../api/client";
import { getErrorMessage } from "../api/errorMessage";

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

    if (files.length > 5) {
      setSelectedFiles([]);
      setError("Choose no more than 5 files per selection. No files were uploaded.");
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
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-semibold text-slate-900">Upload resumes</h2>
      <p className="mt-1 text-sm text-slate-600">Choose up to 5 PDF or DOCX files, 5 MB each.</p>

      <label htmlFor="resume-files" className="mt-4 block text-sm font-medium text-slate-800">
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
        className="mt-2 block w-full rounded-md border border-slate-300 p-2 text-sm text-slate-700 file:mr-3 file:rounded file:border-0 file:bg-emerald-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-emerald-800"
      />

      {selectedFiles.length > 0 && (
        <p className="mt-2 text-sm text-slate-600" aria-live="polite">
          Selected: {selectedFiles.map((file) => file.name).join(", ")}
        </p>
      )}
      <button
        type="button"
        onClick={uploadFiles}
        disabled={busy || selectedFiles.length === 0}
        className="mt-4 rounded-md bg-emerald-800 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-900 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Uploading and parsing..." : "Upload selected files"}
      </button>

      {error && <p className="mt-3 text-sm text-red-700" role="alert">{error}</p>}
      {busy && (
        <p className="mt-3 text-sm text-slate-600" role="status">
          Uploading and parsing {selectedFiles.length} file{selectedFiles.length === 1 ? "" : "s"}...
        </p>
      )}
      {uploaded && (
        <p className="mt-3 text-sm text-emerald-800" role="status">
          Upload complete. Run scoring again to include the new resume.
        </p>
      )}

      {outcomes.length > 0 && (
        <ul className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
          {outcomes.map((outcome) => (
            <li key={outcome.key} className={`flex flex-wrap items-start justify-between gap-2 p-3 text-sm ${outcome.status === "failed" ? "text-red-700" : ""}`}>
              <span className="break-all">{outcome.filename}</span>
              <span className={outcome.status === "done" ? "font-medium text-emerald-700" : "font-medium text-red-700"}>
                {outcome.status}
              </span>
              <span className="w-full">Failure reason: {outcome.failure_reason || "None"}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
