"""
PlaceIQ — FastAPI Backend
REST API for real-time placement risk scoring, batch processing,
portfolio analytics, and action engine.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import json
import io
import sys
import os
from pathlib import Path
from typing import Optional, List
import uvicorn

# Add ml directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "ml"))

try:
    from predict import score_student, score_batch, CITY_DEMAND, BASE_SALARIES
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

app = FastAPI(
    title="PlaceIQ API",
    description="AI-Powered Placement Risk Intelligence for Education Loan Portfolios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Schemas (inline for simplicity) ─────────────────────────────

from pydantic import BaseModel, Field

class StudentInput(BaseModel):
    student_id:           Optional[str] = "DEMO001"
    name:                 Optional[str] = "Student"
    stream:               Optional[str] = "B.Tech CS"
    institute:            Optional[str] = "Unknown Institute"
    institute_tier:       int   = Field(2, ge=1, le=3)
    city:                 Optional[str] = "Pune"
    cgpa:                 float = Field(6.5, ge=0.0, le=10.0)
    cgpa_sem_prev1:       Optional[float] = None
    cgpa_sem_prev2:       Optional[float] = None
    backlogs:             int   = Field(0, ge=0)
    sem_gap_years:        int   = Field(0, ge=0)
    num_internships:      int   = Field(0, ge=0)
    internship_quality:   int   = Field(0, ge=0, le=4)
    num_certifications:   int   = Field(0, ge=0)
    has_github:           bool  = False
    has_linkedin:         bool  = False
    job_portal_activity:  float = Field(0.3, ge=0.0, le=1.0)
    sector_growth_index:  Optional[float] = 1.0

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "STU0001",
                "name": "Rahul Sharma",
                "stream": "B.Tech CS",
                "institute": "PICT Pune",
                "institute_tier": 2,
                "city": "Pune",
                "cgpa": 6.8,
                "cgpa_sem_prev1": 6.5,
                "cgpa_sem_prev2": 6.3,
                "backlogs": 0,
                "sem_gap_years": 0,
                "num_internships": 1,
                "internship_quality": 1,
                "num_certifications": 0,
                "has_github": False,
                "has_linkedin": True,
                "job_portal_activity": 0.35,
                "sector_growth_index": 0.95
            }
        }

class BatchInput(BaseModel):
    students: List[StudentInput]


# ─── Fallback scoring (no ML models needed for demo) ─────────────

def fallback_score(student: dict) -> dict:
    """Formula-based scoring when ML models aren't loaded."""
    cgpa  = float(student.get("cgpa", 6.5))
    tier  = int(student.get("institute_tier", 2))
    city  = student.get("city", "Pune")
    inter = int(student.get("internship_quality", 0))
    certs = int(student.get("num_certifications", 0))
    portal = float(student.get("job_portal_activity", 0.3))
    backlogs = int(student.get("backlogs", 0))

    city_demand_map = {
        "Bangalore": 1.35, "Hyderabad": 1.25, "Pune": 1.10, "Mumbai": 1.20,
        "Delhi NCR": 1.15, "Chennai": 1.05, "Kolkata": 0.90, "Jaipur": 0.82,
        "Bhopal": 0.75, "Patna": 0.68, "Lucknow": 0.72, "Nagpur": 0.80,
    }
    city_d = city_demand_map.get(city, 1.0)

    base = {1: 0.88, 2: 0.62, 3: 0.38}[tier]
    cgpa_boost = (cgpa - 6.0) / 4.0 * 0.18
    intern_boost = inter / 4.0 * 0.20
    cert_boost = min(certs * 0.04, 0.12)
    market_boost = (city_d - 1.0) * 0.12
    portal_boost = portal * 0.10
    backlog_pen = min(backlogs * 0.05, 0.20)

    p6 = float(np.clip(base + cgpa_boost + intern_boost + cert_boost +
                       market_boost + portal_boost - backlog_pen, 0.05, 0.97))
    p3  = round(p6 * 0.38, 4)
    p12 = round(min(p6 * 1.32, 0.97), 4)
    p6  = round(p6, 4)

    risk_score = float(np.clip(p6 * 55 + (cgpa/10)*20 + (inter/4)*15 + (city_d-0.5)/1.3*10, 0, 100))
    if risk_score >= 75:   band = "LOW"
    elif risk_score >= 50: band = "MEDIUM"
    elif risk_score >= 25: band = "HIGH"
    else:                  band = "CRITICAL"

    # PMScore
    cgpa_p1 = float(student.get("cgpa_sem_prev1") or cgpa - 0.1)
    cgpa_p2 = float(student.get("cgpa_sem_prev2") or cgpa - 0.2)
    pm = float(np.clip((cgpa - cgpa_p2) * 5 + (portal - 0.5) * 6 + min(certs*1.5+inter*1.5, 8), -25, 25))
    pm_trend = "Improving" if pm > 2 else ("Declining" if pm < -2 else "Stable")

    # Salary
    base_sal_map = {
        "B.Tech CS": 650000, "B.Tech ECE": 550000, "B.Tech Mech": 480000,
        "MBA Finance": 720000, "MBA Marketing": 680000, "BBA": 380000,
        "B.Pharm": 420000, "B.Sc Nursing": 350000, "LLB": 450000, "BCA": 420000,
    }
    tier_m = {1: 2.2, 2: 1.2, 3: 0.75}[tier]
    base_sal = base_sal_map.get(student.get("stream", "B.Tech CS"), 500000)
    p50 = int(base_sal * tier_m * city_d)
    p25 = int(p50 * 0.78)
    p75 = int(p50 * 1.28)

    action_map = {
        "LOW": {
            "student_actions": ["Continue placement progress tracking","Register on additional job portals","Attend campus placement drives"],
            "lender_actions": ["Routine portfolio monitoring","Send placement tracker"],
            "alert_level": "info"
        },
        "MEDIUM": {
            "student_actions": ["Complete resume review","Close skill gaps via online courses","Apply to 5+ job portals this week","Activate LinkedIn profile"],
            "lender_actions": ["Flag for counselor review","Send skill-gap alert","Monitor in 30-day cycle"],
            "alert_level": "warning"
        },
        "HIGH": {
            "student_actions": ["Book mock interview session now","Complete one certification within 30 days","Apply to 10+ positions immediately","Connect with 5 sector alumni on LinkedIn"],
            "lender_actions": ["Pre-emptive EMI restructure offer","Assign relationship manager","Prepare for potential NPA classification"],
            "alert_level": "high"
        },
        "CRITICAL": {
            "student_actions": ["Immediate career counselor assignment","Explore alternative career pathways","Apply to mass recruiters without restrictions","Consider 6-month upskilling program"],
            "lender_actions": ["Initiate repayment plan negotiation","Prepare legal documentation","Escalate to senior credit officer","Offer extended moratorium period"],
            "alert_level": "critical"
        },
    }

    # SHAP-style drivers (formula-based)
    contributions = [
        ("internship_quality", "Internship quality", inter / 4.0, intern_boost),
        ("cgpa", "Current CGPA", cgpa, cgpa_boost),
        ("city_labor_demand", "City labor demand", city_d, market_boost),
        ("num_certifications", "Certifications earned", certs, cert_boost),
        ("job_portal_activity", "Job portal engagement", portal, portal_boost),
        ("backlogs", "Number of backlogs", backlogs, -backlog_pen),
    ]
    contributions.sort(key=lambda x: abs(x[3]), reverse=True)
    shap_drivers = [
        {
            "feature": c[0], "label": c[1], "value": round(c[2], 3),
            "shap": round(c[3], 4), "abs_shap": round(abs(c[3]), 4),
            "direction": "positive" if c[3] >= 0 else "risk",
            "description": f"{'Strong' if c[3] > 0 else 'Low'} {c[1].lower()}"
        }
        for c in contributions[:3]
    ]

    return {
        "student_id":   student.get("student_id", "DEMO"),
        "name":         student.get("name", "Student"),
        "stream":       student.get("stream", "B.Tech CS"),
        "institute":    student.get("institute", "Unknown"),
        "institute_tier": tier,
        "city":         city,
        "placement_probability": {"3mo": p3, "6mo": p6, "12mo": p12},
        "risk_score":   round(risk_score, 1),
        "risk_band":    band,
        "pmscore":      {"pmscore": round(pm, 1), "trend": pm_trend,
                         "trend_icon": "📈" if pm > 2 else ("📉" if pm < -2 else "➡️"),
                         "is_improving": pm >= 0},
        "salary":       {"p25": p25, "p50": p50, "p75": p75,
                         "formatted": {"p25": f"₹{p25/100000:.1f}L",
                                       "p50": f"₹{p50/100000:.1f}L",
                                       "p75": f"₹{p75/100000:.1f}L"}},
        "shap_drivers": shap_drivers,
        "recommended_actions": action_map[band],
        "model_version": "1.0.0-fallback",
    }


