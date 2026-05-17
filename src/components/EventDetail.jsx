import React from 'react'
import { X, AlertTriangle, Cpu, Network, Database } from 'lucide-react'
import { useStore } from '../store/useStore'

const TTP_LINKS = (code) =>
  `https://attack.mitre.org/techniques/${code.replace('.','/')}/`

export default function EventDetail() {
  const { selectedEvent: ev, setSelectedEvent, phaseColor } = useStore()
  if (!ev) return null

  const col        = phaseColor(ev.phase)
  const score      = ev.suspicion_score || 0
  const scoreColor = score >= 80 ? '#ef4444' : score >= 50 ? '#f59e0b' : '#22c55e'
  const norm       = ev.normalized || {}

  const dt = new Date(ev.timestamp)
  const ts = [
    dt.getUTCFullYear(),
    String(dt.getUTCMonth()+1).padStart(2,'0'),
    String(dt.getUTCDate()).padStart(2,'0'),
  ].join('-') + ' ' + [
    String(dt.getUTCHours()).padStart(2,'0'),
    String(dt.getUTCMinutes()).padStart(2,'0'),
    String(dt.getUTCSeconds()).padStart(2,'0'),
  ].join(':') + ' UTC'

  return (
    <div className="rounded-xl overflow-hidden flex flex-col"
         style={{ background: 'var(--bg-elevated)',
                  border: `1px solid ${col}44`,
                  maxHeight: '100%' }}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3"
           style={{ background: col + '18', borderBottom: `1px solid ${col}33` }}>
        <div className="flex items-center gap-2">
          <EventIcon type={ev.event_type} col={col} />
          <span className="font-bold text-sm" style={{ color: col }}>
            {ev.event_type?.replace(/_/g,' ').toUpperCase()}
          </span>
          <span className="phase-badge" style={{ background: col+'22', color: col }}>
            {ev.phase?.replace(/_/g,' ')}
          </span>
        </div>
        <button onClick={() => setSelectedEvent(null)}
                aria-label="Close event details"
                title="Close"
                className="p-1 rounded hover:bg-black/10 transition-colors focus-visible:ring-2">
          <X size={14} style={{ color: 'var(--text-secondary)' }} />
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-4 text-sm">

        {/* Score + timestamp */}
        <div className="flex items-center justify-between">
          <span className="mono text-xs" style={{ color: 'var(--text-muted)' }}>{ts}</span>
          <div className="flex items-center gap-2">
            <AlertTriangle size={12} style={{ color: scoreColor }} />
            <span className="mono font-bold" style={{ color: scoreColor }}>
              {score.toFixed(0)} risk
            </span>
          </div>
        </div>

        {/* Summary */}
        {ev.summary && (
          <div className="px-3 py-2 rounded mono text-xs leading-relaxed"
               style={{ background: 'var(--bg-surface)',
                        color: 'var(--text-secondary)',
                        borderLeft: `3px solid ${col}` }}>
            {ev.summary}
          </div>
        )}

        {/* ATT&CK TTPs */}
        {ev.ttp_codes?.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-widest"
               style={{ color: 'var(--text-muted)' }}>ATT&CK Techniques</p>
            <div className="flex flex-wrap gap-1.5">
              {ev.ttp_codes.map(code => (
                <a key={code} href={TTP_LINKS(code)} target="_blank" rel="noreferrer"
                   className="phase-badge hover:opacity-80 transition-opacity"
                   style={{ background: col+'22', color: col,
                            border: `1px solid ${col}44`, cursor: 'pointer',
                            textDecoration: 'none' }}>
                  {code}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Normalised fields */}
        <NormFields norm={norm} type={ev.event_type} />

        {/* Sysmon Event ID */}
        {ev.sysmon_event_id && (
          <div className="flex items-center justify-between py-2"
               style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ color: 'var(--text-muted)' }}>Sysmon Event ID</span>
            <span className="mono" style={{ color: 'var(--text-secondary)' }}>
              {ev.sysmon_event_id}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function NormFields({ norm, type }) {
  const SHOW_FIELDS = {
    process_create:  ['image','parent_name','cmd','user','pid','integrity'],
    network_connect: ['image_name','dest_ip','dest_hostname','dest_port','protocol','user'],
    registry_set:    ['image_name','target_object','details','user'],
    registry_create: ['image_name','target_object','user'],
    process_access:  ['source_name','target_name','granted_access'],
    dns_query:       ['image_name','query_name','query_results'],
    file_create:     ['image_name','target_file','creation_utc'],
    create_remote_thread: ['source_name','target_name','start_address'],
  }
  const fields = SHOW_FIELDS[type] || Object.keys(norm).slice(0, 8)

  return (
    <div className="space-y-1">
      {fields.map(f => {
        const val = norm[f]
        if (!val) return null
        return (
          <div key={f} className="grid grid-cols-[120px_1fr] gap-2 py-1"
               style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <span className="mono text-xs truncate"
                  style={{ color: 'var(--text-muted)' }}>
              {f}
            </span>
            <span className="mono text-xs break-all"
                  style={{ color: 'var(--text-secondary)' }}>
              {String(val)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function EventIcon({ type, col }) {
  const size = 14
  if (type?.includes('network') || type?.includes('dns'))
    return <Network size={size} style={{ color: col }} />
  if (type?.includes('registry') || type?.includes('file'))
    return <Database size={size} style={{ color: col }} />
  return <Cpu size={size} style={{ color: col }} />
}
