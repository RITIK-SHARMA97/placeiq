import { useState } from "react";

const STREAMS = ["B.Tech CS","B.Tech ECE","B.Tech Mech","MBA Finance",
                 "MBA Marketing","BBA","B.Pharm","B.Sc Nursing","LLB","BCA"];
const CITIES  = ["Bangalore","Hyderabad","Pune","Mumbai","Delhi NCR",
                 "Chennai","Kolkata","Jaipur","Bhopal","Patna","Lucknow","Nagpur"];
const INTERNSHIP_LABELS = [
  "0 — None",
  "1 — Low depth (local/unrelated)",
  "2 — Moderate (SME/relevant)",
  "3 — Strong (MNC/core domain)",
  "4 — Excellent (FAANG/Top MNC)",
];

function Field({ label, children, hint }) {
  return (
    <div className="form-field">
      <label className="form-label">{label}</label>
      {children}
      {hint && <span className="form-hint">{hint}</span>}
    </div>
  );
}

export default function ScoreForm({ apiUrl, onResult }) {
  const [form, setForm] = useState({
    student_id: "DEMO001",
    name: "",
    stream: "B.Tech CS",
    institute: "",
    institute_tier: 2,
    city: "Pune",
    cgpa: "",
    cgpa_sem_prev1: "",
    cgpa_sem_prev2: "",
    backlogs: 0,
    sem_gap_years: 0,
    num_internships: 0,
    internship_quality: 0,
    num_certifications: 0,
    has_github: false,
    has_linkedin: false,
    job_portal_activity: 0.35,
    sector_growth_index: 1.0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        cgpa:              parseFloat(form.cgpa) || 6.5,
        cgpa_sem_prev1:    form.cgpa_sem_prev1 ? parseFloat(form.cgpa_sem_prev1) : null,
        cgpa_sem_prev2:    form.cgpa_sem_prev2 ? parseFloat(form.cgpa_sem_prev2) : null,
        backlogs:          parseInt(form.backlogs) || 0,
        sem_gap_years:     parseInt(form.sem_gap_years) || 0,
        num_internships:   parseInt(form.num_internships) || 0,
        internship_quality:parseInt(form.internship_quality) || 0,
        num_certifications:parseInt(form.num_certifications) || 0,
        job_portal_activity:parseFloat(form.job_portal_activity) || 0.3,
        institute_tier:    parseInt(form.institute_tier) || 2,
      };
      const res = await fetch(`${apiUrl}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      onResult(data);
    } catch (err) {
      setError(err.message || "Scoring failed. Is the API running?");
    } finally {
      setLoading(false);
    }
  }

  function loadDemo() {
    setForm({
      student_id: "STU0001",
      name: "Rahul Sharma",
      stream: "B.Tech CS",
      institute: "PICT Pune",
      institute_tier: 2,
      city: "Pune",
      cgpa: "6.8",
      cgpa_sem_prev1: "6.5",
      cgpa_sem_prev2: "6.3",
      backlogs: 0,
      sem_gap_years: 0,
      num_internships: 1,
      internship_quality: 1,
      num_certifications: 0,
      has_github: false,
      has_linkedin: true,
      job_portal_activity: 0.35,
      sector_growth_index: 0.95,
    });
  }

  return (
    <div className="form-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Score a Student</h1>
          <p className="page-sub">Enter student profile → instant PlaceIQ risk card</p>
        </div>
        <button className="btn-secondary" onClick={loadDemo}>Load Demo Profile</button>
      </div>

      <form className="score-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <h3 className="form-section-title">Student Identity</h3>
          <div className="form-grid-3">
            <Field label="Full Name">
              <input value={form.name} onChange={e => set("name", e.target.value)}
                placeholder="Rahul Sharma" />
            </Field>
            <Field label="Stream / Program">
              <select value={form.stream} onChange={e => set("stream", e.target.value)}>
                {STREAMS.map(s => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="City">
              <select value={form.city} onChange={e => set("city", e.target.value)}>
                {CITIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Institute Name">
              <input value={form.institute} onChange={e => set("institute", e.target.value)}
                placeholder="e.g. PICT Pune" />
            </Field>
            <Field label="Institute Tier" hint="1 = IIT/NIT, 2 = State Engg, 3 = Others">
              <select value={form.institute_tier} onChange={e => set("institute_tier", e.target.value)}>
                <option value={1}>Tier 1 — IIT / NIT / Top Private</option>
                <option value={2}>Tier 2 — State Engg / Mid Private</option>
                <option value={3}>Tier 3 — Private / Rural</option>
              </select>
            </Field>
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Academic Performance</h3>
          <div className="form-grid-3">
            <Field label="Current CGPA (out of 10)">
              <input type="number" step="0.1" min="0" max="10"
                value={form.cgpa} onChange={e => set("cgpa", e.target.value)}
                placeholder="6.8" required />
            </Field>
            <Field label="CGPA Last Semester" hint="Leave blank to auto-fill">
              <input type="number" step="0.1" min="0" max="10"
                value={form.cgpa_sem_prev1} onChange={e => set("cgpa_sem_prev1", e.target.value)}
                placeholder="auto" />
            </Field>
            <Field label="CGPA 2 Semesters Ago" hint="For PMScore calculation">
              <input type="number" step="0.1" min="0" max="10"
                value={form.cgpa_sem_prev2} onChange={e => set("cgpa_sem_prev2", e.target.value)}
                placeholder="auto" />
            </Field>
            <Field label="Active Backlogs">
              <input type="number" min="0" max="20"
                value={form.backlogs} onChange={e => set("backlogs", e.target.value)} />
            </Field>
            <Field label="Academic Gap (years)">
              <input type="number" min="0" max="5"
                value={form.sem_gap_years} onChange={e => set("sem_gap_years", e.target.value)} />
            </Field>
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Experience & Skills</h3>
          <div className="form-grid-3">
            <Field label="Number of Internships">
              <input type="number" min="0" max="10"
                value={form.num_internships} onChange={e => set("num_internships", e.target.value)} />
            </Field>
            <Field label="Internship Quality">
              <select value={form.internship_quality}
                onChange={e => set("internship_quality", e.target.value)}>
                {INTERNSHIP_LABELS.map((l, i) => <option key={i} value={i}>{l}</option>)}
              </select>
            </Field>
            <Field label="Certifications Earned">
              <input type="number" min="0" max="20"
                value={form.num_certifications} onChange={e => set("num_certifications", e.target.value)} />
            </Field>
            <Field label="Job Portal Activity (0–1)" hint="0 = inactive, 1 = very active">
              <div className="range-wrap">
                <input type="range" min="0" max="1" step="0.05"
                  value={form.job_portal_activity}
                  onChange={e => set("job_portal_activity", parseFloat(e.target.value))} />
                <span className="range-val">{form.job_portal_activity}</span>
              </div>
            </Field>
          </div>
          <div className="form-grid-3" style={{ marginTop: 12 }}>
            <label className="checkbox-field">
              <input type="checkbox" checked={form.has_github}
                onChange={e => set("has_github", e.target.checked)} />
              <span>Active GitHub Profile</span>
            </label>
            <label className="checkbox-field">
              <input type="checkbox" checked={form.has_linkedin}
                onChange={e => set("has_linkedin", e.target.checked)} />
              <span>LinkedIn Presence</span>
            </label>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        <div className="form-actions">
          <button type="submit" className="btn-primary btn-large" disabled={loading}>
            {loading ? (
              <><span className="spinner-sm" /> Scoring…</>
            ) : "⚡ Generate PlaceIQ Score"}
          </button>
        </div>
      </form>
    </div>
  );
}
