# ⚔️ INCIDENT REPLAY

> Drop Sysmon/EVTX logs. Watch the attack reconstruct itself as an animated timeline.

A local-first DFIR tool that turns raw Windows event logs into a cinematic attack timeline
with MITRE ATT&CK mapping, phase clustering, and narration.

---

## 🚀 Setup (2 terminals, 5 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- On Windows PowerShell, use `Activate.ps1` to enter the virtual environment.

### Terminal 1 — Python Backend

```bash
cd incident-replay

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Make sure pip can resolve prebuilt wheels cleanly
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Generate a built-in sample attack log to test with
python scripts/generate_sample.py > data/sample_attack.xml

# Start API server
python -m uvicorn engine.main:app --reload --port 8000
```

### Terminal 2 — React Frontend

```bash
cd incident-replay

npm install
npm run dev
```

Open **http://localhost:5173**

Drag `data/sample_attack.xml` onto the drop zone → watch the attack reconstruct.

---

## 🗂️ Project Structure

```
incident-replay/
├── engine/                          # Python FastAPI backend
│   ├── main.py                      # All API routes
│   ├── db/
│   │   └── database.py              # SQLite layer (no ORM)
│   ├── parsers/
│   │   └── sysmon_parser.py         # Sysmon XML + EVTX parser
│   ├── intelligence/
│   │   ├── ttp_detector.py          # 35+ ATT&CK signatures
│   │   └── phase_clusterer.py       # Kill-chain phase grouping
│   └── ai/
│       └── narrator.py              # Template narration (Ollama coming soon)
│
├── src/                             # React frontend
│   ├── App.jsx                      # Root layout + view router
│   ├── store/useStore.js            # Zustand global state
│   ├── index.css                    # Global styles + CSS vars
│   └── components/
│       ├── ImportScreen.jsx         # Drag-and-drop import wizard
│       ├── TopBar.jsx               # Navigation bar
│       ├── StatsBar.jsx             # Live event/phase counters
│       ├── PhaseBar.jsx             # Phase filter chips
│       ├── EventDetail.jsx          # Click-to-inspect event panel
│       ├── NarrationPanel.jsx       # Phase narration + exec summary
│       └── Timeline/
│           ├── TimelineCanvas.jsx   # D3 animated swimlane timeline
│           └── PlaybackControls.jsx # Scrubber + speed controls
│
├── scripts/
│   └── generate_sample.py           # Synthetic 14-event attack generator
├── data/                            # DB + log files land here
├── requirements.txt
├── package.json
└── vite.config.js
```

---

## 🔍 Supported Log Formats

| Format | Notes |
|--------|-------|
| Sysmon XML | Single `<Event>` or `<Events>` wrapper |
| Windows EVTX | Binary format via python-evtx |

**Real test data:** https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES

---

## 🗺️ ATT&CK Phases Detected

`Initial Access` → `Execution` → `Persistence` → `Privilege Escalation` →
`Defense Evasion` → `Credential Access` → `Discovery` → `Lateral Movement` →
`Collection` → `Command & Control` → `Exfiltration` → `Impact`

---

## 🤖 AI Narration (Coming Soon)

Ollama integration is stubbed and ready. Once you run:
```bash
ollama pull llama3.1:8b
```
Swap the narrator stub in `engine/ai/narrator.py` for the Ollama version.
The API endpoints `/api/investigations/{id}/narrate/{phase}` and
`/api/investigations/{id}/summary` are already wired up and waiting.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/import` | Upload + parse a log file |
| GET | `/api/investigations` | List all investigations |
| GET | `/api/investigations/{id}` | Investigation metadata |
| GET | `/api/investigations/{id}/events` | Paginated events (filter by phase, score) |
| GET | `/api/investigations/{id}/phases` | Phase breakdown |
| POST | `/api/investigations/{id}/narrate/{phase}` | Generate phase narration |
| POST | `/api/investigations/{id}/summary` | Generate executive summary |
