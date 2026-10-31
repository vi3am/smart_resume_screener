import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function AppShell({ children }) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const signOut = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link className="brand" to="/"><span className="brand-mark">S</span><span>screener</span></Link>
          <nav className="top-nav" aria-label="Main navigation"><NavLink to="/" end className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Workspace</NavLink></nav>
          <div className="topbar-actions"><span className="workspace-avatar">R</span><span className="workspace-label">Recruiter</span><button className="button button-quiet signout-button" onClick={signOut}>Sign out</button></div>
        </div>
      </header>
      <main className="page-content">{children}</main>
      <footer className="app-footer"><span> screener</span><span>Candidate review, made clearer.</span></footer>
    </div>
  );
}
