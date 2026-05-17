import React from 'react'
import { useStore } from '../store/useStore'

export default function PhaseBar() {
  const { phases, activePhaseFilter, setActivePhaseFilter, phaseColor } = useStore()
  if (!phases.length) return null

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs uppercase tracking-widest"
            style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
        Phases
      </span>
      {phases.map(ph => {
        const col     = phaseColor(ph.phase_name)
        const active  = activePhaseFilter === ph.phase_name
        return (
          <button
            key={ph.phase_name}
            onClick={() => setActivePhaseFilter(ph.phase_name)}
            className="phase-badge transition-all"
            style={{
              background: active ? col : 'transparent',
              color:      active ? '#000' : col,
              border:     `1px solid ${col}`,
              opacity:    activePhaseFilter && !active ? 0.4 : 1,
              cursor:     'pointer',
            }}
            title={`${ph.event_count} events`}
          >
            {ph.display_name}
            <span className="ml-1.5 opacity-60">{ph.event_count}</span>
          </button>
        )
      })}
      {activePhaseFilter && (
        <button
          onClick={() => setActivePhaseFilter(null)}
          className="text-xs px-2 py-0.5 rounded transition-colors hover:bg-white/5"
          style={{ color: 'var(--text-muted)' }}
        >
          ✕ clear
        </button>
      )}
    </div>
  )
}
