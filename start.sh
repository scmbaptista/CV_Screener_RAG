#!/bin/bash

set -e

echo "=========================================="
echo "  CV Screener RAG - Startup"
echo "=========================================="

echo "  Check Python 3 Availability "
echo "=========================================="

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi


echo "  Install dependencies if needed "
echo "=========================================="
echo "Checking dependencies..."
pip install -q -r requirements.txt


echo "  Generate CVs if not present "
echo "=========================================="
if [ ! "$(ls -A data/cvs/*.pdf 2>/dev/null)" ]; then
    echo "Generating synthetic CV dataset..."
    python3 generate_cvs.py
fi


echo "  Starting backend"
echo "=========================================="
echo ""
echo "Open http://localhost:8000 in your browser"
echo "API docs: http://localhost:8000/docs"
echo "=========================================="
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
