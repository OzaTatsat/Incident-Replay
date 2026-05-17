"""
Incident Replay — FastAPI backend
Run: uvicorn engine.main:app --reload --port 8000
"""

from __future__ import annotations
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from engine.db.database import (
    init_db, create_investigation, update_investigation_stats,
    insert_events_bulk, insert_phases, get_investigation,
    list_investigations, get_events, get_phases,
    update_phase_narration, update_executive_summary
)
from engine.parsers.sysmon_parser import parse_file
from engine.intelligence.ttp_detector import detect_ttps, score_event
from engine.intelligence.phase_clusterer import assign_phase, cluster_phases
from engine.ai.narrator import narrate_phase, generate_summary

# ── App setup ───────────────────────────────────────────────────────────────────

app = FastAPI(title="Incident Replay", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()


# ── Health ───────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# ── Import ───────────────────────────────────────────────────────────────────────

@app.post("/api/import")
async def import_log(file: UploadFile = File(...)):
    """
    Accept a Sysmon XML or EVTX file, parse it, run TTP detection,
    phase clustering, and store everything in SQLite.
    Returns investigation ID + summary stats.
    """
    suffix = Path(file.filename or "upload.xml").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        raw_events = parse_file(tmp_path)
    except Exception as exc:
        raise HTTPException(400, f"Failed to parse file: {exc}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not raw_events:
        raise HTTPException(400, "No parseable Sysmon events found in this file.")

    # Create investigation record
    inv_id     = str(uuid.uuid4())
    inv_name   = Path(file.filename or "upload").stem
    created_at = int(datetime.now(timezone.utc).timestamp() * 1000)
    create_investigation(inv_id, inv_name, file.filename, created_at)

    # Enrich events with TTP detection + phase assignment
    db_events = []
    for ev in raw_events:
        ttps   = detect_ttps(ev)
        score  = score_event(ev, ttps)
        phase  = assign_phase(ev, ttps)
        codes  = ",".join(t["code"] for t in ttps)

        db_events.append({
            "investigation_id": inv_id,
            "sysmon_event_id":  ev.get("sysmon_event_id"),
            "timestamp":        ev["timestamp"],
            "event_type":       ev.get("event_type", "unknown"),
            "phase":            phase,
            "suspicion_score":  round(score, 1),
            "ttp_codes":        codes,
            "summary":          ev.get("summary", ""),
            "normalized":       json.dumps({
                k: v for k, v in ev.items()
                if k not in ("raw_fields",)
            }),
        })

    insert_events_bulk(db_events)

    # Phase clustering
    phases = cluster_phases(db_events, inv_id)
    insert_phases(phases)

    # Update investigation stats
    timestamps  = [e["timestamp"] for e in db_events]
    update_investigation_stats(inv_id, len(db_events), min(timestamps), max(timestamps))

    # Build event type breakdown
    type_counts: dict[str, int] = {}
    for ev in db_events:
        t = ev["event_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # Phase breakdown
    phase_names = [p["phase_name"] for p in phases]

    return {
        "investigation_id":  inv_id,
        "name":              inv_name,
        "total_events":      len(db_events),
        "time_range": {
            "start": min(timestamps),
            "end":   max(timestamps),
        },
        "phases_detected":   phase_names,
        "event_type_counts": type_counts,
    }


# ── Investigations ───────────────────────────────────────────────────────────────

@app.get("/api/investigations")
def get_investigations():
    return list_investigations()


@app.get("/api/investigations/{inv_id}")
def get_inv(inv_id: str):
    inv = get_investigation(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return inv


# ── Events ───────────────────────────────────────────────────────────────────────

@app.get("/api/investigations/{inv_id}/events")
def get_inv_events(
    inv_id:    str,
    phase:     str | None = None,
    min_score: float = 0,
    limit:     int = 5000,
    offset:    int = 0,
):
    inv = get_investigation(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    events = get_events(inv_id, phase=phase, min_score=min_score,
                        limit=limit, offset=offset)
    return {"events": events, "total": len(events)}


# ── Phases ───────────────────────────────────────────────────────────────────────

@app.get("/api/investigations/{inv_id}/phases")
def get_inv_phases(inv_id: str):
    inv = get_investigation(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return {"phases": get_phases(inv_id)}


# ── AI Narration ─────────────────────────────────────────────────────────────────

@app.post("/api/investigations/{inv_id}/narrate/{phase_name}")
async def narrate(inv_id: str, phase_name: str):
    inv = get_investigation(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")

    phase_events  = get_events(inv_id, phase=phase_name, limit=200)
    all_phases    = get_phases(inv_id)
    phase_meta    = next((p for p in all_phases if p["phase_name"] == phase_name), None)

    if not phase_events:
        raise HTTPException(404, f"No events found for phase '{phase_name}'")

    display = phase_meta["display_name"] if phase_meta else phase_name.replace("_", " ").title()
    techniques = phase_meta["key_techniques"] if phase_meta else []

    narration = await narrate_phase(phase_name, display, phase_events, techniques)
    update_phase_narration(inv_id, phase_name, narration)
    return {"phase": phase_name, "narration": narration}


# ── Executive Summary ─────────────────────────────────────────────────────────────

@app.post("/api/investigations/{inv_id}/summary")
async def generate_inv_summary(inv_id: str):
    inv = get_investigation(inv_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")

    phases = get_phases(inv_id)
    duration_ms = (inv.get("time_end") or 0) - (inv.get("time_start") or 0)
    duration_min = duration_ms / 60_000

    summary = await generate_summary(
        inv["name"], phases, inv.get("total_events", 0), duration_min
    )
    update_executive_summary(inv_id, summary)
    return {"summary": summary}
