import React, { useRef, useEffect, useCallback } from 'react'
import * as d3 from 'd3'
import { useStore } from '../../store/useStore'

// Swimlane config — which event types live on which row
const LANES = [
  { key: 'process_create',     label: 'PROCESS',   row: 0 },
  { key: 'network_connect',    label: 'NETWORK',   row: 1 },
  { key: 'registry_set',       label: 'REGISTRY',  row: 2 },
  { key: 'registry_create',    label: 'REGISTRY',  row: 2 },
  { key: 'file_create',        label: 'FILE',      row: 3 },
  { key: 'process_access',     label: 'ACCESS',    row: 4 },
  { key: 'dns_query',          label: 'DNS',       row: 5 },
  { key: 'create_remote_thread',label:'INJECT',    row: 6 },
  { key: 'image_load',         label: 'DLL',       row: 7 },
]
const LANE_LABELS = ['PROCESS','NETWORK','REGISTRY','FILE','ACCESS','DNS','INJECT','DLL']
const LANE_HEIGHT = 44
const MARGIN      = { top: 32, right: 28, bottom: 36, left: 76 }

export default function TimelineCanvas({ width, height }) {
  const svgRef   = useRef(null)
  const rafRef   = useRef(null)
  const {
    investigation, events, phases, playhead, isPlaying,
    playbackSpeed, setPlayhead, setIsPlaying, setSelectedEvent,
    phaseColor, activePhaseFilter, PHASE_COLORS,
  } = useStore()

  const totalH = LANE_LABELS.length * LANE_HEIGHT + MARGIN.top + MARGIN.bottom
  const realH  = Math.max(height || totalH, totalH)
  const innerW = (width || 900) - MARGIN.left - MARGIN.right

  // ── X scale ──────────────────────────────────────────────────────────────────
  const tMin = investigation?.time_start || 0
  const tMax = investigation?.time_end   || 1
  const xScale = d3.scaleLinear().domain([tMin, tMax]).range([0, innerW])

  // ── Visible events ────────────────────────────────────────────────────────────
  const cutoff = tMin + playhead * (tMax - tMin)
  const visible = events.filter(ev =>
    ev.timestamp <= cutoff &&
    (!activePhaseFilter || ev.phase === activePhaseFilter)
  )

  const laneRow = Object.fromEntries(LANES.map(l => [l.key, l.row]))

  // ── Draw ──────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!svgRef.current || !events.length) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const g = svg.append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`)

    // Phase bands
    phases.forEach((ph, i) => {
      if (!ph.start_ts || !ph.end_ts) return
      const x1 = xScale(ph.start_ts)
      const x2 = xScale(ph.end_ts)
      const col = PHASE_COLORS[ph.phase_name] || '#475569'
      g.append('rect')
        .attr('x', x1).attr('y', -MARGIN.top)
        .attr('width', Math.max(x2 - x1, 2))
        .attr('height', realH - MARGIN.bottom + MARGIN.top)
        .attr('fill', col)
        .attr('opacity', 0.06)

      // Phase label at top
      const labelText = ph.display_name?.toUpperCase() || ph.phase_name.toUpperCase()
      // Estimate text width roughly: ~5.5px per character at 9px font-size + padding
      const estWidth = labelText.length * 6
      if (x2 - x1 > estWidth) {
        // Stagger the labels to prevent overlapping if regions are dense, rotating through 3 levels
        const yOffset = -6 - (i % 3) * 10
        g.append('text')
          .attr('x', x1 + (x2 - x1) / 2)
          .attr('y', yOffset)
          .attr('text-anchor', 'middle')
          .attr('fill', col)
          .attr('font-size', 9)
          .attr('font-weight', 700)
          .attr('letter-spacing', '0.08em')
          .attr('font-family', 'Inter, sans-serif')
          .text(labelText)
      }
    })

    // Swimlane rules
    LANE_LABELS.forEach((label, i) => {
      const y = i * LANE_HEIGHT + LANE_HEIGHT / 2
      g.append('line')
        .attr('x1', 0).attr('y1', y + LANE_HEIGHT / 2)
        .attr('x2', innerW).attr('y2', y + LANE_HEIGHT / 2)
        .attr('stroke', '#e5e3da')
        .attr('stroke-dasharray', '2,2')
        .attr('stroke-width', 1)

      svg.append('text')
        .attr('x', MARGIN.left - 8)
        .attr('y', MARGIN.top + y + 5)
        .attr('text-anchor', 'end')
        .attr('fill', '#8c8984')
        .attr('font-size', 9)
        .attr('font-weight', 600)
        .attr('letter-spacing', '0.12em')
        .attr('font-family', 'JetBrains Mono, monospace')
        .text(label)
    })

    // X axis ticks
    const timeAxis = d3.axisBottom(xScale)
      .ticks(8)
      .tickFormat(d => {
        const dt = new Date(d)
        return `${String(dt.getUTCHours()).padStart(2,'0')}:${String(dt.getUTCMinutes()).padStart(2,'0')}:${String(dt.getUTCSeconds()).padStart(2,'0')}`
      })

    g.append('g')
      .attr('transform', `translate(0,${LANE_LABELS.length * LANE_HEIGHT + 8})`)
      .call(timeAxis)
      .call(ax => {
        ax.select('.domain').attr('stroke', '#e5e3da')
        ax.selectAll('.tick line').attr('stroke', '#e5e3da')
        ax.selectAll('.tick text')
          .attr('fill', '#8c8984')
          .attr('font-size', 9)
          .attr('font-family', 'JetBrains Mono, monospace')
      })

    // Events group (updated separately for performance)
    g.append('g').attr('class', 'events-layer')

  }, [events, phases, width, height, activePhaseFilter])

  // ── Update dots when visible events change ───────────────────────────────────
  useEffect(() => {
    if (!svgRef.current || !events.length) return
    const g = d3.select(svgRef.current).select('.events-layer')
    if (g.empty()) return

    const dots = g.selectAll('circle.evt').data(visible, d => d.id)

    dots.enter().append('circle')
      .attr('class', 'evt event-dot')
      .attr('cx', d => xScale(d.timestamp))
      .attr('cy', d => {
        const row = laneRow[d.event_type] ?? 7
        return row * LANE_HEIGHT + LANE_HEIGHT / 2
      })
      .attr('r', 0)
      .attr('fill', d => PHASE_COLORS[d.phase] || '#475569')
      .attr('opacity', 0.85)
      .attr('stroke', d => {
        const score = d.suspicion_score || 0
        return score > 70 ? '#2c2b29' : 'none'
      })
      .attr('stroke-width', 1)
      .on('click', (event, d) => { event.stopPropagation(); setSelectedEvent(d) })
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', Math.max(6, scoreToRadius(d.suspicion_score) + 2))
      })
      .on('mouseout', function(event, d) {
        d3.select(this).attr('r', scoreToRadius(d.suspicion_score))
      })
      .transition().duration(200)
      .attr('r', d => scoreToRadius(d.suspicion_score))

    dots.exit()
      .transition().duration(150)
      .attr('r', 0).attr('opacity', 0).remove()

  }, [visible.length, playhead, activePhaseFilter])

  // ── Playback engine ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isPlaying) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      return
    }
    if (playhead >= 1) { setIsPlaying(false); return }

    let last = null
    const step = (now) => {
      if (!last) { last = now }
      const dt      = (now - last) / 1000
      last = now
      const range   = tMax - tMin
      const advance = range > 0 ? (dt * playbackSpeed * 10000) / range : 0
      const next    = Math.min(playhead + advance, 1)
      setPlayhead(next)
      if (next < 1) rafRef.current = requestAnimationFrame(step)
      else setIsPlaying(false)
    }
    rafRef.current = requestAnimationFrame(step)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [isPlaying, playhead, playbackSpeed, tMin, tMax])

  // ── Playhead line ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!svgRef.current || !events.length) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('.playhead-line').remove()
    const x = MARGIN.left + xScale(tMin + playhead * (tMax - tMin))
    svg.append('line')
      .attr('class', 'playhead-line')
      .attr('x1', x).attr('y1', MARGIN.top - 14)
      .attr('x2', x).attr('y2', realH - MARGIN.bottom + MARGIN.top)
      .attr('stroke', '#4a729e')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '3,3')
      .attr('opacity', 0.8)
  }, [playhead, events.length, width])

  // Click on SVG to scrub
  const onSvgClick = useCallback((e) => {
    if (!events.length) return
    const rect  = svgRef.current.getBoundingClientRect()
    const relX  = e.clientX - rect.left - MARGIN.left
    const ratio = Math.max(0, Math.min(1, relX / innerW))
    setPlayhead(ratio)
    setSelectedEvent(null)
  }, [events.length, innerW])

  return (
    <svg
      ref={svgRef}
      width={width || '100%'}
      height={realH}
      style={{ cursor: 'crosshair', display: 'block' }}
      onClick={onSvgClick}
    />
  )
}

function scoreToRadius(score) {
  const s = score || 0
  if (s >= 90) return 7
  if (s >= 70) return 5.5
  if (s >= 50) return 4.5
  if (s >= 30) return 3.5
  return 2.5
}
