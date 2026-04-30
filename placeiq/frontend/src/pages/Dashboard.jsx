import { useState, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from "recharts";

const BAND_COLORS = {
  CRITICAL: { bg: "#FEE2E2", text: "#991B1B", border: "#F87171", dot: "#EF4444" },
  HIGH:     { bg: "#FEF3C7", text: "#92400E", border: "#FBBF24", dot: "#F59E0B" },
  MEDIUM:   { bg: "#FEF9C3", text: "#854D0E", border: "#FDE68A", dot: "#EAB308" },
  LOW:      { bg: "#DCFCE7", text: "#14532D", border: "#86EFAC", dot: "#22C55E" },
};

const PIE_COLORS = ["#EF4444", "#F59E0B", "#EAB308", "#22C55E"];

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="stat-card" style={{ borderTop: `3px solid ${accent}` }}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function RiskBadge({ band }) {
  const c = BAND_COLORS[band] || BAND_COLORS.MEDIUM;
  return (
    <span className="risk-badge" style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}>
      <span className="risk-dot" style={{ background: c.dot }} />
      {band}
    </span>
  );
}

function PMScorePill({ pmscore }) {
  const isPos = pmscore.pmscore >= 0;
  return (
    <span className={`pm-pill ${isPos ? "pm-pos" : "pm-neg"}`}>
      {pmscore.trend_icon} {pmscore.pmscore > 0 ? "+" : ""}{pmscore.pmscore}
    </span>
  );
}

