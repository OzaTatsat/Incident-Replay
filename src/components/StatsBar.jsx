import React from 'react'
import { Shield, AlertTriangle, Activity, Clock } from 'lucide-react'
import { useStore } from '../store/useStore'

export default function StatsBar() {
  const { investigation, events, phases, playhead } = useStore()
  if (!investigation) return null

  const tMin = investigation.time_start || 0
  const tMax = investigation.time_end   || 1
  const cutoff = tMin + playhead * (tMax - tMin)

  const visibleCount = events.filter(e => e.timestamp <= cutoff).length
  const highRisk     = events.filter(e => e.timestamp <= cutoff && e.suspicion_score >= 70).length
  const durationMs   = tMax - tMin
  const durationMin  = (durationMs / 60000).toFixed(0)

  const uniquePhases = [...new Set(
    events.filter(e => e.timestamp <= cutoff).map(e => e.phase)
  )].filter(p => p !== 'unknown').length

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {[
        {
          icon: Activity,
          label: 'Events',
          value: visibleCount.toLocaleString(),
          sub: `/ ${events.length.toLocaleString()}`,
          col: 'var(--accent)',
        },
        {
          icon: AlertTriangle,
          label: 'High Risk',
          value: highRisk,
          sub: 'score ≥70',
          col: highRisk > 0 ? '#ef4444' : 'var(--text-muted)',
        },
        {
          icon: Shield,
          label: 'Phases',
          value: uniquePhases,
          sub: `of ${phases.length}`,
          col: '#a855f7',
        },
        {
          icon: Clock,
          label: 'Duration',
          value: durationMin + 'm',
          sub: 'total span',
          col: 'var(--text-secondary)',
        },
      ].map(({ icon: Icon, label, value, sub, col }) => (
        <div key={label} className="flex items-center gap-2.5 px-4 py-2 rounded-lg"
             style={{ background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)' }}>
          <Icon size={14} style={{ color: col }} />
          <div>
            <div className="flex items-baseline gap-1">
              <span className="mono font-bold text-sm" style={{ color: col }}>
                {value}
              </span>
              <span className="mono text-xs" style={{ color: 'var(--text-muted)' }}>
                {sub}
              </span>
            </div>
            <p className="text-xs uppercase tracking-widest"
               style={{ color: 'var(--text-muted)', lineHeight: 1 }}>
              {label}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
