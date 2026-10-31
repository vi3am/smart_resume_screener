import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../hooks/useAuth";

export default function AuthPage({ mode }) {
  const isRegister = mode === "register";
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/" replace />;

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = isRegister
        ? { email: form.email, password: form.password, full_name: form.full_name || null }
        : { email: form.email, password: form.password };
      const response = await client.post(isRegister ? "/auth/register" : "/auth/login", payload);
      login(response.data.access_token);
      navigate("/", { replace: true });
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : isRegister
        ? "Could not create your account. Check your details and try again."
        : "Email or password is incorrect.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <Link className="brand brand-light" to="/login"><span className="brand-mark">S</span> screener</Link>
        <div className="story-copy">
          <p className="eyebrow eyebrow-light">HIRING, WITH CLARITY</p>
          <h1>Find the signal in every resume.</h1>
          <p>Bring your roles and candidates together in one calm, focused workspace.</p>
          <div className="story-note"><span className="note-check">✓</span><span>Upload resumes and compare candidate matches side by side.</span></div>
        </div>
        <div className="story-footer">A clearer shortlist starts here.</div>
      </section>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><Link className="brand" to="/login"><span className="brand-mark">S</span> screener</Link></div>
        <div className="auth-form-wrap">
          <p className="eyebrow">YOUR RECRUITING WORKSPACE</p>
          <h2>{isRegister ? "Create your account" : "Welcome back"}</h2>
          <p className="auth-subtitle">{isRegister ? "Get started with your candidate workspace." : "Sign in to continue to your workspace."}</p>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <form className="form-stack" onSubmit={submit}>
            {isRegister && <label className="field-label">Full name <span className="optional">(optional)</span><input name="full_name" autoComplete="name" value={form.full_name} onChange={update} placeholder="Jordan Lee" /></label>}
            <label className="field-label">Work email<input name="email" type="email" autoComplete="email" value={form.email} onChange={update} placeholder="you@company.com" required /></label>
            <label className="field-label">Password<input name="password" type="password" autoComplete={isRegister ? "new-password" : "current-password"} minLength={isRegister ? 8 : undefined} value={form.password} onChange={update} placeholder={isRegister ? "At least 8 characters" : "Enter your password"} required /></label>
            <button className="button button-primary button-full" type="submit" disabled={loading}>{loading ? "Please wait…" : isRegister ? "Create account" : "Sign in"}<span aria-hidden="true">→</span></button>
          </form>
          <p className="auth-switch">{isRegister ? "Already have an account?" : "New to Screener?"} <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create an account"}</Link></p>
        </div>
        <p className="auth-legal">By continuing, you agree to use candidate information responsibly.</p>
      </section>
    </main>
  );
}
