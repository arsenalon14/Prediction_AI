# Design System: TAA Perishable Demand Forecaster

## 1. Visual Theme & Atmosphere

**Mood:** Deep crimson command center — a high-stakes airline operations tool. The interface evokes a premium aviation control room: data-dense, breathably structured, serious and precise.

**Aesthetic Philosophy:** Dark-mode with a near-black warm-crimson base. Brand color is Thai AirAsia red (#ED1C24), paired with muted gold (#E3AE45) and signal emerald (#36c98a). Gradient glows at corners reinforce depth without decoration. No glassmorphism. Panels are semi-opaque tinted surfaces, not frosted cards.

**Register:** Product (tool, not brand). Design serves the data — Q* recommendation table is the primary visual output. Every element earns its density.

**Density:** Medium-high. Data-rich panels with deliberate internal spacing. Tabular numbers throughout.

---

## 2. Color Tokens

All brand colors are tokenized as both hex and RGB component form for alpha compositing.

### Core palette

| Token | Value | Role |
|---|---|---|
| `--bg-0` | `#120c0c` | Deepest background canvas |
| `--bg-1` | `#1a1213` | Secondary background layer |
| `--panel` | `#201617` | Panel surface |
| `--panel-2` | `#26191a` | Elevated panel / header rows |
| `--panel-soft` | `rgba(255,255,255,.035)` | Subtle inline surface tint |
| `--line` | `rgba(255,255,255,.09)` | Structural dividers / borders |
| `--line-strong` | `rgba(255,255,255,.16)` | Emphasis borders |

### Brand & semantic

| Token | Value | Role |
|---|---|---|
| `--red` | `#ED1C24` | Primary brand — Thai AirAsia red. CTAs, active states, active sidebar items |
| `--red-bright` | `#ff3b42` | Hover/focus intensification |
| `--red-deep` | `#a8121a` | Pressed / deep shadow tint |
| `--gold` | `#E3AE45` | Secondary brand — Q* emphasis, warnings, revenue |
| `--gold-bright` | `#F4D078` | Gold hover / highlight |
| `--gold-pale` | `#F6E2B0` | Faint gold tint for backgrounds |
| `--up` | `#36c98a` | Positive delta — sell-through up, load increased |
| `--down` | `#ff6b6b` | Negative delta — stockout risk, load decreased |
| `--warn` | `#E3AE45` | Warning states (aliases `--gold`) |

### Text

| Token | Value | Role |
|---|---|---|
| `--text` | `#F6EFEA` | Primary body text |
| `--text-2` | `#cdbfb9` | Secondary / supporting text |
| `--text-muted` | `#9a8983` | Labels, metadata, section eyebrows |

### RGB decompositions (for alpha compositing)

```css
--red-rgb: 237,28,36;
--up-rgb: 54,201,138;
--gold-rgb: 227,174,69;
--down-rgb: 255,107,107;
```

Usage: `rgba(var(--red-rgb), 0.15)` — never hard-code brand RGBA values.

### Gradient

```css
--grad-sun: linear-gradient(90deg, #7a0f12 0%, #ED1C24 22%, #F2602A 48%, #E3AE45 76%, #F6E2B0 100%);
```

Used on the 4px brand stripe at the top of the viewport and the active-item sidebar indicator.

---

## 3. Typography

**Fonts:**
- Display / headings (`h1`, `h2`, `h3`): `'Poppins'` (Google Fonts), weights 600/700/800
- Body / UI: `'IBM Plex Sans'`, weights 400/500/600/700; falls back to `system-ui, sans-serif`
- Both loaded with `display=swap`

**Scale:**
| Element | Size | Weight | Notes |
|---|---|---|---|
| Brand title (h1) | 1.02rem | 700 | Sidebar brand lockup only |
| Panel titles (h3) | 1.12rem | 700 | `.panel-title` on each content panel |
| Section labels | 0.72rem | 700 | Uppercase, 0.14em tracking, `--text-muted` |
| Body | 0.9–0.95rem | 400 | Primary text |
| Table headers | 0.82–0.85rem | 600 | Uppercase, 0.08em tracking |
| Data values | 1.2–1.4rem | 700 | KPI stat values |
| Small / metadata | 0.72–0.78rem | 400–500 | Tags, badges, theory labels |

**Rules:**
- `font-variant-numeric: tabular-nums` on all numerical data columns — non-negotiable for aligned Q* tables
- `text-wrap: balance` on short headings
- Line length capped at ~75ch on prose; tables may be wider

---

## 4. Spacing & Layout

**Border radii:**
```css
--r-lg: 18px   /* panels, modals */
--r-md: 12px   /* cards, upload zones */
--r-sm: 8px    /* buttons, inputs, badges */
```

**App shell:** Two-column grid — `320px` fixed sidebar + `1fr` main content.

**Sidebar:** `position: sticky; height: 100vh; overflow-y: auto`. Gradient `#1c1314 → #160f10`.

**Panel rhythm:** `1.5–1.8rem` internal padding. `1.2–1.5rem` gap between panels.

**Responsive breakpoints:**
- `1100px`: sidebar collapses to icon strip; main content takes full width
- `980px`: actuals grid 2-col (with last-child spanning full width)
- `640px`: single-column actuals grid; KPI row becomes 2×2; upload grid stacks

---

## 5. Components

### Sidebar menu item
- Default: transparent background, `--text-2` label
- Active: `rgba(var(--red-rgb),.18)` background, `var(--red-bright)` left indicator strip (3px), `--text` label
- Hover: `rgba(255,255,255,.05)` tint
- Inactive items hidden behind toggle (not removed from DOM — toggled via `[hidden]`)

### Toggle switch
- 50×26px capsule. Off: `rgba(255,255,255,.12)`. On: `var(--red)`.
- Knob: 20px white circle, `translateX(0)` → `translateX(24px)` on activation
- Transition: `0.28s cubic-bezier(.4,0,.2,1)` on `background` and `transform`

### Buttons
- **Primary:** Red gradient, `--r-sm`, glow shadow `0 8px 20px -8px rgba(var(--red-rgb),.8)`. Hover: deeper glow.
- **Secondary / ghost:** `rgba(255,255,255,.07)` fill, `var(--line-strong)` border
- **Upload CTA:** Dashed `rgba(var(--red-rgb),.5)` border, `rgba(var(--red-rgb),.04)` bg. Dragover: brighter border + tint

### Badges
- All `border-radius: 20px`, `0.78rem / 600` weight
- `.b-up`: `rgba(var(--up-rgb),.15)` bg, `rgba(var(--up-rgb),.28)` border, `#56d79e` text
- `.b-down`: `rgba(var(--down-rgb),.15)` bg, `rgba(var(--down-rgb),.28)` border, `rgba(var(--down-rgb),1)` text
- `.b-neutral`: `rgba(255,255,255,.08)` bg, `--text-2` text

### Theory tags
- `rgba(var(--red-rgb),.13)` bg, `#ff9a9e` text (red variant)
- `rgba(var(--gold-rgb),.14)` bg, `var(--gold-bright)` text (gold variant)
- Border-radius: `20px`; font size: `0.72rem`

### Q* table
- Full-width, no outer border. Row hover: `rgba(255,255,255,.02)`. Header row: `--panel-2` bg, uppercase labels.
- Columns use `tabular-nums`. Confidence column uses `.b-up` / `.b-down` badges.
- Q* value column: bolder weight, `--text` color — the primary decision output.

### Bar chart (sell-through / margin bars)
- `.bar-track`: 6px tall, `--panel-soft` background, `--r-sm` radius
- `.bar-fill`: `var(--grad-sun)` gradient; starts at `scaleX(0)`, animates to target via `requestAnimationFrame` after DOM insert; `will-change: transform` set for compositor promotion
- Transition: `transform .8s cubic-bezier(.4,0,.2,1)`

### Tooltips (`.tooltip-help`)
- Pure CSS `::after` pseudo-element positioned above trigger
- Keyboard-accessible: `tabindex="0"`, `role="button"`, `aria-label` set at init
- Triggers on both `:hover` and `:focus-visible`

### Modal / dialog
- `<dialog>` element with `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- Overlay: `rgba(8,5,5,.66)` backdrop. Panel: `--panel-2` bg, `--r-lg` radius
- Focus trapped inside while open; `Escape` closes

### Form inputs
- Background: `--panel`. Border: `1px solid var(--line-strong)`. Text: `--text`
- Focus: `outline: 2px solid var(--red); outline-offset: 2px; border-color: var(--red)`
- `focus-visible` only (no outline on mouse click)
- `@media (forced-colors: active)` fallback: `outline: 2px solid ButtonText`

---

## 6. Motion & Animation

**Default easing:** `--ease: .28s cubic-bezier(.4,0,.2,1)` — standard for micro-interactions.

**Rules:**
- Animate only `transform` and `opacity` by default. `will-change: transform` on bar fills.
- No layout-property animation (`width`, `height`, `top`, `left`).
- All transitions have `@media (prefers-reduced-motion: reduce)` fallbacks — disable transforms, keep instant state changes.
- No page-load orchestration. The interface loads into a task; no entrance choreography.

**Specific motions:**
- Sidebar active indicator: `opacity` + `transform: scaleY(1)` fade-in on active item change
- Bar fills: `scaleX(0) → scaleX(target)` triggered via `requestAnimationFrame` after `innerHTML` set
- Tooltips: `opacity` + `transform: scale(1)` reveal on hover/focus
- Modal open/close: `opacity` + `transform: translateY` fade-slide; `0.28s` in, `0.22s` out

---

## 7. Accessibility

- WCAG AA minimum throughout
- Heading hierarchy: `h1` (brand), `h3` (panel titles — `.panel-title`) — no `h2` in current layout
- All `<th>` in data tables carry `scope="col"` or `scope="row"`
- KPI values (`#kpi-pax`, `#kpi-bob`, `#kpi-pbm`, `#kpi-date`) have `aria-live="polite"`
- Skip-to-main link at top of `<body>` (`.skip-link`)
- All interactive elements have visible focus indicators
- `forced-colors` media query on focus states
- Desktop-first (1280px+); touch targets not a primary concern for this ops-room context

---

## 8. Audit History

| Date | Score | Notes |
|---|---|---|
| 2026-06-03 Pass 1 | 14/20 | Baseline — JS SyntaxError fixed, CSS `[hidden]` override fixed |
| 2026-06-03 Pass 2 | 17/20 | A11y +1, Perf +1, Responsive +1 — all P1 issues resolved |
| 2026-06-03 Pass 3 | 19/20 | `--down-rgb` tokenized; `will-change: transform` on bar fills |

**Remaining open items (P3):**
- Switch toggle touch target: 40×22px — below 44px minimum (acceptable for desktop-only context)
- Emoji icons in upload zones — rendering edge case on some Linux font stacks
