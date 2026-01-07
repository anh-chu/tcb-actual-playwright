#!/bin/bash
set -e

# Start FastAPI App
# No need for Xvfb - Playwright's headless mode works without X11
echo "Starting FastAPI App..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
