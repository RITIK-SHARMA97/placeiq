import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import StudentCard from "./components/StudentCard";
import ScoreForm from "./pages/ScoreForm";
import BatchUpload from "./pages/BatchUpload";
import "./index.css";

export default function App() {
  const [view, setView] = useState("dashboard");
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(false);

  const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchPortfolio();
  }, []);

  async function fetchPortfolio() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/portfolio/summary`);
      const data = await res.json();
      setPortfolio(data);
    } catch (e) {
      console.error("Could not load portfolio", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      {/* Top navbar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="brand-logo">P</div>
          <span className="brand-name">PlaceIQ</span>
          <span className="brand-tagline">Placement Risk Intelligence</span>
        </div>
        <div className="navbar-links">
          {[
            { key: "dashboard", label: "Portfolio" },
            { key: "score",     label: "Score Student" },
            { key: "batch",     label: "Batch Upload" },
          ].map(({ key, label }) => (
            <button
              key={key}
              className={`nav-btn ${view === key ? "active" : ""}`}
              onClick={() => { setView(key); setSelectedStudent(null); }}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="navbar-meta">
          <span className="status-dot" />
          <span className="status-text">Live</span>
        </div>
      </nav>

      {/* Main content */}
      <main className="main-content">
        {selectedStudent ? (
          <StudentCard
            student={selectedStudent}
            onBack={() => setSelectedStudent(null)}
          />
        ) : view === "dashboard" ? (
          <Dashboard
            portfolio={portfolio}
            loading={loading}
            onRefresh={fetchPortfolio}
            onSelectStudent={setSelectedStudent}
          />
        ) : view === "score" ? (
          <ScoreForm
            apiUrl={API}
            onResult={setSelectedStudent}
          />
        ) : (
          <BatchUpload
            apiUrl={API}
            onSelectStudent={setSelectedStudent}
          />
        )}
      </main>
    </div>
  );
}
