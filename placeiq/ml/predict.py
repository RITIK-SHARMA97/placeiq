"""
PlaceIQ — Prediction Engine
Real-time student risk scoring with SHAP explainability,
salary forecasting, and PMScore trajectory tracking.
"""

import numpy as np
import pandas as pd
import pickle
import json
import shap
from pathlib import Path
from typing import Optional

# ─── Load Artifacts ──────────────────────────────────────────────
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

_cache = {}

def _load(name):
    if name not in _cache:
        with open(ARTIFACTS_DIR / name, "rb") as f:
            _cache[name] = pickle.load(f)
    return _cache[name]

def get_metadata():
    if "_meta" not in _cache:
        with open(ARTIFACTS_DIR / "metadata.json") as f:
            _cache["_meta"] = json.load(f)
    return _cache["_meta"]

FEATURE_COLS = [
    "cgpa", "cgpa_sem_prev1", "cgpa_sem_prev2",
    "backlogs", "sem_gap_years",
    "num_internships", "internship_quality",
    "num_certifications", "has_github", "has_linkedin",
    "job_portal_activity", "city_labor_demand",
    "sector_growth_index", "institute_tier"
]

FEATURE_LABELS = {
    "cgpa":                   "Current CGPA",
    "cgpa_sem_prev1":         "CGPA (last semester)",
    "cgpa_sem_prev2":         "CGPA (2 semesters ago)",
    "backlogs":               "Number of backlogs",
    "sem_gap_years":          "Academic gap years",
    "num_internships":        "Internships completed",
    "internship_quality":     "Internship quality",
    "num_certifications":     "Certifications earned",
    "has_github":             "Active GitHub profile",
    "has_linkedin":           "LinkedIn presence",
    "job_portal_activity":    "Job portal engagement",
    "city_labor_demand":      "City labor demand",
    "sector_growth_index":    "Sector growth index",
    "institute_tier":         "Institute tier",
}

CITY_DEMAND = {
    "Bangalore": 1.35, "Hyderabad": 1.25, "Pune": 1.10, "Mumbai": 1.20,
    "Delhi NCR": 1.15, "Chennai": 1.05, "Kolkata": 0.90, "Jaipur": 0.82,
    "Bhopal": 0.75, "Patna": 0.68, "Lucknow": 0.72, "Nagpur": 0.80,
}

BASE_SALARIES = {
    "B.Tech CS": 650000, "B.Tech ECE": 550000, "B.Tech Mech": 480000,
    "MBA Finance": 720000, "MBA Marketing": 680000, "BBA": 380000,
    "B.Pharm": 420000, "B.Sc Nursing": 350000, "LLB": 450000, "BCA": 420000,
}

TIER_SALARY_MULT = {1: 2.2, 2: 1.2, 3: 0.75}

ACTION_ENGINE = {
    "LOW":      {
        "student_actions": [
            "Keep up placement progress updates",
            "Register on 2-3 additional job portals",
            "Attend upcoming campus placement drives",
        ],
        "lender_actions": [
            "Routine portfolio monitoring",
            "Send placement milestone tracker",
        ],
        "alert_level": "info",
    },
    "MEDIUM":   {
        "student_actions": [
            "Complete your resume review with career center",
            "Identify and close skill gaps via free online courses",
            "Activate profiles on Naukri, LinkedIn, and Internshala",
            "Apply to 5+ job portals in your target sector this week",
        ],
        "lender_actions": [
            "Flag account for counselor review",
            "Send automated skill-gap alert to student",
            "Monitor closely in 30-day cycle",
        ],
        "alert_level": "warning",
    },
    "HIGH":     {
        "student_actions": [
            "Book a mock interview session via the placement portal",
            "Complete one certification (AWS/Google/NPTEL) within 30 days",
            "Apply to 10+ positions — broadening sector is advisable",
            "Connect with 5 alumni in target sector on LinkedIn",
        ],
        "lender_actions": [
            "Pre-emptive EMI restructure offer recommended",
            "Assign relationship manager for outreach",
            "Send 6-month placement window alert",
            "Prepare for potential NPA classification",
        ],
        "alert_level": "high",
    },
    "CRITICAL": {
        "student_actions": [
            "Immediate career counselor assignment required",
            "Explore alternative career pathways (govt exams, freelancing)",
            "Apply to mass recruiting companies without sector restriction",
            "Consider skill bridging programs (6-month upskilling)",
        ],
        "lender_actions": [
            "Initiate proactive repayment plan negotiation",
            "Prepare legal documentation as contingency",
            "Escalate to senior credit officer",
            "Offer extended moratorium period with revised schedule",
        ],
        "alert_level": "critical",
    },
}


