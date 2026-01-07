#!/bin/bash
# Quick start script for local development

# Activate virtual environment
source venv/bin/activate

# Run the app
echo "Starting FastAPI server..."
echo "Access the app at: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000
