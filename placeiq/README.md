# PlaceIQ — AI-Powered Placement Risk Intelligence

> **TenzorX 2026 National AI Hackathon** · Poonawalla Fincorp · Grand Prize Submission

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange?style=flat)](https://xgboost.readthedocs.io)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://reactjs.org)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable_AI-blue?style=flat)](https://shap.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

India has **₹2.2 Lakh Crore** in active education loans (RBI 2024).  
**28%** of Tier 2/3 college borrowers show early-stage stress.  
Yet **no NBFC has a placement risk model** integrated into loan monitoring.

Lenders disburse based on program quality — then have **zero visibility** into what happens after graduation.  
They discover risk at **EMI-miss**, when recovery costs ₹40,000+ per borrower. The intervention window has closed.

---

## The Solution: PlaceIQ

A real-time AI engine that converts student + market signals into **placement risk scores**, **salary forecasts**, and **automated lender actions** — 6–12 months before any EMI is missed.

```
INPUTS             AI ENGINE          OUTPUTS          ACTIONS
Student Profile  →  XGBoost + SHAP  →  Risk Score   →  Student: Mock Interview
Institute Data      PMScore Tracker     Salary Band     Lender: Pre-EMI Offer
Labor Market        Action Engine       3 Horizons      RM: Flag for Review
```

### 1% NPA reduction on ₹1,000 Cr book = **₹10 Crore saved annually**

---

## Live Demo Output

```
PlaceIQ — Student Risk Profile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rahul Sharma  |  B.Tech CS  |  Tier-2 Institute, Pune  |  Final Year 2025

Placement @ 3 mo   ████░░░░░░░░░░░░░  22%  — Unlikely without intervention
Placement @ 6 mo   ██████████░░░░░░░  61%  — Moderate confidence
Placement @ 12 mo  █████████████████  84%  — High confidence

Risk Score    🔴 HIGH — 38/100
PMScore       📉 −8.0  — Declining

Salary Range  ₹4.2L – ₹6.8L per annum  |  P50: ₹5.4L

Top Risk Drivers (SHAP)
  ▼ Low internship quality  (0.31)
  ▼ Weak IT hiring — Pune Q1 2025  (0.24)
  ▼ No certifications  (0.19)

Lender Alert  ⚠️  Pre-emptive EMI restructure offer recommended.
Student Action  → Book mock interview  → Apply to 5 BFSI portals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Key Features

### Placement Prediction (Multi-Horizon)
- 3-month, 6-month, 12-month placement probability per student
- XGBoost classifier calibrated per institute tier and program stream
- Handles B.Tech, MBA, Healthcare, Law, and BCA streams

### PMScore™ — The Signature Feature
The **Placement Momentum Score** tracks *trajectory*, not just a snapshot.

```
Semester −2: 6.3 CGPA → Semester −1: 6.5 CGPA → Now: 6.8 CGPA
PMScore: +12 → Improving — same risk score, very different intervention needed
```

Like CIBIL tracks credit *behaviour* — PMScore tracks employability *behaviour*.  
**First such metric in the Indian NBFC space.**

### SHAP Explainability (RBI Fair Practice Compliant)
Every score shows the top-3 human-readable risk drivers:
- *"Low internship depth (0.31 SHAP impact)"*
- *"Weak IT hiring in Pune Q1 2025 (0.24)"*
- Auditor-friendly · No black-box decisions · RBI compliant

### Action Engine
Automatically prescribes the right response for every risk level:

| Band | Score | Student Action | Lender Action |
|------|-------|---------------|---------------|
| 🟢 LOW | 75–100 | Progress updates | Routine monitoring |
| 🟡 MEDIUM | 50–74 | Resume review + skill gap nudge | Flag for counselor review |
| 🔴 HIGH | 25–49 | Mock interview + job portal activation | Pre-emptive EMI restructure |
| ⚫ CRITICAL | 0–24 | Career counselor assignment | Proactive repayment plan |

### Salary Forecasting
- P25 / P50 / P75 salary band using quantile regression
- Benchmarked by institute tier, city, and program stream
- Confidence intervals, not just point estimates

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      React Dashboard                          │
│  Portfolio View · Student Card · SHAP Chart · Batch Upload   │
└─────────────────────────┬────────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend                           │
│  /predict · /batch · /upload-csv · /portfolio/summary        │
└──────────────┬───────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────┐
│                      ML Layer                                 │
│  XGBoost (3 placement models) + Salary Regressor (P25/P50/P75)│
│  SHAP TreeExplainer · PMScore Engine · Action Rule Table     │
└──────────────┬───────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────┐
│                     Data Layer                                │
│  1,000 synthetic students · NIRF institute data              │
│  NSDC labor demand indices · City-level hiring signals       │
└──────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| ML | Python, XGBoost, SHAP, scikit-learn | Industry standard, explainable, fast |
| Backend | FastAPI + Pydantic + Uvicorn | Async REST, auto-docs, 2× faster than Flask |
| Frontend | React 18 + Recharts + Vite | Modern, component-based, rapid build |
| Infra | Docker + Docker Compose | One-command deploy, zero config |

---

## Quick Start

### Option 1 — Automated Setup (recommended)

```bash
git clone https://github.com/your-team/placeiq
cd placeiq
bash setup.sh
```

Then open two terminals:
```bash
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

- **Dashboard:** http://localhost:3000  
- **API Docs:** http://localhost:8000/docs  
- **Health Check:** http://localhost:8000/health  

### Option 2 — Docker (one command)

```bash
docker-compose up
```

### Manual Setup

```bash
# Python environment
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Generate data + train models
cd data && python generate_dataset.py
cd ../ml && python train_model.py

# Frontend
cd ../frontend && npm install && npm run dev
```

---

## API Reference

### `POST /predict` — Score a single student

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rahul Sharma",
    "stream": "B.Tech CS",
    "institute_tier": 2,
    "city": "Pune",
    "cgpa": 6.8,
    "num_internships": 1,
    "internship_quality": 1,
    "num_certifications": 0,
    "has_linkedin": true,
    "job_portal_activity": 0.35
  }'
