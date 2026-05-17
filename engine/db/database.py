"""
SQLite database layer for Incident Replay.
Single-file, no ORM - fast to iterate on during a sprint.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "incident_replay.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS investigations (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            source_file TEXT,
            created_at  INTEGER,
            total_events INTEGER DEFAULT 0,
            time_start  INTEGER,
            time_end    INTEGER,
            executive_summary TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            investigation_id  TEXT NOT NULL,
            sysmon_event_id   INTEGER,
            timestamp         INTEGER NOT NULL,
            event_type        TEXT,
            phase             TEXT DEFAULT 'unknown',
            suspicion_score   REAL DEFAULT 0,
            ttp_codes         TEXT DEFAULT '',
            summary           TEXT,
            normalized        TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_events_inv   ON events(investigation_id);
        CREATE INDEX IF NOT EXISTS idx_events_ts    ON events(investigation_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_phase ON events(investigation_id, phase);

        CREATE TABLE IF NOT EXISTS attack_phases (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            investigation_id TEXT,
            phase_name       TEXT,
            display_name     TEXT,
            start_ts         INTEGER,
            end_ts           INTEGER,
            event_count      INTEGER DEFAULT 0,
            key_techniques   TEXT DEFAULT '',
            ai_narration     TEXT,
            confidence       REAL DEFAULT 0
        );
        """)


# Investigations ────────────────────────────────────────────────────────────────

def create_investigation(inv_id, name, source_file, created_at):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO investigations (id,name,source_file,created_at) VALUES (?,?,?,?)",
            (inv_id, name, source_file, created_at)
        )

def update_investigation_stats(inv_id, total, start_ts, end_ts):
    with get_conn() as conn:
        conn.execute(
            "UPDATE investigations SET total_events=?,time_start=?,time_end=? WHERE id=?",
            (total, start_ts, end_ts, inv_id)
        )

def update_executive_summary(inv_id, summary):
    with get_conn() as conn:
        conn.execute("UPDATE investigations SET executive_summary=? WHERE id=?", (summary, inv_id))

def get_investigation(inv_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM investigations WHERE id=?", (inv_id,)).fetchone()
    return dict(row) if row else None

def list_investigations():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM investigations ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


# Events ────────────────────────────────────────────────────────────────────────

def insert_events_bulk(events):
    if not events:
        return
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO events
               (investigation_id,sysmon_event_id,timestamp,event_type,
                phase,suspicion_score,ttp_codes,summary,normalized)
               VALUES (:investigation_id,:sysmon_event_id,:timestamp,:event_type,
                       :phase,:suspicion_score,:ttp_codes,:summary,:normalized)""",
            events
        )

def get_events(inv_id, phase=None, min_score=0, limit=5000, offset=0):
    with get_conn() as conn:
        if phase:
            rows = conn.execute(
                """SELECT * FROM events WHERE investigation_id=? AND phase=?
                   AND suspicion_score>=? ORDER BY timestamp ASC LIMIT ? OFFSET ?""",
                (inv_id, phase, min_score, limit, offset)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM events WHERE investigation_id=?
                   AND suspicion_score>=? ORDER BY timestamp ASC LIMIT ? OFFSET ?""",
                (inv_id, min_score, limit, offset)
            ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d['normalized'] = json.loads(d['normalized']) if d['normalized'] else {}
        d['ttp_codes'] = [t for t in d['ttp_codes'].split(',') if t]
        result.append(d)
    return result

def get_event_count(inv_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM events WHERE investigation_id=?", (inv_id,)
        ).fetchone()[0]


# Attack Phases ─────────────────────────────────────────────────────────────────

def insert_phases(phases):
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO attack_phases
               (investigation_id,phase_name,display_name,start_ts,end_ts,
                event_count,key_techniques,confidence)
               VALUES (:investigation_id,:phase_name,:display_name,:start_ts,:end_ts,
                       :event_count,:key_techniques,:confidence)""",
            phases
        )

def get_phases(inv_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM attack_phases WHERE investigation_id=? ORDER BY start_ts ASC",
            (inv_id,)
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d['key_techniques'] = [t for t in d['key_techniques'].split(',') if t]
        result.append(d)
    return result

def update_phase_narration(inv_id, phase_name, narration):
    with get_conn() as conn:
        conn.execute(
            "UPDATE attack_phases SET ai_narration=? WHERE investigation_id=? AND phase_name=?",
            (narration, inv_id, phase_name)
        )
