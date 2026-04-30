"""
PlaceIQ — Synthetic Dataset Generator
Generates 1,000 realistic Indian education loan student profiles
with placement outcomes for model training.
"""

import numpy as np
import pandas as pd
import json
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# ─── Domain Constants ─────────────────────────────────────────────
STREAMS = ["B.Tech CS", "B.Tech ECE", "B.Tech Mech", "MBA Finance",
           "MBA Marketing", "BBA", "B.Pharm", "B.Sc Nursing", "LLB", "BCA"]

INSTITUTE_TIERS = {
    1: {"name_suffix": "IIT/NIT/Top Private", "base_placement": 0.92, "salary_mult": 2.2},
    2: {"name_suffix": "State Engg/Mid Private", "base_placement": 0.68, "salary_mult": 1.2},
    3: {"name_suffix": "Tier-3 Private/Rural", "base_placement": 0.41, "salary_mult": 0.75},
}

CITIES = {
    "Bangalore": {"demand_mult": 1.35, "sector": "IT"},
    "Hyderabad": {"demand_mult": 1.25, "sector": "IT"},
    "Pune":      {"demand_mult": 1.10, "sector": "IT/Manufacturing"},
    "Mumbai":    {"demand_mult": 1.20, "sector": "BFSI"},
    "Delhi NCR": {"demand_mult": 1.15, "sector": "Mixed"},
    "Chennai":   {"demand_mult": 1.05, "sector": "IT/Manufacturing"},
    "Kolkata":   {"demand_mult": 0.90, "sector": "Mixed"},
    "Jaipur":    {"demand_mult": 0.82, "sector": "Manufacturing"},
    "Bhopal":    {"demand_mult": 0.75, "sector": "Government/PSU"},
    "Patna":     {"demand_mult": 0.68, "sector": "Government/PSU"},
    "Lucknow":   {"demand_mult": 0.72, "sector": "Mixed"},
    "Nagpur":    {"demand_mult": 0.80, "sector": "Manufacturing"},
}

SECTORS = ["IT", "BFSI", "Healthcare", "Manufacturing", "Government/PSU", "E-commerce", "Consulting"]

INTERNSHIP_QUALITY = {
    0: {"label": "None", "score": 0.0},
    1: {"label": "Low depth (local/unrelated)", "score": 0.25},
    2: {"label": "Moderate (SME/relevant)", "score": 0.55},
    3: {"label": "Strong (MNC/core domain)", "score": 0.85},
    4: {"label": "Excellent (FAANG/Top MNC)", "score": 1.0},
}

BASE_SALARIES = {
    "B.Tech CS": 650000, "B.Tech ECE": 550000, "B.Tech Mech": 480000,
    "MBA Finance": 720000, "MBA Marketing": 680000, "BBA": 380000,
    "B.Pharm": 420000, "B.Sc Nursing": 350000, "LLB": 450000, "BCA": 420000,
}

# ─── Feature Generation ────────────────────────────────────────────

