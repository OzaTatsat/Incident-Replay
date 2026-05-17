import React from 'react'
import { Play, Pause, SkipBack, Gauge } from 'lucide-react'
import { useStore } from '../../store/useStore'

const SPEEDS = [1, 5, 10, 30]

export default function PlaybackControls() {
  const {
    isPlaying, setIsPlaying, playbackSpeed, setPlaybackSpeed,
    playhead, setPlayhead, events, investigation,
  } = useStore()

  const tMin = investigation?.time_start || 0
  const tMax = investigation?.time_end   || 1
  const current = new Date(tMin + playhead * (tMax - tMin))
  const timeStr = [
    String(current.getUTCHours()).padStart(2,'0'),
    String(current.getUTCMinutes()).padStart(2,'0'),
    String(current.getUTCSeconds()).padStart(2,'0'),
  ].join(':')

  const totalVisible = events.filter(e =>
    e.timestamp <= tMin + playhead * (tMax - tMin)
  ).length

  return (
    <div className="flex items-center gap-4 px-5 py-3 rounded-xl"
         style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>

      {/* Reset */}
      <button
        onClick={() => { setPlayhead(0); setIsPlaying(false) }}
        aria-label="Reset playback"
        title="Reset"
        className="p-1.5 rounded hover:bg-white/5 transition-colors focus-visible:ring-2"
      >
        <SkipBack size={15} style={{ color: 'var(--text-secondary)' }} />
      </button>

      {/* Play / Pause */}
      <button
        onClick={() => {
          if (playhead >= 1) setPlayhead(0)
          setIsPlaying(!isPlaying)
        }}
        aria-label={isPlaying ? "Pause playback" : "Play timeline"}
        title={isPlaying ? "Pause" : "Play"}
        disabled={!events.length}
        className="w-9 h-9 rounded-full flex items-center justify-center transition-all focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-offset-[#0d1117]"
        style={{
          background: events.length ? 'var(--accent)' : 'var(--border-subtle)',
          cursor: events.length ? 'pointer' : 'not-allowed',
        }}
      >
        {isPlaying
          ? <Pause  size={15} fill="#000" color="#000" />
          : <Play   size={15} fill="#000" color="#000" style={{ marginLeft: 2 }} />
        }
      </button>

      {/* Scrubber */}
      <input
        type="range" min={0} max={1000} step={1}
        value={Math.round(playhead * 1000)}
        onChange={e => { setPlayhead(e.target.value / 1000); setIsPlaying(false) }}
        aria-label="Timeline scrubber"
        disabled={!events.length}
        className="flex-1 h-1 rounded accent-sky-400 focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-offset-[#0d1117]"
        style={{ accentColor: 'var(--accent)', cursor: events.length ? 'pointer' : 'not-allowed' }}
      />

      {/* Timestamp */}
      <span className="mono text-xs w-24 text-right"
            style={{ color: 'var(--accent)' }}>
        {events.length ? timeStr + ' UTC' : '--:--:-- UTC'}
      </span>

      {/* Events count */}
      <span className="mono text-xs w-20 text-right"
            style={{ color: 'var(--text-muted)' }}>
        {totalVisible.toLocaleString()} evt
      </span>

      {/* Speed */}
      <div className="flex items-center gap-1">
        <Gauge size={12} style={{ color: 'var(--text-muted)' }} />
        <div className="flex gap-0.5" role="group" aria-label="Playback speed">
          {SPEEDS.map(s => (
            <button
              key={s}
              onClick={() => setPlaybackSpeed(s)}
              aria-label={`Speed ${s}x`}
              aria-pressed={playbackSpeed === s}
              className="px-2 py-0.5 rounded text-xs mono transition-colors focus-visible:ring-2 focus-visible:ring-inset"
              style={{
                background: playbackSpeed === s ? 'var(--accent)' : 'transparent',
                color:      playbackSpeed === s ? '#000' : 'var(--text-muted)',
                fontWeight: playbackSpeed === s ? 700 : 400,
              }}
            >
              {s}×
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