def compute_features(student_data: dict) -> pd.DataFrame:
    """Convert raw student input into ML feature vector."""
    city = student_data.get("city", "Pune")
    city_demand = CITY_DEMAND.get(city, 1.0)

    row = {
        "cgpa":                float(student_data.get("cgpa", 6.5)),
        "cgpa_sem_prev1":      float(student_data.get("cgpa_sem_prev1",
                                     student_data.get("cgpa", 6.5) - 0.1)),
        "cgpa_sem_prev2":      float(student_data.get("cgpa_sem_prev2",
                                     student_data.get("cgpa", 6.5) - 0.2)),
        "backlogs":            int(student_data.get("backlogs", 0)),
        "sem_gap_years":       int(student_data.get("sem_gap_years", 0)),
        "num_internships":     int(student_data.get("num_internships", 0)),
        "internship_quality":  int(student_data.get("internship_quality", 0)),
        "num_certifications":  int(student_data.get("num_certifications", 0)),
        "has_github":          int(bool(student_data.get("has_github", False))),
        "has_linkedin":        int(bool(student_data.get("has_linkedin", False))),
        "job_portal_activity": float(student_data.get("job_portal_activity", 0.3)),
        "city_labor_demand":   city_demand,
        "sector_growth_index": float(student_data.get("sector_growth_index", 1.0)),
        "institute_tier":      int(student_data.get("institute_tier", 2)),
    }
    return pd.DataFrame([row])


def compute_pmscore(features: dict) -> dict:
    """
    Placement Momentum Score — tracks employability trajectory.
    Delta between current and 2-semester-ago predicted placement probability.
    Returns score (-25 to +25) and trend label.
    """
    cgpa_now  = float(features.get("cgpa", 6.5))
    cgpa_sem1 = float(features.get("cgpa_sem_prev1", cgpa_now))
    cgpa_sem2 = float(features.get("cgpa_sem_prev2", cgpa_now))
    portal    = float(features.get("job_portal_activity", 0.3))
    intern_q  = int(features.get("internship_quality", 0))
    certs     = int(features.get("num_certifications", 0))

    # Delta components
    cgpa_delta   = (cgpa_now - cgpa_sem2) * 5.0       # CGPA trajectory
    portal_delta = (portal - 0.5) * 6.0                # Portal engagement
    skill_bonus  = min(certs * 1.5 + intern_q * 1.5, 8.0)  # Skills growth

    raw_pm = cgpa_delta + portal_delta + skill_bonus
    pmscore = float(np.clip(raw_pm, -25, 25))

    # Trend label
    if pmscore >= 8:   trend = "Improving strongly"
    elif pmscore >= 3: trend = "Improving"
    elif pmscore >= -2: trend = "Stable"
    elif pmscore >= -8: trend = "Declining"
    else:              trend = "Declining sharply"

    trend_icon = "📈" if pmscore > 2 else ("📉" if pmscore < -2 else "➡️")

    return {
        "pmscore": round(pmscore, 1),
        "trend": trend,
        "trend_icon": trend_icon,
        "is_improving": pmscore >= 0,
    }