def generate_student(idx):
    stream = random.choice(STREAMS)
    tier = np.random.choice([1, 2, 3], p=[0.12, 0.45, 0.43])
    city = random.choice(list(CITIES.keys()))
    city_info = CITIES[city]
    tier_info = INSTITUTE_TIERS[tier]

    # Academic features
    cgpa_mu = {1: 7.8, 2: 6.9, 3: 6.1}[tier]
    cgpa = float(np.clip(np.random.normal(cgpa_mu, 0.8), 4.0, 10.0))

    backlogs = max(0, int(np.random.poisson({1: 0.2, 2: 0.8, 3: 2.1}[tier])))
    sem_gap = random.choice([0, 0, 0, 1, 1, 2])  # year gaps

    # Internship
    internship_prob = {1: [0.02, 0.08, 0.20, 0.35, 0.35],
                       2: [0.12, 0.28, 0.32, 0.22, 0.06],
                       3: [0.30, 0.38, 0.22, 0.08, 0.02]}[tier]
    internship_quality = int(np.random.choice([0,1,2,3,4], p=internship_prob))
    num_internships = max(0, internship_quality + np.random.randint(-1, 2)) if internship_quality > 0 else 0

    # Skills / Certifications
    num_certs = max(0, int(np.random.poisson({1: 2.5, 2: 1.2, 3: 0.5}[tier])))
    has_github = random.random() < {1: 0.7, 2: 0.4, 3: 0.15}[tier]
    has_linkedin = random.random() < {1: 0.85, 2: 0.55, 3: 0.25}[tier]
    job_portal_activity = float(np.clip(np.random.beta(
        {1: 4, 2: 2.5, 3: 1.5}[tier], {1: 2, 2: 3, 3: 4}[tier]), 0.0, 1.0))

    # Market signals
    labor_demand = float(np.clip(city_info["demand_mult"] + np.random.normal(0, 0.15), 0.4, 1.8))
    sector_growth = float(np.clip(np.random.normal(1.0, 0.25), 0.3, 1.6))

    # PMScore history (2 previous semesters)
    # Simulate a trajectory of improvement or decline
    trend = np.random.choice([-1, 0, 1], p=[0.25, 0.35, 0.40])
    sem_prev2_cgpa = float(np.clip(cgpa + trend * np.random.uniform(0.3, 0.8), 4.0, 10.0))
    sem_prev1_cgpa = float(np.clip(cgpa + trend * np.random.uniform(0.15, 0.4), 4.0, 10.0))

    # ─── Outcome Simulation (ground truth) ───────────────────────
    # Placement probability model (deterministic + noise)
    base_p = tier_info["base_placement"]

    # Feature contributions to placement probability
    cgpa_contrib       = (cgpa - 6.0) / 4.0 * 0.18
    intern_contrib     = INTERNSHIP_QUALITY[internship_quality]["score"] * 0.20
    cert_contrib       = min(num_certs * 0.04, 0.12)
    market_contrib     = (labor_demand - 1.0) * 0.12
    portal_contrib     = job_portal_activity * 0.10
    linkedin_contrib   = 0.04 if has_linkedin else 0.0
    github_contrib     = 0.03 if has_github else 0.0
    backlog_penalty    = min(backlogs * 0.05, 0.20)
    gap_penalty        = sem_gap * 0.03

    # Trend contribution (PMScore)
    trend_contrib = trend * 0.05

    raw_p = (base_p + cgpa_contrib + intern_contrib + cert_contrib +
             market_contrib + portal_contrib + linkedin_contrib +
             github_contrib + trend_contrib - backlog_penalty - gap_penalty)
    raw_p = float(np.clip(raw_p + np.random.normal(0, 0.05), 0.02, 0.98))

    # Multi-horizon placement probabilities
    placed_3mo  = float(np.clip(raw_p * 0.35 + np.random.normal(0, 0.04), 0.01, 0.95))
    placed_6mo  = float(np.clip(raw_p * 0.72 + np.random.normal(0, 0.04), 0.05, 0.97))
    placed_12mo = float(np.clip(raw_p * 0.95 + np.random.normal(0, 0.03), 0.10, 0.99))

    # Binary outcomes (for classification training)
    is_placed_3mo  = int(random.random() < placed_3mo)
    is_placed_6mo  = int(random.random() < placed_6mo)
    is_placed_12mo = int(random.random() < placed_12mo)

    # Salary prediction (only if placed)
    base_sal = BASE_SALARIES.get(stream, 500000)
    salary_mult = (tier_info["salary_mult"] * city_info["demand_mult"] *
                   (1 + cgpa_contrib + intern_contrib) *
                   max(0.6, 1 + np.random.normal(0, 0.15)))
    expected_salary = float(base_sal * salary_mult)
    salary_p25 = float(expected_salary * 0.78)
    salary_p75 = float(expected_salary * 1.28)

    # PMScore (current semester delta from 2 semesters ago)
    pmscore = float(np.clip((cgpa - sem_prev2_cgpa) * 8 + trend * 5 +
                            (job_portal_activity - 0.5) * 4 +
                            np.random.normal(0, 2), -25, 25))

    # Risk score (composite, 0-100, higher = better)
    risk_score = float(np.clip(
        raw_p * 60 +
        (cgpa / 10) * 15 +
        INTERNSHIP_QUALITY[internship_quality]["score"] * 15 +
        (labor_demand / 1.5) * 10 +
        np.random.normal(0, 3),
        0, 100
    ))

    # Risk band
    if risk_score >= 75:   risk_band = "LOW"
    elif risk_score >= 50: risk_band = "MEDIUM"
    elif risk_score >= 25: risk_band = "HIGH"
    else:                  risk_band = "CRITICAL"

    # Generate realistic name
    first_names = ["Rahul","Priya","Arjun","Neha","Karan","Ananya","Vikram","Shreya",
                   "Aditya","Pooja","Rohan","Simran","Nikhil","Kavya","Siddharth"]
    last_names  = ["Sharma","Patel","Singh","Kumar","Gupta","Joshi","Verma","Shah",
                   "Yadav","Mishra","Nair","Reddy","Mehta","Chopra","Agarwal"]
    name = f"{random.choice(first_names)} {random.choice(last_names)}"

    # Institute name
    inst_names = {
        1: ["IIT Bombay", "IIT Delhi", "NIT Trichy", "BITS Pilani", "VIT Vellore"],
        2: ["PICT Pune", "SRM Chennai", "Manipal Jaipur", "Amity Noida", "MIT Aurangabad"],
        3: ["Sunrise College Patna", "Global Institute Bhopal", "City College Nagpur",
            "Rajasthan Tech Jaipur", "Eastern College Kolkata"]
    }
    institute = random.choice(inst_names[tier])

    return {
        # Identifiers
        "student_id":          f"STU{idx:04d}",
        "name":                name,
        "stream":              stream,
        "institute":           institute,
        "institute_tier":      tier,
        "city":                city,
        "grad_year":           2025,

        # Academic
        "cgpa":                round(cgpa, 2),
        "cgpa_sem_prev1":      round(sem_prev1_cgpa, 2),
        "cgpa_sem_prev2":      round(sem_prev2_cgpa, 2),
        "backlogs":            backlogs,
        "sem_gap_years":       sem_gap,

        # Internship
        "num_internships":     num_internships,
        "internship_quality":  internship_quality,
        "internship_label":    INTERNSHIP_QUALITY[internship_quality]["label"],

        # Skills
        "num_certifications":  num_certs,
        "has_github":          int(has_github),
        "has_linkedin":        int(has_linkedin),
        "job_portal_activity": round(job_portal_activity, 3),

        # Market
        "city_labor_demand":   round(labor_demand, 3),
        "sector_growth_index": round(sector_growth, 3),
        "primary_sector":      city_info["sector"],

        # Derived
        "pmscore":             round(pmscore, 2),

        # Targets (what we predict)
        "placement_prob_3mo":  round(placed_3mo, 4),
        "placement_prob_6mo":  round(placed_6mo, 4),
        "placement_prob_12mo": round(placed_12mo, 4),
        "is_placed_3mo":       is_placed_3mo,
        "is_placed_6mo":       is_placed_6mo,
        "is_placed_12mo":      is_placed_12mo,
        "expected_salary":     round(expected_salary, 0),
        "salary_p25":          round(salary_p25, 0),
        "salary_p75":          round(salary_p75, 0),

        # Risk output
        "risk_score":          round(risk_score, 2),
        "risk_band":           risk_band,
    }


