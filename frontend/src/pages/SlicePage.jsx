// src/pages/SlicePage.jsx
import { useRef, useState } from "react";
import client from "../api/client";

function SlicePage() {
    const [job, setJob] = useState(null);
    const [resume, setResume] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [rankings, setRankings] = useState([]);
    const [error, setError] = useState("");
    const fileInput = useRef(null);

    const createJob = async () => {
        setError("");
        try {
            const res = await client.post("/jobs/", {
                title: "Mobile App Developer",
                description:
                    "We are seeking a Mobile App Devloper to build and maintain modern Android applications.",
                required_skills: ["Kotlin", "Android", "Jetpack Compose", "REST API", "Git"],
                min_years_experience: 1,
                min_education_level: "associate",
            });
            setJob(res.data);
        } catch {
            setError("Could not create job");
        }
    };

    const uploadResume = async () => {
        if (!job || !selectedFile) {
            setError("Create a job and choose a resume file first");
            return;
        }

        const extension = selectedFile.name.split(".").pop().toLowerCase();
        if (!["pdf", "docx"].includes(extension)) {
            setError("Choose a PDF or DOCX file");
            return;
        }
        if (selectedFile.size > 5 * 1024 * 1024) {
            setError("File is too large (maximum 5 MB)");
            return;
        }

        const formData = new FormData();
        formData.append("file", selectedFile);
        setError("");
        setUploading(true);
        try {
            const res = await client.post(`/jobs/${job.id}/resumes/`, formData);
            setResume(res.data);
            setSelectedFile(null);
            if (fileInput.current) fileInput.current.value = "";
        } catch (err) {
            setError(err.response?.data?.detail || err.message || "Upload failed");
        } finally {
            setUploading(false);
        }
    };


    const [loading, setLoading] = useState(false);


    // SlicePage.jsx
    const viewRankings = async () => {
        if (!job) return;
        setError("");
        setLoading(true);
        try {
            const res = await client.get(`/jobs/${job.id}/resumes/rankings`);  // was /jobs/${job.id}/rankings
            setRankings(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || "Could not load rankings");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto mt-10 space-y-6 p-4">
            <h1 className="text-2xl font-bold">Vertical Slice</h1>
            {error && <p className="text-red-600">{error}</p>}

            <div>
                <button onClick={createJob} className="bg-blue-600 text-white px-4 py-2 rounded">
                    1. Create Job
                </button>
                {job && <p className="mt-2 text-sm text-gray-700">Created: {job.title} (id {job.id})</p>}
            </div>

            <div>
                <label className="block mb-1 font-medium">2. Upload Resume</label>
                <input
                    ref={fileInput}
                    type="file"
                    id="resume-file"
                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={(e) => {
                        setSelectedFile(e.target.files[0] || null);
                        setError("");
                    }}
                    disabled={uploading}
                    className="sr-only"
                />
                <label
                    htmlFor="resume-file"
                    className={`inline-block cursor-pointer rounded bg-gray-200 px-4 py-2 text-gray-900 hover:bg-gray-300 ${
                        uploading ? "pointer-events-none opacity-50" : ""
                    }`}
                >
                    Choose PDF or DOCX
                </label>
                {selectedFile && (
                    <p className="mt-2 text-sm text-gray-700">
                        Selected: {selectedFile.name}
                    </p>
                )}
                <button
                    type="button"
                    onClick={uploadResume}
                    disabled={!job || !selectedFile || uploading}
                    className="mt-2 bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
                >
                    {uploading ? "Uploading..." : "Upload Resume"}
                </button>
                {resume && (
                    <div className="mt-2 text-sm text-gray-700">
                        <p>Uploaded: {resume.filename}</p>
                        <p>Status: {resume.status}</p>
                    </div>
                )}
            </div>

            <div>
                <button onClick={viewRankings} disabled={!job || loading} className="bg-green-600 text-white px-4 py-2 rounded">
                    {loading ? "Loading..." : "3. View Rankings"}
                </button>
                <ul className="mt-2 space-y-1">
                    {rankings.map((r) => (
                        <li key={r.resume_id} className="text-sm">
                            {r.candidate_name || r.filename} — score {r.overall_score}
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

export default SlicePage;