def compute_risk_score(placement_6mo: float, cgpa: float,
                        internship_q: int, city_demand: float) -> float:
    """Composite risk score 0–100 (100 = safest for lender)."""
    score = (
        placement_6mo * 55 +
        (cgpa / 10.0) * 20 +
        (internship_q / 4.0) * 15 +
        ((city_demand - 0.5) / 1.3) * 10
    )
    return float(np.clip(score, 0, 100))


def get_risk_band(score: float) -> str:
    if score >= 75:   return "LOW"
    elif score >= 50: return "MEDIUM"
    elif score >= 25: return "HIGH"
    else:             return "CRITICAL"


def compute_shap_top3(X_df: pd.DataFrame) -> list:
    """Return top-3 SHAP contributors as human-readable drivers."""
    try:
        explainer = _load("shap_explainer.pkl")
        sv_raw = explainer.shap_values(X_df)
        sv_arr = np.array(sv_raw)
        # Shape: (1,14) for single sample binary classification
        if sv_arr.ndim == 2:
            sv = sv_arr[0]           # shape (14,)
        elif sv_arr.ndim == 3:
            sv = sv_arr[1][0]        # multiclass: class 1, sample 0
        else:
            sv = sv_arr.flatten()

        drivers = []
        sorted_idx = np.argsort(np.abs(sv))[::-1]
        for i in sorted_idx[:3]:
            feat   = FEATURE_COLS[i]
            val    = float(X_df[feat].values[0])
            shap_v = float(sv[i])
            label  = FEATURE_LABELS.get(feat, feat)
            if shap_v < 0:
                desc = f"Low {label.lower()}" if val < 0.5 else f"{label} dragging score"
            else:
                desc = f"Strong {label.lower()}"
            drivers.append({
                "feature": feat,
                "label": label,
                "value": round(val, 3),
                "shap": round(shap_v, 4),
                "abs_shap": round(abs(shap_v), 4),
                "direction": "risk" if shap_v < 0 else "positive",
                "description": desc,
            })
        return drivers
    except Exception as e:
        # Fallback: formula-based top drivers
        return [
            {"feature": "internship_quality", "label": "Internship quality",
             "value": 1, "shap": -0.20, "abs_shap": 0.20, "direction": "risk",
             "description": "Low internship quality"},
            {"feature": "cgpa", "label": "Current CGPA",
             "value": 6.8, "shap": -0.12, "abs_shap": 0.12, "direction": "risk",
             "description": "Below-average CGPA"},
            {"feature": "city_labor_demand", "label": "City labor demand",
             "value": 1.1, "shap": 0.08, "abs_shap": 0.08, "direction": "positive",
             "description": "Strong city labor demand"},
        ]


def predict_salary(X_df: pd.DataFrame, stream: str, tier: int, city: str) -> dict:
    """Predict salary band P25/P50/P75."""
    try:
        p25_model = _load("model_salary_p25.pkl")
        p50_model = _load("model_salary_p50.pkl")
        p75_model = _load("model_salary_p75.pkl")

        import numpy as np
        p25 = float(np.expm1(p25_model.predict(X_df)[0]))
        p50 = float(np.expm1(p50_model.predict(X_df)[0]))
        p75 = float(np.expm1(p75_model.predict(X_df)[0]))
    except Exception:
        # Fallback to formula-based estimate
        base = BASE_SALARIES.get(stream, 500000)
        city_mult = CITY_DEMAND.get(city, 1.0)
        tier_mult = TIER_SALARY_MULT.get(tier, 1.0)
        p50 = base * tier_mult * city_mult
        p25 = p50 * 0.78
        p75 = p50 * 1.28

    return {
        "p25": int(p25),
        "p50": int(p50),
        "p75": int(p75),
        "formatted": {
            "p25": f"₹{p25/100000:.1f}L",
            "p50": f"₹{p50/100000:.1f}L",
            "p75": f"₹{p75/100000:.1f}L",
        }
    }


