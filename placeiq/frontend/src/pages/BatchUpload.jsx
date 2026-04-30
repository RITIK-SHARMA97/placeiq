import { useState, useRef } from "react";

const BAND_COLORS = {
  CRITICAL: "#EF4444", HIGH: "#F59E0B", MEDIUM: "#EAB308", LOW: "#22C55E"
};

export default function BatchUpload({ apiUrl, onSelectStudent }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [drag, setDrag]       = useState(false);
  const fileRef = useRef();

  async function handleFile(file) {
    if (!file || !file.name.endsWith(".csv")) {
      setError("Please upload a CSV file."); return;
    }
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${apiUrl}/upload-csv`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault(); setDrag(false);
    handleFile(e.dataTransfer.files[0]);
  }

  function downloadSample() {
    const header = "student_id,name,stream,institute,institute_tier,city,cgpa,num_internships,internship_quality,num_certifications,has_github,has_linkedin,job_portal_activity,backlogs\n";
    const rows = [
      "STU001,Rahul Sharma,B.Tech CS,PICT Pune,2,Pune,6.8,1,1,0,0,1,0.35,0",
      "STU002,Priya Patel,MBA Finance,Symbiosis Pune,2,Pune,7.5,2,2,1,1,1,0.60,0",
      "STU003,Arjun Singh,B.Tech ECE,NIT Trichy,1,Chennai,8.2,2,3,2,1,1,0.75,0",
      "STU004,Neha Kumar,BCA,Sunrise College,3,Patna,5.9,0,0,0,0,0,0.10,2",
      "STU005,Karan Gupta,B.Tech CS,Amity Noida,2,Delhi NCR,7.0,1,2,1,1,1,0.50,0",
    ].join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "placeiq_sample.csv"; a.click();
  }

  const students = result?.students || [];
  const summary  = result?.summary  || {};
  const dist     = summary.risk_distribution || {};

  return (
    <div className="batch-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Batch Upload</h1>
          <p className="page-sub">Upload a CSV to score entire cohorts at once</p>
        </div>
        <button className="btn-secondary" onClick={downloadSample}>
          ↓ Download Sample CSV
        </button>
      </div>

      {/* Drop zone */}
      <div
        className={`dropzone ${drag ? "drag-active" : ""} ${loading ? "loading" : ""}`}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" accept=".csv" style={{ display: "none" }}
          onChange={e => handleFile(e.target.files[0])} />
        {loading ? (
          <div className="dz-content">
            <div className="spinner" />
            <p>Scoring students…</p>
          </div>
        ) : (
          <div className="dz-content">
            <div className="dz-icon">📂</div>
            <p className="dz-title">Drop CSV file here or click to browse</p>
            <p className="dz-sub">Supports up to 200 students · CSV format</p>
          </div>
        )}
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {result && (
        <>
          {/* Summary cards */}
          <div className="batch-summary">
            <div className="batch-kpi">
              <div className="batch-kpi-val">{summary.total_students}</div>
              <div className="batch-kpi-label">Students Scored</div>
            </div>
            <div className="batch-kpi">
              <div className="batch-kpi-val" style={{ color: "#EF4444" }}>{summary.npa_risk_count}</div>
              <div className="batch-kpi-label">NPA Risk ({summary.npa_risk_pct}%)</div>
            </div>
            <div className="batch-kpi">
              <div className="batch-kpi-val">{summary.avg_risk_score}</div>
              <div className="batch-kpi-label">Avg Risk Score</div>
            </div>
            <div className="batch-kpi">
              <div className="batch-kpi-val"
                style={{ color: summary.avg_pmscore >= 0 ? "#22C55E" : "#EF4444" }}>
                {summary.avg_pmscore > 0 ? "+" : ""}{summary.avg_pmscore}
              </div>
              <div className="batch-kpi-label">Avg PMScore</div>
            </div>
          </div>

          {/* Risk distribution bar */}
          <div className="dist-bar-wrap">
            <div className="dist-bar">
              {["CRITICAL","HIGH","MEDIUM","LOW"].map(b => {
                const pct = summary.total_students
                  ? (dist[b] || 0) / summary.total_students * 100 : 0;
                return pct > 0 ? (
                  <div key={b}
                    className="dist-segment"
                    style={{ width: `${pct}%`, background: BAND_COLORS[b] }}
                    title={`${b}: ${dist[b]}`}
                  />
                ) : null;
              })}
            </div>
            <div className="dist-legend">
              {["CRITICAL","HIGH","MEDIUM","LOW"].map(b => (
                <span key={b} className="dist-legend-item">
                  <span className="dist-dot" style={{ background: BAND_COLORS[b] }} />
                  {b}: {dist[b] || 0}
                </span>
              ))}
            </div>
          </div>

          {/* Results table */}
          <div className="table-wrapper">
            <table className="student-table">
              <thead>
                <tr>
                  <th>Student</th><th>Stream</th><th>City</th>
                  <th>Risk Band</th><th>Risk Score</th>
                  <th>Placement 6mo</th><th>PMScore</th><th>Salary P50</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {students.map(s => (
                  <tr key={s.student_id} className="student-row"
                    onClick={() => onSelectStudent(s)}>
                    <td>
                      <div className="student-name">{s.name}</div>
                      <div className="student-id">{s.student_id}</div>
                    </td>
                    <td style={{ fontSize: 12 }}>{s.stream}</td>
                    <td style={{ fontSize: 12 }}>{s.city}</td>
                    <td>
                      <span className="risk-mini" style={{
                        background: BAND_COLORS[s.risk_band] + "22",
                        color: BAND_COLORS[s.risk_band],
                        border: `1px solid ${BAND_COLORS[s.risk_band]}44`,
                        padding: "2px 8px", borderRadius: 20, fontSize: 11, fontWeight: 600
                      }}>
                        {s.risk_band}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: BAND_COLORS[s.risk_band] }}>
                      {Math.round(s.risk_score)}
                    </td>
                    <td>{((s.placement_probability?.["6mo"] || 0) * 100).toFixed(0)}%</td>
                    <td style={{ color: (s.pmscore?.pmscore || 0) >= 0 ? "#22C55E" : "#EF4444", fontWeight: 600 }}>
                      {(s.pmscore?.pmscore || 0) > 0 ? "+" : ""}{s.pmscore?.pmscore || 0}
                    </td>
                    <td style={{ fontSize: 12 }}>{s.salary?.formatted?.p50 || "—"}</td>
                    <td>
                      <button className="view-btn"
                        onClick={e => { e.stopPropagation(); onSelectStudent(s); }}>
                        View →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
