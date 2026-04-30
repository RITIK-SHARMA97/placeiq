#!/bin/bash
# PlaceIQ — One-Command Setup
# Usage: bash setup.sh

set -e
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   PlaceIQ — Setup & Launch           ║"
echo "║   TenzorX 2026 National AI Hackathon ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. Python deps
echo "▶ Installing Python dependencies..."
pip install -r requirements.txt -q

# 2. Generate dataset
echo "▶ Generating synthetic dataset (1,000 students)..."
cd data && python generate_dataset.py && cd ..

# 3. Train models
echo "▶ Training ML models (XGBoost + SHAP)..."
cd ml && python train_model.py && cd ..

# 4. Install frontend deps
echo "▶ Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

echo ""
echo "✅  Setup complete!"
echo ""
echo "  Start backend:   cd backend && uvicorn main:app --reload"
echo "  Start frontend:  cd frontend && npm run dev"
echo "  API docs:        http://localhost:8000/docs"
echo "  Dashboard:       http://localhost:3000"
echo ""
echo "  Or use Docker:   docker-compose up"
echo ""
