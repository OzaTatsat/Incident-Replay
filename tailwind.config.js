/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        ui:   ['Inter', 'sans-serif'],
      },
      colors: {
        bg:      { primary: '#f9f8f6', surface: '#ffffff', elevated: '#f3f1ed' },
        border:  { subtle: '#e5e3da', strong: '#d1cdc5' },
        text:    { primary: '#2c2b29', secondary: '#6b6965', muted: '#8c8984' },
        accent:  '#4a729e',
        phase: {
          reconnaissance:      '#7fa1c3',
          initial_access:      '#d4a373',
          execution:           '#e29578',
          persistence:         '#a594f9',
          privilege_escalation:'#e5989b',
          defense_evasion:     '#83c5be',
          credential_access:   '#e9c46a',
          discovery:           '#90e0ef',
          lateral_movement:    '#48cae4',
          collection:          '#bde0fe',
          command_and_control: '#ffb4a2',
          exfiltration:        '#e56b6f',
          impact:              '#b56576',
          unknown:             '#9ca3af',
        }
      }
    }
  },
  plugins: []
}
