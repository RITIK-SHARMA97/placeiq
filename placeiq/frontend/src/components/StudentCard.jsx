import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Cell, Tooltip
} from "recharts";

const BAND_META = {
  CRITICAL: { color: "#DC2626", bg: "#FEF2F2", icon: "⚫", label: "Critical Risk" },
  HIGH:     { color: "#D97706", bg: "#FFFBEB", icon: "🔴", label: "High Risk" },
  MEDIUM:   { color: "#CA8A04", bg: "#FEFCE8", icon: "🟡", label: "Medium Risk" },
  LOW:      { color: "#16A34A", bg: "#F0FDF4", icon: "🟢", label: "Low Risk" },
};

const ALERT_META = {
  info:     { bg: "#EFF6FF", border: "#3B82F6", text: "#1D4ED8", icon: "ℹ️" },
  warning:  { bg: "#FFFBEB", border: "#F59E0B", text: "#92400E", icon: "⚠️" },
  high:     { bg: "#FFF7ED", border: "#EA580C", text: "#9A3412", icon: "🔔" },
  critical: { bg: "#FEF2F2", border: "#DC2626", text: "#991B1B", icon: "🚨" },
};

function ProbBar({ label, prob, color }) {
  const pct = Math.round(prob * 100);
  return (
    <div className="prob-row">
      <span className="prob-label">{label}</span>
      <div className="prob-track">
        <div className="prob-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="prob-pct" style={{ color }}>{pct}%</span>
      <span className="prob-note">
        {pct >= 75 ? "High confidence" : pct >= 45 ? "Moderate" : "Unlikely without action"}
      </span>
    </div>
  );
}

function ShapBar({ driver }) {
  const isRisk = driver.direction === "risk";
  const barW = Math.min(driver.abs_shap * 600, 180);
  return (
    <div className="shap-row">
      <div className="shap-bar-wrap">
        <div className="shap-bar"
          style={{
            width: barW,
            background: isRisk ? "#EF4444" : "#22C55E",
            opacity: 0.7
          }} />
        <span className="shap-label">{driver.label}</span>
      </div>
      <span className={`shap-val ${isRisk ? "shap-neg" : "shap-pos"}`}>
        {isRisk ? "▼" : "▲"} {driver.abs_shap.toFixed(3)}
      </span>
    </div>
  );
}