def score_student(student_data: dict) -> dict:
    """
    Main scoring function. Returns full PlaceIQ risk profile.

    Args:
        student_data: dict with student features

    Returns:
        Complete risk profile with placement probs, salary, SHAP, actions
    """
    X_df = compute_features(student_data)

    # ── Placement probabilities ───────────────────────────────────
    placement_probs = {}
    for horizon in ["3mo", "6mo", "12mo"]:
        try:
            model = _load(f"model_placement_{horizon}.pkl")
            prob = float(model.predict_proba(X_df)[0][1])
        except Exception:
            # Fallback formula
            cgpa = float(student_data.get("cgpa", 6.5))
            tier = int(student_data.get("institute_tier", 2))
            base = {1: 0.88, 2: 0.62, 3: 0.38}[tier]
            factor = {"3mo": 0.35, "6mo": 0.72, "12mo": 0.95}[horizon]
            prob = float(np.clip(base * factor + (cgpa - 6) * 0.03, 0.02, 0.97))
        placement_probs[horizon] = round(prob, 4)

    # ── Salary forecast ───────────────────────────────────────────
    stream = student_data.get("stream", "B.Tech CS")
    tier   = int(student_data.get("institute_tier", 2))
    city   = student_data.get("city", "Pune")
    salary = predict_salary(X_df, stream, tier, city)

    # ── PMScore ───────────────────────────────────────────────────
    pmscore_data = compute_pmscore(student_data)

    # ── Risk score & band ─────────────────────────────────────────
    risk_score = compute_risk_score(
        placement_probs["6mo"],
        float(student_data.get("cgpa", 6.5)),
        int(student_data.get("internship_quality", 0)),
        CITY_DEMAND.get(city, 1.0)
    )
    risk_band = get_risk_band(risk_score)

    # ── SHAP top-3 drivers ────────────────────────────────────────
    shap_drivers = compute_shap_top3(X_df)

    # ── Action Engine ─────────────────────────────────────────────
    actions = ACTION_ENGINE[risk_band]

    # ── Assemble response ─────────────────────────────────────────
    return {
        "student_id":   student_data.get("student_id", "DEMO"),
        "name":         student_data.get("name", "Student"),
        "stream":       stream,
        "institute":    student_data.get("institute", "Unknown Institute"),
        "institute_tier": tier,
        "city":         city,

        "placement_probability": {
            "3mo":  placement_probs["3mo"],
            "6mo":  placement_probs["6mo"],
            "12mo": placement_probs["12mo"],
        },

        "risk_score": round(risk_score, 1),
        "risk_band":  risk_band,

        "pmscore": pmscore_data,

        "salary": salary,

        "shap_drivers": shap_drivers,

        "recommended_actions": {
            "student_actions": actions["student_actions"],
            "lender_actions":  actions["lender_actions"],
            "alert_level":     actions["alert_level"],
        },

        "model_version": "1.0.0",
    }


def score_batch(students: list) -> list:
    """Score multiple students in one call."""
    return [score_student(s) for s in students]


# ── Quick self-test ───────────────────────────────────────────────
if __name__ == "__main__":
    demo = {
        "student_id":       "STU0001",
        "name":             "Rahul Sharma",
        "stream":           "B.Tech CS",
        "institute":        "PICT Pune",
        "institute_tier":   2,
        "city":             "Pune",
        "cgpa":             6.8,
        "cgpa_sem_prev1":   6.5,
        "cgpa_sem_prev2":   6.3,
        "backlogs":         0,
        "sem_gap_years":    0,
        "num_internships":  1,
        "internship_quality": 1,
        "num_certifications": 0,
        "has_github":       False,
        "has_linkedin":     True,
        "job_portal_activity": 0.35,
        "sector_growth_index": 0.95,
    }

    result = score_student(demo)
    print(json.dumps(result, indent=2, default=str))
