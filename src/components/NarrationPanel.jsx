import React from 'react'
import { Sparkles, ChevronRight, FileText, Loader, Clock } from 'lucide-react'
import { useStore } from '../store/useStore'

export default function NarrationPanel() {
  const {
    phases, narrations, narratingPhase, narratePhase,
    executiveSummary, generateSummary, generatingSummary,
    phaseColor, investigation,
  } = useStore()

  return (
    <div className="h-full flex flex-col narration-panel"
         style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 12 }}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3"
           style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="flex items-center gap-2">
          <Sparkles size={15} style={{ color: 'var(--accent)' }} />
          <span className="font-bold text-sm tracking-wide uppercase"
                style={{ color: 'var(--text-primary)' }}>
            Narration
          </span>
        </div>
        <span className="text-xs px-2 py-0.5 rounded mono"
              style={{ background: 'rgba(251,191,36,.1)', color: '#fbbf24',
                       border: '1px solid rgba(251,191,36,.2)' }}>
          Ollama pending
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">

        {/* Ollama notice */}
        <div className="rounded-lg p-3 flex items-start gap-3"
             style={{ background: 'rgba(56,189,248,.05)',
                      border: '1px solid rgba(56,189,248,.15)' }}>
          <Clock size={14} style={{ color: 'var(--accent)', marginTop: 1, flexShrink: 0 }} />
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            Ollama integration is next on the roadmap. For now, narrations use
            rule-based templates derived from detected techniques and event counts.
            Pull <span className="mono" style={{ color: 'var(--accent)' }}>llama3.1:8b</span> to
            unlock full AI analysis.
          </p>
        </div>

        {/* Executive Summary */}
        <div className="rounded-lg p-3 space-y-2"
             style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <FileText size={12} style={{ color: 'var(--accent)' }} />
              <span className="text-xs font-bold uppercase tracking-widest"
                    style={{ color: 'var(--accent)' }}>
                Executive Summary
              </span>
            </div>
            <button
              onClick={generateSummary}
              disabled={generatingSummary || !investigation}
              className="text-xs px-2.5 py-1 rounded transition-colors font-semibold"
              style={{
                background: generatingSummary ? 'var(--border-subtle)' : 'var(--accent)',
                color:      generatingSummary ? 'var(--text-muted)' : '#000',
                cursor:     generatingSummary ? 'wait' : 'pointer',
              }}
            >
              {generatingSummary ? 'Generating…' : 'Generate'}
            </button>
          </div>
          {executiveSummary ? (
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {executiveSummary}
            </p>
          ) : (
            <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>
              Generates a template-based incident summary from detected phases and techniques.
            </p>
          )}
        </div>

        {/* Per-phase */}
        <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
          Phase Narrations
        </p>

        {phases.map(ph => {
          const col        = phaseColor(ph.phase_name)
          const text       = narrations[ph.phase_name]
          const inProgress = narratingPhase === ph.phase_name

          return (
            <div key={ph.phase_name} className="rounded-lg p-3 space-y-2"
                 style={{ background: 'var(--bg-elevated)', border: `1px solid ${col}33` }}>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: col }} />
                  <span className="text-xs font-bold" style={{ color: col }}>
                    {ph.display_name}
                  </span>
                  <span className="mono text-xs" style={{ color: 'var(--text-muted)' }}>
                    {ph.event_count} events
                  </span>
                </div>
                <button
                  onClick={() => narratePhase(ph.phase_name)}
                  disabled={!!narratingPhase}
                  className="flex items-center gap-1 text-xs px-2 py-0.5 rounded transition-colors"
                  style={{
                    color:      narratingPhase ? 'var(--text-muted)' : col,
                    border:     `1px solid ${col}55`,
                    background: inProgress ? col + '15' : 'transparent',
                    cursor:     narratingPhase ? 'wait' : 'pointer',
                  }}
                >
                  {inProgress
                    ? <><Loader size={10} className="animate-spin" /> Thinking…</>
                    : <><ChevronRight size={10} /> Narrate</>}
                </button>
              </div>

              {ph.key_techniques?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {ph.key_techniques.slice(0, 5).map(t => (
                    <span key={t} className="mono text-xs px-1.5 py-0.5 rounded"
                          style={{ background: col+'18', color: col, border: `1px solid ${col}33` }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {text ? (
                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {text}
                </p>
              ) : (
                <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>
                  Click Narrate for a template-based phase summary.
                </p>
              )}
            </div>
          )
        })}

        {!phases.length && (
          <p className="text-xs text-center py-8" style={{ color: 'var(--text-muted)' }}>
            Import a log file to begin.
          </p>
        )}
      </div>
    </div>
  )
}