export default function Dashboard({ portfolio, loading, onRefresh, onSelectStudent }) {
  const [sortKey, setSortKey] = useState("risk_score");
  const [sortDir, setSortDir] = useState("asc");
  const [filterBand, setFilterBand] = useState("ALL");
  const [search, setSearch] = useState("");

  const students = portfolio?.students || [];
  const summary  = portfolio?.summary || {};

  const sorted = useMemo(() => {
    let list = [...students];
    if (filterBand !== "ALL") list = list.filter(s => s.risk_band === filterBand);
    if (search) list = list.filter(s =>
      s.name?.toLowerCase().includes(search.toLowerCase()) ||
      s.stream?.toLowerCase().includes(search.toLowerCase()) ||
      s.city?.toLowerCase().includes(search.toLowerCase())
    );
    list.sort((a, b) => {
      let av = a[sortKey], bv = b[sortKey];
      if (sortKey === "pmscore") { av = a.pmscore?.pmscore; bv = b.pmscore?.pmscore; }
      if (sortKey === "placement_6mo") { av = a.placement_probability?.["6mo"]; bv = b.placement_probability?.["6mo"]; }
      if (typeof av === "string") return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === "asc" ? av - bv : bv - av;
    });
    return list;
  }, [students, sortKey, sortDir, filterBand, search]);

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("asc"); }
  }

  const pieData = summary.risk_distribution
    ? Object.entries(summary.risk_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const barData = students.slice(0, 20).map(s => ({
    name: s.name?.split(" ")[0] || "—",
    risk: Math.round(s.risk_score),
    pm:   Math.round(s.pmscore?.pmscore || 0),
  }));

  if (loading) return (
    <div className="loading-screen">
      <div className="spinner" />
      <p>Loading portfolio...</p>
    </div>
  );

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Lender Portfolio</h1>
          <p className="page-sub">
            {summary.total_students || 0} students · AI-scored in real-time
          </p>
        </div>
        <button className="btn-primary" onClick={onRefresh}>↻ Refresh</button>
      </div>

      {/* KPI Row */}
      <div className="stats-row">
        <StatCard
          label="Avg Risk Score" value={summary.avg_risk_score || "—"}
          sub="out of 100" accent="#3B82F6"
        />
        <StatCard
          label="NPA Risk Students" value={summary.npa_risk_count || 0}
          sub={`${summary.npa_risk_pct || 0}% of portfolio`} accent="#EF4444"
        />
        <StatCard
          label="Critical Band" value={summary.risk_distribution?.CRITICAL || 0}
          sub="immediate action needed" accent="#DC2626"
        />
        <StatCard
          label="Avg PMScore" value={(summary.avg_pmscore > 0 ? "+" : "") + (summary.avg_pmscore || 0)}
          sub="trajectory index" accent="#10B981"
        />
        <StatCard
          label="Avg Salary P50"
          value={summary.avg_salary_p50 ? `₹${(summary.avg_salary_p50 / 100000).toFixed(1)}L` : "—"}
          sub="expected annual" accent="#8B5CF6"
        />
      </div>

      {/* Charts row */}
      <div className="charts-row">
        {/* Pie chart */}
        <div className="chart-card">
          <h3 className="chart-title">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={80}
                dataKey="value" label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                } labelLine={false}>
                {pieData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="legend-row">
            {["CRITICAL","HIGH","MEDIUM","LOW"].map((b,i) => (
              <div key={b} className="legend-item">
                <span className="legend-dot" style={{background: PIE_COLORS[i]}} />
                <span>{b}: {summary.risk_distribution?.[b] || 0}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar chart */}
        <div className="chart-card chart-wide">
          <h3 className="chart-title">Risk Scores — Top 20 (worst first)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData} margin={{ top: 5, right: 10, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="risk" name="Risk Score" radius={[4,4,0,0]}
                fill="#3B82F6"
                label={false}
              >
                {barData.map((entry, i) => (
                  <Cell key={i} fill={
                    entry.risk < 25 ? "#EF4444" :
                    entry.risk < 50 ? "#F59E0B" :
                    entry.risk < 75 ? "#EAB308" : "#22C55E"
                  } />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Table controls */}
      <div className="table-controls">
        <input
          className="search-input"
          placeholder="Search by name, stream, city..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="filter-tabs">
          {["ALL","CRITICAL","HIGH","MEDIUM","LOW"].map(b => (
            <button
              key={b}
              className={`filter-tab ${filterBand === b ? "active" : ""}`}
              onClick={() => setFilterBand(b)}
              style={filterBand === b && b !== "ALL" ? {
                background: BAND_COLORS[b]?.bg,
                color: BAND_COLORS[b]?.text,
                border: `1px solid ${BAND_COLORS[b]?.border}`
              } : {}}
            >
              {b}
              {b !== "ALL" && summary.risk_distribution?.[b] !== undefined &&
                <span className="filter-count">{summary.risk_distribution[b]}</span>
              }
            </button>
          ))}
        </div>
      </div>

      {/* Student table */}
      <div className="table-wrapper">
        <table className="student-table">
          <thead>
            <tr>
              {[
                { key: "name",          label: "Student" },
                { key: "stream",        label: "Program" },
                { key: "institute_tier",label: "Tier" },
                { key: "city",          label: "City" },
                { key: "risk_band",     label: "Risk Band" },
                { key: "risk_score",    label: "Risk Score" },
                { key: "placement_6mo", label: "Placement 6mo" },
                { key: "pmscore",       label: "PMScore" },
                { key: null,            label: "Action" },
              ].map(({ key, label }) => (
                <th key={label}
                  onClick={key ? () => handleSort(key) : undefined}
                  className={key ? "sortable" : ""}
                >
                  {label}
                  {sortKey === key && <span className="sort-arrow">{sortDir === "asc" ? " ↑" : " ↓"}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(s => (
              <tr key={s.student_id} className="student-row"
                onClick={() => onSelectStudent(s)}>
                <td>
                  <div className="student-name">{s.name}</div>
                  <div className="student-id">{s.student_id}</div>
                </td>
                <td>{s.stream}</td>
                <td>
                  <span className="tier-badge tier-{s.institute_tier}">
                    Tier {s.institute_tier}
                  </span>
                </td>
                <td>{s.city}</td>
                <td><RiskBadge band={s.risk_band} /></td>
                <td>
                  <div className="score-cell">
                    <div className="score-bar-bg">
                      <div className="score-bar-fill"
                        style={{
                          width: `${s.risk_score}%`,
                          background: s.risk_score >= 75 ? "#22C55E" :
                            s.risk_score >= 50 ? "#EAB308" :
                            s.risk_score >= 25 ? "#F59E0B" : "#EF4444"
                        }} />
                    </div>
                    <span className="score-num">{Math.round(s.risk_score)}</span>
                  </div>
                </td>
                <td>
                  <span className="prob-num">
                    {((s.placement_probability?.["6mo"] || 0) * 100).toFixed(0)}%
                  </span>
                </td>
                <td><PMScorePill pmscore={s.pmscore || { pmscore: 0, trend_icon: "➡️" }} /></td>
                <td>
                  <button className="view-btn" onClick={e => { e.stopPropagation(); onSelectStudent(s); }}>
                    View →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <div className="empty-state">No students match your filter.</div>
        )}
      </div>
    </div>
  );
}