def do_score(student_dict: dict) -> dict:
    """Score using ML models if available, else fallback."""
    if ML_AVAILABLE:
        try:
            return score_student(student_dict)
        except Exception:
            pass
    return fallback_score(student_dict)


# ─── Routes ──────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "PlaceIQ API",
        "version": "1.0.0",
        "status": "running",
        "ml_models_loaded": ML_AVAILABLE,
        "endpoints": ["/predict", "/batch", "/portfolio", "/health", "/docs"]
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "ml_available": ML_AVAILABLE}


@app.post("/predict", tags=["Scoring"])
def predict_student(student: StudentInput):
    """
    Score a single student — returns full PlaceIQ risk profile.
    Includes placement probabilities, salary forecast, SHAP drivers, PMScore, and action recommendations.
    """
    data = student.dict()
    if data.get("cgpa_sem_prev1") is None:
        data["cgpa_sem_prev1"] = data["cgpa"] - 0.15
    if data.get("cgpa_sem_prev2") is None:
        data["cgpa_sem_prev2"] = data["cgpa"] - 0.30
    return do_score(data)


@app.post("/batch", tags=["Scoring"])
def batch_score(payload: BatchInput):
    """
    Score multiple students at once. Returns ranked list sorted by risk (worst first).
    Includes portfolio-level summary stats.
    """
    students = [s.dict() for s in payload.students]
    for s in students:
        if s.get("cgpa_sem_prev1") is None:
            s["cgpa_sem_prev1"] = s["cgpa"] - 0.15
        if s.get("cgpa_sem_prev2") is None:
            s["cgpa_sem_prev2"] = s["cgpa"] - 0.30

    results = [do_score(s) for s in students]
    results.sort(key=lambda x: x["risk_score"])  # worst first

    # Portfolio summary
    bands = [r["risk_band"] for r in results]
    total = len(results)
    avg_risk = float(np.mean([r["risk_score"] for r in results]))
    avg_pm   = float(np.mean([r["pmscore"]["pmscore"] for r in results]))

    summary = {
        "total_students":    total,
        "avg_risk_score":    round(avg_risk, 1),
        "avg_pmscore":       round(avg_pm, 1),
        "risk_distribution": {
            "CRITICAL": bands.count("CRITICAL"),
            "HIGH":     bands.count("HIGH"),
            "MEDIUM":   bands.count("MEDIUM"),
            "LOW":      bands.count("LOW"),
        },
        "npa_risk_count":    bands.count("CRITICAL") + bands.count("HIGH"),
        "npa_risk_pct":      round((bands.count("CRITICAL") + bands.count("HIGH")) / total * 100, 1),
    }

    return {"summary": summary, "students": results}


