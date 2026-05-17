#!/bin/bash
# Start the Incident Replay backend
cd "$(dirname "$0")/.."
echo "[*] Starting Incident Replay backend on http://localhost:8000"
python -m uvicorn engine.main:app --reload --port 8000 --log-level warning
