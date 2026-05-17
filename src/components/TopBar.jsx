import React from 'react'
import { Shield, FolderOpen, Activity, MessageSquare } from 'lucide-react'
import { useStore } from '../store/useStore'

export default function TopBar() {
  const { view, setView, investigation } = useStore()

  const resetAll = () => {
    useStore.setState({
      view: 'import', investigation: null, events: [], phases: [],
      selectedEvent: null, narrations: {}, executiveSummary: null,
      playhead: 0, isPlaying: false, activePhaseFilter: null,
    })
  }

  return (
    <div className="flex items-center justify-between px-5 py-3 shrink-0"
         style={{ borderBottom: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)' }}>

      {/* Brand */}
      <div className="flex items-center gap-2.5 min-w-0">
        <Shield size={18} style={{ color: 'var(--accent)' }} />
        <span className="font-bold tracking-[.2em] text-sm uppercase shrink-0"
              style={{ color: 'var(--text-primary)' }}>
          INCIDENT REPLAY
        </span>
        {investigation && (
          <>
            <span className="shrink-0" style={{ color: 'var(--border-strong)' }}>/</span>
            <span className="text-sm truncate max-w-xs" style={{ color: 'var(--text-secondary)' }}>
              {investigation.name}
            </span>
          </>
        )}
      </div>

      {/* Nav */}
      <div className="flex items-center gap-1">
        {investigation && (
          <>
            <NavBtn
              active={view === 'timeline'}
              onClick={() => setView('timeline')}
              icon={<Activity size={12} />}
              label="Timeline"
            />
            <NavBtn
              active={view === 'narration'}
              onClick={() => setView('narration')}
              icon={<MessageSquare size={12} />}
              label="AI Narration"
            />
            <button
              onClick={resetAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs
                         transition-colors hover:bg-black/5 ml-2"
              style={{ color: 'var(--text-muted)' }}
            >
              <FolderOpen size={13} /> New
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function NavBtn({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs
                 font-semibold transition-colors uppercase tracking-wider"
      style={{
        background: active ? 'var(--accent)' : 'transparent',
        color:      active ? '#ffffff' : 'var(--text-muted)',
      }}
    >
      {icon}
      {label}
    </button>
  )
}