@app.post("/upload-csv", tags=["Scoring"])
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV of student records for batch scoring.
    Returns full portfolio analysis with risk rankings.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(400, f"Could not parse CSV: {e}")

    # Map columns flexibly
    col_map = {
        "cgpa": ["cgpa", "CGPA", "gpa"],
        "institute_tier": ["institute_tier", "tier", "Tier"],
        "city": ["city", "City", "location"],
        "name": ["name", "Name", "student_name"],
        "stream": ["stream", "Stream", "program", "Program"],
    }

    students = []
    for _, row in df.iterrows():
        student = {}
        for field, aliases in col_map.items():
            for a in aliases:
                if a in row:
                    student[field] = row[a]
                    break
        # Fill remaining from row directly
        for col in df.columns:
            if col not in student:
                student[col] = row[col]
        students.append(student)

    if not students:
        raise HTTPException(400, "No valid student records found in CSV")

    results = [do_score(s) for s in students[:200]]  # cap at 200
    results.sort(key=lambda x: x["risk_score"])

    bands = [r["risk_band"] for r in results]
    total = len(results)

    return {
        "filename": file.filename,
        "total_scored": total,
        "summary": {
            "total_students":    total,
            "avg_risk_score":    round(float(np.mean([r["risk_score"] for r in results])), 1),
            "avg_pmscore":       round(float(np.mean([r["pmscore"]["pmscore"] for r in results])), 1),
            "risk_distribution": {
                "CRITICAL": bands.count("CRITICAL"),
                "HIGH":     bands.count("HIGH"),
                "MEDIUM":   bands.count("MEDIUM"),
                "LOW":      bands.count("LOW"),
            },
            "npa_risk_count": bands.count("CRITICAL") + bands.count("HIGH"),
            "npa_risk_pct": round((bands.count("CRITICAL") + bands.count("HIGH")) / total * 100, 1),
        },
        "students": results,
    }


