import React, { useRef, useEffect, useState } from 'react'
import { useStore } from './store/useStore'
import ImportScreen    from './components/ImportScreen'
import TimelineCanvas  from './components/Timeline/TimelineCanvas'
import PlaybackControls from './components/Timeline/PlaybackControls'
import PhaseBar        from './components/PhaseBar'
import EventDetail     from './components/EventDetail'
import NarrationPanel  from './components/NarrationPanel'
import StatsBar        from './components/StatsBar'
import TopBar          from './components/TopBar'

export default function App() {
  const { view } = useStore()
  const canvasRef = useRef(null)
  const [canvasSize, setCanvasSize] = useState({ w: 900, h: 400 })

  useEffect(() => {
    if (!canvasRef.current) return
    const obs = new ResizeObserver(([entry]) => {
      setCanvasSize({
        w: entry.contentRect.width,
        h: entry.contentRect.height,
      })
    })
    obs.observe(canvasRef.current)
    return () => obs.disconnect()
  }, [])

  if (view === 'import') {
    return (
      <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
        <TopBar />
        <div className="flex-1 overflow-hidden">
          <ImportScreen />
        </div>
      </div>
    )
  }

  if (view === 'narration') {
    return (
      <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
        <TopBar />
        <div className="flex-1 overflow-hidden p-4">
          <NarrationPanel />
        </div>
      </div>
    )
  }

  // ── Timeline view ──────────────────────────────────────────────────────────────
  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      <TopBar />

      {/* Stats row */}
      <div className="flex items-center gap-3 px-4 pt-3 pb-2 shrink-0 flex-wrap">
        <StatsBar />
      </div>

      {/* Phase filter bar */}
      <div className="px-4 pb-2 shrink-0">
        <PhaseBar />
      </div>

      {/* Main area: canvas left, detail right */}
      <div className="flex-1 flex gap-3 px-4 pb-4 overflow-hidden min-h-0">

        {/* Timeline canvas */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <div ref={canvasRef} className="flex-1 rounded-xl overflow-hidden"
               style={{ background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)' }}>
            <TimelineCanvas width={canvasSize.w} height={canvasSize.h} />
          </div>
          <PlaybackControls />
        </div>

        {/* Right panel: event detail */}
        <div className="w-80 shrink-0 overflow-hidden">
          <EventDetail />
          {!useStore.getState().selectedEvent && <PhaseHint />}
        </div>
      </div>
    </div>
  )
}

function PhaseHint() {
  const { phases, phaseColor } = useStore()
  if (!phases.length) return null

  return (
    <div className="rounded-xl p-4 space-y-3"
         style={{ background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)' }}>
      <p className="text-xs uppercase tracking-widest"
         style={{ color: 'var(--text-muted)' }}>
        Attack phases detected
      </p>
      {phases.map(ph => {
        const col = phaseColor(ph.phase_name)
        return (
          <div key={ph.phase_name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ background: col }} />
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {ph.display_name}
              </span>
            </div>
            <span className="mono text-xs" style={{ color: 'var(--text-muted)' }}>
              {ph.event_count}
            </span>
          </div>
        )
      })}
      <p className="text-xs pt-1" style={{ color: 'var(--text-muted)' }}>
        Click any dot on the timeline to inspect an event.
      </p>
    </div>
  )
}
