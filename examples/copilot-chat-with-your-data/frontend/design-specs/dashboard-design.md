# Dashboard Design Blueprint

This document captures the current dashboard experience rendered by `components/Dashboard.tsx` so the layout can be regenerated through CopilotKit's generative UI pipeline. It focuses on data bindings, hierarchy, interactions, and visual styling rather than implementation details.

## 1. Purpose and Audience
- **Goal**: Provide an executive view of SaaS sales performance, top products, category mix, regional contribution, customer demographics, and AI-authored strategic commentary.
- **Users**: Revenue and growth leaders who need at-a-glance KPIs with drill-down ability, plus analysts who consume AI-generated insights.
- **Tone**: Professional, data-forward, with concise formatting and high information density.

## 2. Data Model Overview
- Data is delivered as `DashboardDataPayload` (see `frontend/data/dashboard-data.ts`). It contains:
  - `metrics`: Totals and ratios (revenue, profit, customers, conversion rate, average order value, profit margin).
  - `salesData`: Monthly timeseries for Sales, Profit, Expenses, Customers.
  - `productData`: Per-product sales, growth %, units.
  - `categoryData`: Category revenue share and growth.
  - `regionalData`: Regional sales, market share.
  - `demographicsData`: Age-cohort share and spending.
- Strategic commentary is requested via `/ag-ui/action/generateStrategicCommentary` and returns Markdown grouped into Risks, Opportunities, Recommendations.
- Dataset is mirrored on the backend and front-end; highlight events reference chart IDs: `sales-overview`, `product-performance`, `sales-by-category`, `regional-sales`, `customer-demographics`, `strategic-commentary`.

## 3. Layout Blueprint
- **Grid**: Top-level `div` uses `grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4` so large screens display four columns.
- **Metric cards**: Six cards displayed in a nested grid `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6`.
- **Charts**:
  1. `Sales Overview` – spans all four columns (`lg:col-span-4`), area chart with Sales/Profit/Expenses series, legend enabled.
  2. `Product Performance` – `lg:col-span-2`, horizontal bar for `sales` per product.
  3. `Sales by Category` – `lg:col-span-2`, donut chart showing `% value` by category.
  4. `Regional Sales` – `lg:col-span-2`, horizontal bar for `sales` per region.
  5. `Customer Demographics` – `lg:col-span-2`, horizontal bar for `spending` per age group.
- **Strategic Commentary**: Full-width card with tabs for Risks, Opportunities, Recommendations. Each tab renders Markdown via `ReactMarkdown` + `remark-gfm`.
- **Spacing**: Cards use `CardHeader` (title + description) and `CardContent` (chart container). Chart heights fixed at `h-60`.

## 4. Visual Treatments
- **Cards**: Use shadcn card components with default foreground/background tokens.
- **Typography**: Titles `text-base font-medium`, descriptions `text-xs` muted. Metric values `text-xl`. Commentary uses `prose prose-sm` with dark-mode invert.
- **Color palette**: Custom arrays per chart for consistent theme (blue/green/red for area, purple gradient for product bars, mixed palette for categories, green gradient for regions, orange-yellow gradient for demographics).
- **States**:
  - Loading commentary: skeleton pulses (three `div` rows).
  - Errors: red alert block spanning full width.
  - Empty commentary: placeholder text.

## 5. Behaviour & Interactions
- **Data fetch**: Dashboard data delivered via SSE (`/ag-ui/dashboard-data`). Commentary fetched via POST action.
- **Highlight integration**: Cards include `data-chart-id` attributes. AG-UI events trigger `chart.highlight` custom events that focus charts or switch commentary tabs.
- **Tab synchronisation**: Custom event `STRATEGIC_COMMENTARY_TAB_EVENT` keeps commentary tabs in sync with narration/story review.
- **Responsive**: On small screens, charts stack vertically; metrics show in 2-column grid; commentary tabs degrade to single-column buttons.
- **Edit mode ergonomics**: During drag or resize operations the grid overlay is constrained to the Dashboard Preview card, cards snap to column/row cells (gaps are ignored), single-cell cards collapse into a compact header that preserves the icon, delete action, and a truncated title so essential controls stay visible, and selecting a card triggers an AG-UI `DirectUIUpdate` instructing the Data Assistant to show that item's properties.

## 6. Generative UI Guidance
- **Inputs to provide the agent**:
  - Dataset schema (as above) or real payload from `/ag-ui/dashboard-data`.
  - Strategic commentary blueprint (three sections, Markdown bullet lists).
  - Highlight IDs for chart mapping.
- **Desired outputs**:
  - Auto-generated metric cards mirroring `metrics` keys.
  - Visualisations chosen per dataset heuristics:
    - Timeseries (`date` + numeric fields) → multi-series area/line chart.
    - Nominal categories + currency metrics → horizontal bar chart.
    - Share-of-total metrics (values 0–100 labelled `value`, `percentage`, or `marketShare`) → donut or stacked bar.
  - Commentary tab component fed by Markdown with optional skeleton + error states.
- **Constraints**:
  - Maintain chart IDs listed above for compatibility with highlight events.
  - Keep card titles concise; show short descriptions pulled from dataset meaning (e.g., "Monthly sales and profit data").
  - Ensure consistent figure formatting: currency for large monetary values, `%` for rates/share, `toLocaleString` for counts.
  - Provide accessible labels and ensure components adapt to dark mode.
- **Open slots for future extension**:
  - Optionally render secondary metrics (growth %, units) alongside primary charts.
  - Allow narration actions or CTA buttons near commentary.

## 7. Error & Loading Patterns
- Display dataset fetch errors as bordered alerts occupying the full grid width.
- Show loading state for commentary; dataset skeleton can reuse card placeholders if needed.
- Strategic commentary fallback: show raw Markdown if headings are missing; otherwise show placeholder text.

This guide should be sufficient for CopilotKit's generative UI agent to reconstruct the dashboard programmatically, mapping dataset structures to visual components while honouring existing interactions.