export default function StudentCard({ student, onBack }) {
  if (!student) return null;
  const band = BAND_META[student.risk_band] || BAND_META.MEDIUM;
  const alert = ALERT_META[student.recommended_actions?.alert_level || "info"];
  const probs = student.placement_probability || {};
  const pm    = student.pmscore || { pmscore: 0, trend: "Stable", trend_icon: "➡️" };
  const sal   = student.salary || {};
  const drivers = student.shap_drivers || [];
  const actions = student.recommended_actions || {};

  // Radar chart data
  const radarData = [
    { axis: "CGPA",       val: Math.min(100, (student.cgpa || 6) / 10 * 100) },
    { axis: "Internship", val: (student.internship_quality || 0) / 4 * 100 },
    { axis: "Skills",     val: Math.min(100, (student.num_certifications || 0) * 20) },
    { axis: "Market",     val: Math.min(100, ((student.city_labor_demand || 1.0) - 0.5) / 1.3 * 100) },
    { axis: "Portal",     val: Math.round((student.job_portal_activity || 0.3) * 100) },
    { axis: "Placement",  val: Math.round((probs["6mo"] || 0) * 100) },
  ];

  return (
    <div className="card-page">
      {/* Back button */}
      <button className="back-btn" onClick={onBack}>← Back to Portfolio</button>

      {/* Card header */}
      <div className="sc-header" style={{ borderLeft: `5px solid ${band.color}` }}>
        <div className="sc-header-left">
          <div className="sc-avatar" style={{ background: band.bg, color: band.color }}>
            {(student.name || "S").charAt(0)}
          </div>
          <div>
            <h2 className="sc-name">{student.name}</h2>
            <p className="sc-meta">
              {student.stream} · {student.institute} · {student.city} · Final Year 2025
            </p>
          </div>
        </div>
        <div className="sc-header-right">
          <div className="risk-badge-large" style={{ background: band.bg, color: band.color }}>
            {band.icon} {band.label}
          </div>
          <div className="sc-score-pair">
            <div>
              <span className="sc-score-num" style={{ color: band.color }}>
                {Math.round(student.risk_score || 0)}
              </span>
              <span className="sc-score-denom">/100</span>
            </div>
            <div className="sc-score-label">Risk Score</div>
          </div>
          <div className="sc-pm-block">
            <span className={`pm-large ${pm.pmscore >= 0 ? "pm-pos" : "pm-neg"}`}>
              {pm.trend_icon} {pm.pmscore > 0 ? "+" : ""}{pm.pmscore}
            </span>
            <div className="pm-trend-label">PMScore · {pm.trend}</div>
          </div>
        </div>
      </div>

      {/* Placement probabilities */}
      <div className="sc-section">
        <h3 className="sc-section-title">Placement Probabilities</h3>
        <ProbBar label="3 months"  prob={probs["3mo"]  || 0} color="#EF4444" />
        <ProbBar label="6 months"  prob={probs["6mo"]  || 0} color="#F59E0B" />
        <ProbBar label="12 months" prob={probs["12mo"] || 0} color="#22C55E" />
      </div>

      {/* Middle row: SHAP + Salary + Radar */}
      <div className="sc-mid-row">

        {/* SHAP explainability */}
        <div className="sc-panel">
          <h3 className="sc-section-title">Top Risk Drivers (SHAP)</h3>
          <p className="sc-panel-sub">Factors most influencing this student's score</p>
          {drivers.map((d, i) => <ShapBar key={i} driver={d} />)}
          <div className="shap-legend">
            <span className="shap-legend-item risk">▼ Risk factor</span>
            <span className="shap-legend-item pos">▲ Positive factor</span>
          </div>
        </div>

        {/* Salary forecast */}
        <div className="sc-panel">
          <h3 className="sc-section-title">Salary Forecast</h3>
          <p className="sc-panel-sub">Expected annual package on placement</p>
          <div className="salary-band">
            <div className="salary-p">
              <div className="salary-label">P25</div>
              <div className="salary-val">{sal.formatted?.p25 || "—"}</div>
            </div>
            <div className="salary-center">
              <div className="salary-p50-label">Median</div>
              <div className="salary-p50">{sal.formatted?.p50 || "—"}</div>
            </div>
            <div className="salary-p">
              <div className="salary-label">P75</div>
              <div className="salary-val">{sal.formatted?.p75 || "—"}</div>
            </div>
          </div>
          {/* Visual band */}
          <div className="salary-visual">
            <div className="salary-track">
              <div className="salary-fill" style={{ left: "0%", width: "100%", background: "#DBEAFE" }} />
              <div className="salary-fill salary-p50-marker" style={{
                left: "50%", width: "3px", background: "#3B82F6"
              }} />
            </div>
            <div className="salary-axis">
              <span>{sal.formatted?.p25}</span>
              <span style={{ color: "#3B82F6", fontWeight: 600 }}>
                ● {sal.formatted?.p50}
              </span>
              <span>{sal.formatted?.p75}</span>
            </div>
          </div>

          {/* PMScore trajectory */}
          <div className="pm-trajectory">
            <h4 className="pm-traj-title">PMScore Trajectory</h4>
            <div className="pm-traj-row">
              <div className={`pm-step ${pm.pmscore > 2 ? "pm-step-pos" : "pm-step-neg"}`}>
                Sem −2<br />
                <strong>{student.cgpa_sem_prev2?.toFixed?.(1) || "6.3"}</strong>
              </div>
              <div className="pm-arrow">→</div>
              <div className={`pm-step ${pm.pmscore > 2 ? "pm-step-pos" : "pm-step-neg"}`}>
                Sem −1<br />
                <strong>{student.cgpa_sem_prev1?.toFixed?.(1) || "6.5"}</strong>
              </div>
              <div className="pm-arrow">→</div>
              <div className="pm-step pm-step-now">
                Now<br />
                <strong>{student.cgpa?.toFixed?.(1) || "6.8"}</strong>
              </div>
            </div>
            <div className={`pm-score-final ${pm.pmscore >= 0 ? "pm-pos" : "pm-neg"}`}>
              PMScore: {pm.pmscore > 0 ? "+" : ""}{pm.pmscore} · {pm.trend}
            </div>
          </div>
        </div>

        {/* Radar chart */}
        <div className="sc-panel">
          <h3 className="sc-section-title">Employability Radar</h3>
          <p className="sc-panel-sub">Multi-dimensional profile overview</p>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11 }} />
              <Radar name="Student" dataKey="val"
                stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.25}
                strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Action engine */}
      <div className="sc-section">
        <h3 className="sc-section-title">Action Engine</h3>
        <div className="action-row">
          {/* Student actions */}
          <div className="action-panel student-actions">
            <h4 className="action-panel-title">📚 Student Actions</h4>
            <ul className="action-list">
              {(actions.student_actions || []).map((a, i) => (
                <li key={i} className="action-item student">{a}</li>
              ))}
            </ul>
          </div>
          {/* Lender actions */}
          <div className="action-panel lender-actions"
            style={{ background: alert.bg, border: `1px solid ${alert.border}` }}>
            <h4 className="action-panel-title" style={{ color: alert.text }}>
              {alert.icon} Lender Alert
            </h4>
            <ul className="action-list">
              {(actions.lender_actions || []).map((a, i) => (
                <li key={i} className="action-item lender" style={{ color: alert.text }}>{a}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Raw data */}
      <details className="raw-data">
        <summary>View Raw Score Data (JSON)</summary>
        <pre>{JSON.stringify(student, null, 2)}</pre>
      </details>
    </div>
  );
}
