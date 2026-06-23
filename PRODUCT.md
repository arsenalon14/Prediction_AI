# Product

## Register

product

## Users

Thai AirAsia catering and operations staff at DMK hub. Primary context: pre-flight planning sessions 2–3 days before departure, often under time pressure with a narrow action window. The primary task on any given session is uploading the passenger manifest and PBM file, running the forecast, and reading the Q* recommendation table to set catering load quantities per SKU.

Secondary task: post-flight actuals upload to keep the model current after each return to DMK.

These are operational professionals, not data scientists. They trust the output when the tool is clear and consistent; they lose trust when numbers are ambiguous or UI state is surprising.

## Product Purpose

AI-driven Buy-on-Board perishable inventory optimizer for Thai AirAsia's DMK–MLE–DMK pair route. Replaces manual stocking heuristics that simultaneously produced 23–34% sell-through and 12–20% stockout rates — discarding most loaded food while still running out of top sellers.

The system outputs Q* (optimal load quantity) per product per flight via a 7-theory operations research pipeline calibrated by product-level Year-over-Year (YoY) demand scaling. The pipeline includes: Tobit MLE demand censoring, Newsvendor critical fractile, demographic gamma adjustment, product substitution for new items, and post-flight MLE refit.

Success means catering staff load with confidence: waste falls, stockouts drop, and the model sharpens every flight.

## Brand Personality

Intelligent, Calm, Trustworthy. The tool earns confidence through precision and clarity — not through visual showmanship. Numbers are correct; states are unambiguous; the interface never surprises a user who has run this workflow before.

## Anti-references

- **Consumer food apps (Grab, Airbnb):** Playful, warmth-forward, designed for discovery. Wrong register: this is a high-stakes operational decision tool, not a consumer experience.
- **Generic SaaS (Notion/Linear-style):** Airy, casual, light — the aesthetic of tools for creative knowledge workers. Inappropriate for an environment where a wrong load quantity has direct financial and food-waste consequences.

## Design Principles

1. **Q* is the product.** Every other element on screen exists to explain or enable the Q* recommendation table. Never let decorative UI compete with the output row.
2. **Workflow as structure.** The three-tab sequence (Menu → Forecast → Actuals) mirrors the operational cadence. Navigation should be invisible to someone who runs this daily.
3. **Precision signals trust.** Exact numbers with clear labels beat rounded approximations with polish. When the model has high confidence, show that. When it has uncertainty, surface it plainly — don't hide variance behind clean formatting.
4. **Calm under pressure.** This interface is used before departure with a narrow time window. No animation distracts; no unexpected state change breaks focus; every error message names the problem and points to the fix.
5. **Earn density.** Data-rich is correct for this context, but density must be legible. Each column and label earns its place against the operator's decision workflow — remove anything that doesn't shorten time-to-action.

## Accessibility & Inclusion

WCAG AA minimum. Desktop-first (1280px+), used in an office or operations room context. Reduced motion support required: all transitions must have a `prefers-reduced-motion` fallback. No accessibility-specific user needs identified beyond standard contrast and keyboard navigation.

## Technical Baseline

Single-file SPA (`forecast_app.html`) served by Flask (`app.py`) on `127.0.0.1:5000`. All CSS, HTML, and JavaScript are co-located in one file. The Flask backend exposes REST endpoints consumed via relative URL (`API = ''`).

- **Fonts:** Poppins (headings) + IBM Plex Sans (body) via Google Fonts with `display=swap`
- **Design tokens:** All brand RGBA values use CSS custom property decomposition (`--red-rgb`, `--up-rgb`, `--gold-rgb`, `--down-rgb`) — no raw brand color values hard-coded
- **Menu source:** `active_menu.json` (22 items, 10 active) — real FNBG codes, loaded at runtime via `/api/menu`
- **Backend:** Python/Flask, `DATA_DIR` at `C:\Users\Chaiwatwannawit\Desktop\AI`

## Quality Status

Last audit: **2026-06-10 — 20/20 (Perfect)**

| Dimension | Score |
|---|---|
| Accessibility | 4/4 |
| Performance | 4/4 |
| Responsive | 4/4 |
| Theming | 4/4 |
| Anti-Patterns | 4/4 |

### Updates (June 10, 2026):
- **Year-over-Year Demand Scaling:** Calibrates pre-2026 historical rates by product-specific demand shift ratios to resolve over-catering safety stock inflation.
- **Daily Sales Monitor API Restore:** Corrected missing total open, sales, and wastage metrics by dynamically reconstructing multi-date aggregates from post-flight CSV uploads.


Remaining P3 gaps: switch toggle touch target (40×22px, below 44px minimum — acceptable desktop-only), emoji icons in upload zones.
