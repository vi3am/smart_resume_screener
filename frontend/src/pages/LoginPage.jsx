// src/pages/LoginPage.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import client from "../api/client";

function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        try {
            const res = await client.post("/auth/login", { email, password });
            login(res.data.access_token);
            navigate("/");
        } catch {
            setError("Invalid email or password");
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-sm mx-auto mt-20 space-y-4">
            <h1 className="text-2xl font-bold">Smart Resume Screener</h1>
            {error && <p className="text-red-600">{error}</p>}
            <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border p-2 rounded"
                required
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border p-2 rounded"
                required
            />
            <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded">
                Log In
            </button>
        </form>
    );
}

export default LoginPage;