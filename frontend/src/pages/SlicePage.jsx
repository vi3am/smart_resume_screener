// src/pages/SlicePage.jsx
import { useState } from "react";
import client from "../api/client";

function SlicePage() {
    const [job, setJob] = useState(null);
    const [resume, setResume] = useState(null);
    const [rankings, setRankings] = useState([]);
    const [error, setError] = useState("");

    const createJob = async () => {
        setError("");
        try {
            const res = await client.post("/jobs/", {
                title: "Mobile App Developer",
                description:
                    "We are seeking a Mobile App Developer to build and maintain modern Android applications.",
                required_skills: ["Kotlin", "Android", "Jetpack Compose", "REST API", "Git"],
                min_years_experience: 1,
                min_education_level: "associate",
            });
            setJob(res.data);
        } catch {
            setError("Could not create job");
        }
    };

    const uploadResume = async (e) => {
        const file = e.target.files[0];
        if (!file || !job) return;
        const formData = new FormData();
        formData.append("file", file);
        setError("");
        try {
            const res = await client.post(`/jobs/${job.id}/resumes/`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            setResume(res.data);
        } catch {
            setError("Upload failed");
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
                <input type="file" onChange={uploadResume} disabled={!job} />
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