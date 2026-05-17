/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        ui:   ['Rajdhani', 'sans-serif'],
      },
      colors: {
        bg:      { primary: '#080c10', surface: '#0d1117', elevated: '#131920' },
        border:  { subtle: '#1a2332', strong: '#243347' },
        text:    { primary: '#e2e8f0', secondary: '#8899aa', muted: '#4a5568' },
        accent:  '#38bdf8',
        phase: {
          reconnaissance:      '#4a9eff',
          initial_access:      '#f59e0b',
          execution:           '#f97316',
          persistence:         '#a855f7',
          privilege_escalation:'#ec4899',
          defense_evasion:     '#14b8a6',
          credential_access:   '#eab308',
          discovery:           '#60a5fa',
          lateral_movement:    '#06b6d4',
          collection:          '#6366f1',
          command_and_control: '#f43f5e',
          exfiltration:        '#ef4444',
          impact:              '#dc2626',
          unknown:             '#475569',
        }
      }
    }
  },
  plugins: []
}
