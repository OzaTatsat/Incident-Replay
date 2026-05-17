import React, { useCallback, useState } from 'react'
import { Upload, Shield, Zap, FileText, AlertCircle } from 'lucide-react'
import { useStore } from '../store/useStore'

const SUPPORTED = ['Sysmon XML', 'EVTX', 'Concatenated Event XML']

export default function ImportScreen() {
  const [dragging, setDragging] = useState(false)
  const { loading, importError, importFile } = useStore()

  const handle = useCallback((file) => {
    if (!file) return
    importFile(file)
  }, [importFile])

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handle(e.dataTransfer.files[0])
  }

  const onInput = (e) => handle(e.target.files[0])

  return (
    <div className="h-full flex flex-col items-center justify-center gap-8 p-8"
         style={{ background: 'var(--bg-primary)' }}>

      {/* Logo / Title */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Shield size={32} style={{ color: 'var(--accent)' }} />
          <h1 className="text-4xl font-bold tracking-widest uppercase"
              style={{ color: 'var(--text-primary)', letterSpacing: '0.15em' }}>
            INCIDENT REPLAY
          </h1>
        </div>
        <p className="text-sm tracking-widest uppercase"
           style={{ color: 'var(--text-muted)' }}>
          Attack Chain Reconstruction &amp; Animated Playback
        </p>
      </div>

      {/* Drop Zone */}
      <label
        className={`drop-zone w-full max-w-xl rounded-xl p-12 flex flex-col
                    items-center justify-center gap-5 cursor-pointer
                    ${dragging ? 'active' : ''}`}
        style={{ background: 'var(--bg-surface)' }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {loading ? (
          <LoadingState />
        ) : (
          <>
            <Upload size={40} style={{ color: 'var(--accent)', opacity: dragging ? 1 : 0.6 }} />
            <div className="text-center space-y-1">
              <p className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Drop your log file here
              </p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                or click to browse
              </p>
            </div>
            <div className="flex gap-2 flex-wrap justify-center">
              {SUPPORTED.map(f => (
                <span key={f} className="phase-badge"
                      style={{ background: 'var(--bg-elevated)',
                               color: 'var(--text-secondary)',
                               border: '1px solid var(--border-subtle)' }}>
                  {f}
                </span>
              ))}
            </div>
          </>
        )}
        <input type="file" className="hidden" accept=".xml,.evtx,.log"
               onChange={onInput} disabled={loading} />
      </label>

      {/* Error */}
      {importError && (
        <div className="flex items-center gap-3 px-5 py-3 rounded-lg w-full max-w-xl"
             style={{ background: 'rgba(220,38,38,.1)',
                      border: '1px solid rgba(220,38,38,.3)' }}>
          <AlertCircle size={16} className="text-red-400 shrink-0" />
          <p className="text-sm text-red-400 mono">{importError}</p>
        </div>
      )}

      {/* Sample hint */}
      <p className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
        Try samples from{' '}
        <span className="mono" style={{ color: 'var(--accent)' }}>
          github.com/sbousseaden/EVTX-ATTACK-SAMPLES
        </span>
      </p>

      {/* Feature chips */}
      <div className="flex gap-6 text-xs" style={{ color: 'var(--text-muted)' }}>
        {[
          [Zap, 'TTP Detection'],
          [Shield, 'ATT&CK Mapping'],
          [FileText, 'AI Narration'],
        ].map(([Icon, label]) => (
          <div key={label} className="flex items-center gap-1.5">
            <Icon size={12} style={{ color: 'var(--accent)' }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}

function LoadingState() {
  const [step, setStep] = React.useState(0)
  const steps = ['Parsing events…', 'Detecting TTPs…', 'Clustering phases…', 'Building timeline…']
  React.useEffect(() => {
    const t = setInterval(() => setStep(s => (s + 1) % steps.length), 900)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="w-8 h-8 rounded-full border-2 animate-spin"
           style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
      <p className="text-sm mono" style={{ color: 'var(--accent)' }}>
        {steps[step]}
      </p>
    </div>
  )
}