@app.get("/portfolio/summary", tags=["Portfolio"])
def portfolio_summary():
    """Return demo portfolio summary with simulated student data."""
    import random
    random.seed(99)
    np.random.seed(99)

    demo_students = []
    names = ["Rahul Sharma","Priya Patel","Arjun Singh","Neha Kumar","Karan Gupta",
             "Ananya Joshi","Vikram Verma","Shreya Shah","Aditya Yadav","Pooja Mishra",
             "Rohan Nair","Simran Reddy","Nikhil Mehta","Kavya Chopra","Siddharth Agarwal",
             "Meera Iyer","Raj Kulkarni","Divya Bhat","Amit Pandey","Sunita Tiwari"]
    streams = ["B.Tech CS","B.Tech ECE","MBA Finance","B.Tech Mech","BCA","MBA Marketing","B.Pharm"]
    cities  = ["Pune","Bangalore","Mumbai","Hyderabad","Chennai","Delhi NCR","Kolkata"]
    insts   = {1:["VIT Vellore","BITS Pilani"], 2:["PICT Pune","SRM Chennai","Manipal Jaipur"],
               3:["Global Institute Bhopal","City College Nagpur","Sunrise College Patna"]}

    for i, name in enumerate(names):
        tier = random.choices([1,2,3], weights=[10,45,45])[0]
        cgpa = round(random.gauss({1:7.8,2:7.0,3:6.2}[tier], 0.7), 1)
        cgpa = max(4.0, min(10.0, cgpa))
        demo_students.append({
            "student_id":         f"STU{i+1:04d}",
            "name":               name,
            "stream":             random.choice(streams),
            "institute":          random.choice(insts[tier]),
            "institute_tier":     tier,
            "city":               random.choice(cities),
            "cgpa":               cgpa,
            "cgpa_sem_prev1":     max(4.0, cgpa - round(random.uniform(0,0.5),1)),
            "cgpa_sem_prev2":     max(4.0, cgpa - round(random.uniform(0,0.8),1)),
            "backlogs":           random.choices([0,1,2,3], weights=[65,20,10,5])[0],
            "sem_gap_years":      random.choices([0,1,2], weights=[80,15,5])[0],
            "num_internships":    random.choices([0,1,2,3], weights=[25,40,25,10])[0],
            "internship_quality": random.choices([0,1,2,3,4], weights=[20,30,28,15,7])[0],
            "num_certifications": random.choices([0,1,2,3], weights=[35,35,20,10])[0],
            "has_github":         random.random() < 0.4,
            "has_linkedin":       random.random() < 0.55,
            "job_portal_activity": round(random.uniform(0.1, 0.9), 2),
            "sector_growth_index": round(random.gauss(1.0, 0.2), 2),
        })

    results = [do_score(s) for s in demo_students]
    results.sort(key=lambda x: x["risk_score"])
    bands = [r["risk_band"] for r in results]
    total = len(results)

    return {
        "portfolio_id": "DEMO-PORTFOLIO-001",
        "total_students": total,
        "summary": {
            "avg_risk_score": round(float(np.mean([r["risk_score"] for r in results])), 1),
            "avg_pmscore": round(float(np.mean([r["pmscore"]["pmscore"] for r in results])), 1),
            "risk_distribution": {
                "CRITICAL": bands.count("CRITICAL"),
                "HIGH": bands.count("HIGH"),
                "MEDIUM": bands.count("MEDIUM"),
                "LOW": bands.count("LOW"),
            },
            "npa_risk_count": bands.count("CRITICAL") + bands.count("HIGH"),
            "npa_risk_pct": round((bands.count("CRITICAL") + bands.count("HIGH")) / total * 100, 1),
            "avg_salary_p50": int(np.mean([r["salary"]["p50"] for r in results])),
        },
        "students": results,
    }


@app.get("/metadata", tags=["Info"])
def get_metadata():
    """Return model metadata and feature information."""
    try:
        import json
        meta_path = Path(__file__).parent.parent / "ml" / "artifacts" / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "model_version": "1.0.0",
        "features": 14,
        "horizons": ["3mo", "6mo", "12mo"],
        "ml_available": ML_AVAILABLE,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
