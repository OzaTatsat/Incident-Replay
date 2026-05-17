# Incident Replay: UI Design Concept

## 1. Design Rationale
The "Neon Cyberpunk" aesthetic, while visually striking, often induces cognitive overload during long investigations. The core objective of this redesign is to transition the UI from a "hacker dashboard" into a **premium investigative operating system** designed for elite analysts and executives. The new aesthetic prioritizes analytical clarity, trust, calmness, and readability, drawing inspiration from high-end SaaS analytics, editorial data visualization, and modern productivity tools.

## 2. Inspiration References
*   **Linear & Notion:** For their clean, breathable layouts, minimal visual noise, and refined typography.
*   **Stripe Dashboard & Vercel:** For elegant data visualization, soft drop shadows, and premium feel.
*   **Modern Bloomberg Terminal:** Re-imagined with a focus on data density without clutter, using intelligent spacing and subtle borders.
*   **Arc Browser:** For its modern, calm, and focused interface approach.

## 3. Color System
A refined warm-neutral palette designed for low eye strain during prolonged use.

*   **Backgrounds:**
    *   `Primary`: `#f9f8f6` (Warm ivory / subtle parchment)
    *   `Surface`: `#ffffff` (Pure white for elevated cards)
    *   `Elevated`: `#f3f1ed` (Soft stone for nested elements)
*   **Borders:**
    *   `Subtle`: `#e5e3da` (Light neutral gray)
    *   `Strong`: `#d1cdc5` (Slightly darker neutral for contrast)
*   **Text:**
    *   `Primary`: `#2c2b29` (Charcoal)
    *   `Secondary`: `#6b6965` (Muted slate)
    *   `Muted`: `#8c8984` (Soft gray)
*   **Accent:**
    *   `Primary`: `#4a729e` (Muted slate blue for primary actions)
    *   `Glow`: `rgba(74, 114, 158, 0.08)` (Subtle interaction highlight)

### MITRE Phase Colors (Muted & Elegant)
*   `Reconnaissance`: `#7fa1c3` (Soft Blue)
*   `Initial Access`: `#d4a373` (Muted Amber)
*   `Execution`: `#e29578` (Soft Rust)
*   `Persistence`: `#a594f9` (Muted Purple)
*   `Privilege Escalation`: `#e5989b` (Soft Rose)
*   `Defense Evasion`: `#83c5be` (Muted Teal)
*   `Credential Access`: `#e9c46a` (Soft Yellow/Gold)
*   `Discovery`: `#90e0ef` (Light Azure)
*   `Lateral Movement`: `#48cae4` (Soft Cyan)
*   `Collection`: `#bde0fe` (Pale Indigo)
*   `Command and Control`: `#ffb4a2` (Soft Coral)
*   `Exfiltration`: `#e56b6f` (Muted Red)
*   `Impact`: `#b56576` (Deep Muted Berry)
*   `Unknown`: `#9ca3af` (Warm Gray)

## 4. Typography System
Moving away from tech-heavy fonts to an editorial and modern stack.

*   **Primary UI Font:** `Inter`, sans-serif. Used for headers, body text, and UI controls. Provides a highly readable, geometric, yet neutral foundation.
*   **Data/Monospace Font:** `JetBrains Mono`. Retained exclusively for precise data points (IPs, Hashes, IDs, JSON), but presented in lighter weights and subtle colors to reduce visual noise.
*   **Hierarchy:**
    *   Large, clean section titles with generous negative space.
    *   Refined spacing between labels and values to naturally guide the eye.

## 5. Layout & Information Architecture
The layout is restructured to "breathe" better, utilizing whitespace over heavy borders to group information.

1.  **Top Navigation:** Minimalistic. Breadcrumbs for current investigation. Subtle tab switching for views.
2.  **Investigation Overview Cards (StatsBar):** Clean white cards on the ivory background with subtle drop shadows. Large clear numbers.
3.  **Timeline Visualization (Core):** Expanded vertical space. See Section 6.
4.  **Event Inspection Panel:** A right-hand drawer or fixed panel that slides in elegantly. White background, separated by ample padding rather than harsh lines.
5.  **AI Narration:** Integrated as a calm reading experience, styled like an intelligence report.
6.  **[New] Process Ancestry Graph:** A modal or dedicated tab displaying a node-link diagram.
7.  **[New] IOC Relationships:** A side panel mapping extracted IOCs.

## 6. Timeline Redesign
The timeline is transformed from a neon sequencer to a cinematic, analytical timeline.

*   **Background:** Soft ivory.
*   **Phase Regions:** Very subtle, low-opacity background fills behind the timeline grid, using the muted MITRE colors.
*   **Grid:** Ultra-light dotted or dashed lines (`#e5e3da`).
*   **Event Markers:** Elegant, solid circles with slight opacity. No glowing borders. On hover, the node gently expands and surrounding nodes slightly fade to focus attention.
*   **Scrubber:** A simple, elegant slate blue line with a subtle playhead indicator, avoiding flashy animations.

## 7. Animation Philosophy
Animations communicate change without distracting the user.

*   **Easing:** Standard ease-in-out or slightly springy, but heavily damped.
*   **Transitions:** Crossfades for state changes. Fluid height calculations for accordions.
*   **Microinteractions:** Buttons softly deepen in background color on hover. Icon-only buttons reveal an `aria-label` tooltip with zero delay.

## 8. Component Styling & Interaction Behaviors
*   **Buttons:** Soft rounded corners (e.g., `rounded-md` or `rounded-lg`). Flat colors for primary actions; transparent with background fades for secondary actions.
*   **Cards:** Pure white (`#ffffff`) over the primary background (`#f9f8f6`), utilizing soft shadows (e.g., `shadow-sm` or `shadow-md` with 5% opacity).
*   **Forms/Inputs:** Clean borders (`border-gray-200`) that turn slate-blue (`ring-slate-500`) on focus.

## 9. Empty & Loading States
*   **Empty States:** Centered, calm illustrations or minimal icons. Soft text explaining what actions to take. Example: "Drag a Sysmon XML or EVTX file to begin reconstruction."
*   **Loading States:** Skeleton loaders that match the layout structure. A subtle shimmer effect using low-contrast grays, completely eliminating the high-contrast "spinners".
*   **Onboarding:** A brief, 3-step modal walkthrough highlighting the timeline, the AI narration, and the inspection panel, using soft spotlight effects.

## 10. React & D3 Architecture Suggestions
*   **D3 Visualization:** Abstract timeline rendering into smaller sub-components (Axes, Nodes, BackgroundBands) if it grows. Use D3 purely for scale calculation and path generation, but let React render the `<circle>` and `<rect>` elements for easier state-driven animations (e.g., via Framer Motion or React Spring if implemented later).
*   **React Architecture:** Maintain Zustand for global state. Extract the `NormFields` and `EventIcon` into their own files to keep `EventDetail.jsx` clean.
*   **New Features Integration:** For the Process Ancestry Graph, consider `react-flow` or a custom D3 force-directed layout styled with the new muted palette.