```

**Response:**
```json
{
  "name": "Rahul Sharma",
  "risk_band": "HIGH",
  "risk_score": 38.2,
  "placement_probability": {
    "3mo": 0.22,
    "6mo": 0.61,
    "12mo": 0.84
  },
  "pmscore": { "pmscore": -8.0, "trend": "Declining", "trend_icon": "📉" },
  "salary": { "p25": 420000, "p50": 540000, "p75": 690000 },
  "shap_drivers": [...],
  "recommended_actions": { "lender_actions": [...], "student_actions": [...] }
}
```

### `POST /batch` — Score multiple students

```bash
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"students": [...]}'
```

### `POST /upload-csv` — Batch upload from CSV

```bash
curl -X POST http://localhost:8000/upload-csv \
  -F "file=@students.csv"
```

### `GET /portfolio/summary` — Demo portfolio

```bash
curl http://localhost:8000/portfolio/summary
```

---

## Model Details

### Feature Engineering (14 features)

| Feature | Description | Impact |
|---------|-------------|--------|
| CGPA (current + 2 prev semesters) | Academic performance + trend | High |
| Internship quality (0–4 scale) | Depth of work experience | High |
| City labor demand index | Local hiring activity | Medium |
| Job portal activity (0–1) | Proactive job search signal | Medium |
| Institute tier (1–3) | Placement infrastructure quality | High |
| Certifications earned | Skill investment signal | Medium |
| GitHub / LinkedIn presence | Digital employability footprint | Low-Medium |
| Backlogs, academic gaps | Risk flags | Medium |

### Model Performance (on test set)

| Model | AUC | Accuracy |
|-------|-----|---------|
| Placement 3-month | 0.89 | 82% |
| Placement 6-month | 0.87 | 79% |
| Placement 12-month | 0.86 | 77% |
| Salary P50 MAE | — | ₹32,000 |

Logistic Regression baseline AUC: ~0.79 (XGBoost +0.08–0.10 improvement)

---

## Data Sources

| Data Type | Source | Status |
|-----------|--------|--------|
| Student profiles | Synthetic (1,000 records modelled on NIRF data) | ✅ Ready |
| Institute placement | NIRF Rankings, AISHE Reports | ✅ Public |
| City labor demand | NSDC reports, CMIE datasets | ✅ Modelled |
| Salary benchmarks | AmbitionBox / Glassdoor indices | ✅ Modelled |
| Macro indicators | RBI Monetary Reports | ✅ Open data |

---

## Scalability Path

```
Hackathon Demo                →  Pilot NBFC (Month 1–3)         →  Scale (Month 4–12)
──────────────────────────        ──────────────────────────────    ─────────────────────
1,000 synthetic students          REST API: Finacle/BankWare        100K+ students
XGBoost trained in <5 min         CSV onboarding 5–10 institutes    AWS Batch pipeline
FastAPI + React prototype          Model calibrated per cluster      Quarterly retraining
Full SHAP + PMScore               Real placement outcome data        NBFC white-labeling
```

---

## Business Impact

| Metric | Value |
|--------|-------|
| NPA savings at 1% improvement | ₹10 Cr per ₹1,000 Cr book |
| Early warning lead time | 6–12 months before EMI miss |
| Cost: intervention vs recovery | ₹500–2,000 vs ₹40,000+ |
| NBFCs with this product today | 0 (first-mover opportunity) |

---

## Repository Structure

```
placeiq/
├── data/
│   ├── generate_dataset.py     # Synthetic data generator
│   └── students.csv            # Generated (auto-created on setup)
├── ml/
│   ├── train_model.py          # XGBoost training pipeline
│   ├── predict.py              # Real-time scoring engine
│   └── artifacts/              # Trained models (auto-created)
├── backend/
│   └── main.py                 # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Portfolio lender view
│   │   │   ├── ScoreForm.jsx   # Live student scoring
│   │   │   └── BatchUpload.jsx # CSV batch scoring
│   │   └── components/
│   │       └── StudentCard.jsx # Full risk profile card
│   └── package.json
├── docker/
│   └── Dockerfile.backend
├── docker-compose.yml
├── requirements.txt
└── setup.sh                    # One-command setup
```

---

## Team

**PlaceIQ Team** · TenzorX 2026 National AI Hackathon · Poonawalla Fincorp

*Predict. Intervene. Protect.*

---

## License

MIT License — see [LICENSE](LICENSE) for details.
