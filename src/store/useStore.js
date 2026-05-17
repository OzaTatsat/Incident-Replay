import { create } from 'zustand'

const PHASE_COLORS = {
  reconnaissance:       '#7fa1c3',
  initial_access:       '#d4a373',
  execution:            '#e29578',
  persistence:          '#a594f9',
  privilege_escalation: '#e5989b',
  defense_evasion:      '#83c5be',
  credential_access:    '#e9c46a',
  discovery:            '#90e0ef',
  lateral_movement:     '#48cae4',
  collection:           '#bde0fe',
  command_and_control:  '#ffb4a2',
  exfiltration:         '#e56b6f',
  impact:               '#b56576',
  unknown:              '#9ca3af',
}

export const useStore = create((set, get) => ({
  // ── View state ──────────────────────────────────────────────────────────────
  view: 'import',  // 'import' | 'timeline' | 'narration'
  setView: (v) => set({ view: v }),

  // ── Investigation ───────────────────────────────────────────────────────────
  investigation: null,
  events:        [],
  phases:        [],
  loading:       false,
  importError:   null,

  setLoading:    (v) => set({ loading: v }),
  setImportError:(v) => set({ importError: v }),

  setInvestigation: (inv) => set({ investigation: inv }),
  setEvents:        (evs) => set({ events: evs }),
  setPhases:        (phs) => set({ phases: phs }),

  // ── Playback ─────────────────────────────────────────────────────────────────
  playhead:       0,      // 0–1 normalized position
  isPlaying:      false,
  playbackSpeed:  1,      // 1 | 5 | 10 | 30

  setPlayhead:      (v) => set({ playhead: Math.max(0, Math.min(1, v)) }),
  setIsPlaying:     (v) => set({ isPlaying: v }),
  setPlaybackSpeed: (v) => set({ playbackSpeed: v }),

  // ── Selected event ───────────────────────────────────────────────────────────
  selectedEvent: null,
  setSelectedEvent: (ev) => set({ selectedEvent: ev }),

  // ── Filter ───────────────────────────────────────────────────────────────────
  activePhaseFilter: null,
  setActivePhaseFilter: (p) => set({
    activePhaseFilter: get().activePhaseFilter === p ? null : p
  }),

  // ── Narration ────────────────────────────────────────────────────────────────
  narrations:         {},   // { phase_name: string }
  executiveSummary:   null,
  narratingPhase:     null,
  generatingSummary:  false,

  setNarration:       (phase, text) => set(s => ({
    narrations: { ...s.narrations, [phase]: text }
  })),
  setExecutiveSummary:(v) => set({ executiveSummary: v }),
  setNarratingPhase:  (v) => set({ narratingPhase: v }),
  setGeneratingSummary:(v) => set({ generatingSummary: v }),

  // ── Derived helpers ──────────────────────────────────────────────────────────
  phaseColor: (name) => PHASE_COLORS[name] || '#475569',
  PHASE_COLORS,

  // Visible events based on playhead
  visibleEvents: () => {
    const { events, playhead, activePhaseFilter } = get()
    if (!events.length) return []
    const inv  = get().investigation
    const tMin = inv?.time_start || 0
    const tMax = inv?.time_end   || 1
    const tCut = tMin + playhead * (tMax - tMin)
    return events.filter(ev =>
      ev.timestamp <= tCut &&
      (!activePhaseFilter || ev.phase === activePhaseFilter)
    )
  },

  // API actions ─────────────────────────────────────────────────────────────────
  importFile: async (file) => {
    set({ loading: true, importError: null })
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res  = await fetch('/api/import', { method: 'POST', body: fd })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(err.detail || 'Upload failed')
      }
      const data = await res.json()

      // Fetch full details
      const [invRes, evRes, phRes] = await Promise.all([
        fetch(`/api/investigations/${data.investigation_id}`),
        fetch(`/api/investigations/${data.investigation_id}/events?limit=5000`),
        fetch(`/api/investigations/${data.investigation_id}/phases`),
      ])
      const inv    = await invRes.json()
      const evData = await evRes.json()
      const phData = await phRes.json()

      set({
        investigation: inv,
        events:        evData.events,
        phases:        phData.phases,
        playhead:      0,
        isPlaying:     false,
        selectedEvent: null,
        narrations:    {},
        executiveSummary: null,
        view: 'timeline',
        loading: false,
      })
    } catch (e) {
      set({ loading: false, importError: e.message })
    }
  },

  narratePhase: async (phaseName) => {
    const { investigation } = get()
    if (!investigation) return
    set({ narratingPhase: phaseName })
    try {
      const res = await fetch(
        `/api/investigations/${investigation.id}/narrate/${phaseName}`,
        { method: 'POST' }
      )
      const data = await res.json()
      get().setNarration(phaseName, data.narration)
    } catch (_) {}
    set({ narratingPhase: null })
  },

  generateSummary: async () => {
    const { investigation } = get()
    if (!investigation) return
    set({ generatingSummary: true })
    try {
      const res = await fetch(
        `/api/investigations/${investigation.id}/summary`,
        { method: 'POST' }
      )
      const data = await res.json()
      set({ executiveSummary: data.summary })
    } catch (_) {}
    set({ generatingSummary: false })
  },
}))
