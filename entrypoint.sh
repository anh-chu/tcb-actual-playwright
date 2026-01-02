#!/bin/bash
set -e

# Start Xvfb
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 &
msg_xvfb=$!

# Wait for Xvfb
echo "Waiting for Xvfb..."
until xdpyinfo -display :99 >/dev/null 2>&1; do sleep 0.2; done

# Start FastAPI App
echo "Starting FastAPI App..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
