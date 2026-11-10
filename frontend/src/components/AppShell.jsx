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
          <Link className="brand" to="/"><span className="brand-mark">S</span><span>Screener</span></Link>
          <nav className="top-nav" aria-label="Main navigation"><NavLink to="/" end className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}><span className="nav-symbol">▦</span> Workspace</NavLink></nav>
          <div className="topbar-actions"><span className="workspace-avatar">R</span><span className="workspace-label">Recruiter workspace</span><span className="topbar-divider" /><button className="button button-quiet signout-button" onClick={signOut}>Sign out <span aria-hidden="true">↗</span></button></div>
        </div>
      </header>
      <main className="page-content">{children}</main>
      <footer className="app-footer"><span>Screener</span><span>Thoughtful hiring starts with a clearer view.</span></footer>
    </div>
  );
}