def main():
    print("Generating 1,000 synthetic student records...")
    students = [generate_student(i) for i in range(1, 1001)]
    df = pd.DataFrame(students)

    # Save CSV
    df.to_csv("students.csv", index=False)
    print(f"Saved students.csv — {len(df)} rows, {len(df.columns)} columns")

    # Distribution summary
    print("\n--- Risk Band Distribution ---")
    print(df["risk_band"].value_counts())
    print("\n--- Institute Tier Distribution ---")
    print(df["institute_tier"].value_counts())
    print("\n--- Avg Placement Probabilities ---")
    print(f"  3-month:  {df['placement_prob_3mo'].mean():.1%}")
    print(f"  6-month:  {df['placement_prob_6mo'].mean():.1%}")
    print(f"  12-month: {df['placement_prob_12mo'].mean():.1%}")
    print(f"\n  Avg risk score: {df['risk_score'].mean():.1f}/100")
    print(f"  Avg expected salary: ₹{df['expected_salary'].mean():,.0f}")

    # Feature schema
    feature_cols = [
        "cgpa", "cgpa_sem_prev1", "cgpa_sem_prev2", "backlogs", "sem_gap_years",
        "num_internships", "internship_quality", "num_certifications",
        "has_github", "has_linkedin", "job_portal_activity",
        "city_labor_demand", "sector_growth_index", "institute_tier"
    ]
    schema = {
        "feature_columns": feature_cols,
        "target_3mo":  "is_placed_3mo",
        "target_6mo":  "is_placed_6mo",
        "target_12mo": "is_placed_12mo",
        "salary_target": "expected_salary",
        "generated_at": datetime.now().isoformat(),
        "n_records": len(df)
    }
    with open("feature_schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    print("\nSaved feature_schema.json")
    print("\nDone!")


if __name__ == "__main__":
    main()
