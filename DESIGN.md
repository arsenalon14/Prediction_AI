# Design System: TAA Perishable Demand Forecaster

## 1. Visual Theme & Atmosphere

**Mood:** Deep, immersive cockpit — a command center for airline operations intelligence. The interface evokes a premium aviation control room: dense with data yet breathably spacious, serious yet modern.

**Aesthetic Philosophy:** Dark-mode glassmorphism with subtle luminous accents. Every surface floats above the deep midnight canvas with whisper-soft frosted-glass translucency. Gradient glows pulse from strategic corners, giving the interface a living, breathing quality — as if the AI engine is actively thinking.

**Density:** Medium-high. Data-rich panels with generous internal padding prevent cognitive overload despite the volume of numerical information.

## 2. Color Palette & Roles

| Descriptive Name | Hex Code | Functional Role |
|---|---|---|
| Midnight Abyss | `#0f172a` | Primary background canvas — the deepest layer |
| Frosted Slate | `rgba(30, 41, 59, 0.7)` | Glass panel backgrounds — semi-transparent card surfaces |
| Electric Cobalt | `#3b82f6` | Primary action accent — buttons, links, active borders, upload zone |
| Royal Indigo | `#6366f1` | Gradient endpoint for primary actions — paired with Electric Cobalt |
| Soft Lavender | `#a78bfa` | Gradient endpoint for headings — creates a blue→purple text shimmer |
| Signal Emerald | `#10b981` | Success states — active toggles, positive delta badges, revenue up |
| Alert Crimson | `#ef4444` | Danger/warning — negative deltas, stockout risk, inactive states |
| Cloud White | `#f8fafc` | Primary text — high-contrast body and heading text |
| Muted Pewter | `#94a3b8` | Secondary text — labels, descriptions, supporting copy |
| Ghost Border | `rgba(255, 255, 255, 0.1)` | Panel borders — barely-visible structural separators |

## 3. Typography Rules

- **Font Family:** `'Inter'` (Google Fonts) — a humanist sans-serif optimized for screen readability at small sizes. Weights: 300 (light), 400 (regular), 600 (semibold), 700 (bold).
- **Headings (h1):** 2rem / 700 weight. Use `background: linear-gradient(to right, #60a5fa, #a78bfa)` with `-webkit-background-clip: text` for a shimmering gradient text effect. Text-wrap: balance.
- **Section Headings (h2):** 1.25rem / 600 weight. Cloud White. Underlined with a 1px Ghost Border bottom.
- **Body Text:** 0.95rem / 400 weight. Cloud White for primary, Muted Pewter for supporting.
- **Table Headers:** 0.85rem / 600 weight. Muted Pewter. UPPERCASE with 0.5px letter-spacing.
- **Data Values:** 1.2rem / 700 weight for emphasis (stat-val class).
- **Number Columns:** Use `font-variant-numeric: tabular-nums` for aligned numerical data.

## 4. Component Stylings

* **Glass Panels:** Generously rounded corners (`border-radius: 16px`). Frosted Slate background with `backdrop-filter: blur(16px)`. Ghost Border edge. Whisper-soft drop shadow (`0 10px 30px rgba(0,0,0,0.2)`). On hover: gentle lift (`translateY(-2px)`) with deepened shadow.
* **Primary Buttons:** Pill-adjacent rounding (`border-radius: 8px`). Gradient fill from Electric Cobalt → Royal Indigo at 135°. Luminous glow shadow (`0 4px 15px rgba(59,130,246,0.4)`). On hover: intensified glow and subtle scale (`1.02`).
* **Secondary Buttons:** Ghost-style — transparent with Ghost Border outline. Cloud White text. On hover: subtle frosted fill (`rgba(255,255,255,0.1)`).
* **Toggle Switches:** 44×24px capsule shape. Off: muted frosted glass. On: Signal Emerald fill. White circular knob slides 20px with 0.3s transition.
* **Upload Zone:** Dashed 2px Electric Cobalt border. Gently rounded (`border-radius: 12px`). Faint blue-tinted background (`rgba(59,130,246,0.05)`). On hover: intensified tint and brighter border.
* **Badges:** Fully rounded pill shape (`border-radius: 99px`). 0.8rem / 600 weight. Success variant: Signal Emerald text on translucent green. Danger variant: Crimson text on translucent red.
* **Tables:** Full-width, collapsed borders. Rows separated by Ghost Border bottom. On hover: faint frosted highlight (`rgba(255,255,255,0.02)`). Header row uses Muted Pewter uppercase labels.

## 5. Layout Principles

- **Grid Structure:** Two-column layout — fixed 350px left sidebar for menu management, fluid right column for upload zone and results table.
- **Spacing Strategy:** 2rem page padding. 2rem gap between grid columns. 1.5rem internal panel padding. Consistent vertical rhythm with 0.75rem between list items.
- **Responsive Behavior:** Designed primarily for desktop operations (1280px+). Panels stack vertically on narrower viewports.
- **Background Depth:** Radial gradients anchored at opposing corners (top-right blue glow, bottom-left emerald glow) create a subtle sense of atmospheric depth behind all panels.

## 6. Animation & Motion

- All transitions use `0.3s ease` for micro-interactions.
- Animate only `transform` and `opacity` (compositor-friendly).
- Honor `prefers-reduced-motion` — disable transforms and transitions.
- Button hover: `transform: scale(1.02)` + shadow intensification.
- Panel hover: `translateY(-2px)` lift.
- Toggle: `translateX(20px)` knob slide.
