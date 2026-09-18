# Lab evolution redesign — 2026-09-09

The homepage now presents an ancestry map with readable research titles, status,
creation dates, and secondary Lab identifiers. The founding studies sit at the
center of their branches. The newest SU(N) direction appears above the D4 and
threshold branches. Hovering or focusing a study highlights its immediate
relationships and names the work it builds on. Every one of the seven registered
parent relationships is preserved; Lab metadata and scientific status were not
changed.

## Audit findings and replacement

The old algorithm allocated another lower lane whenever it discovered a sibling,
so expanding the program produced a downward staircase. Edges reused the same
narrow channels. Its horizontal positions were ordered slots, not a proportional
time axis. Ordinary wheel events were prevented and mapped to zoom.

The replacement orders the DAG topologically, uses ancestry depth for columns,
selects the closest parent for balanced subtree placement, and reserves separate
routes for other recorded parents. Branches containing newer studies are placed
first. HTML cards are measured before routing so titles do not collide with the
layout. Creation dates remain explicit on each card; the footer explains that
spacing represents ancestry rather than elapsed time. Dashed lines are additional
registered parents, not a claim of weaker scientific relevance.

Ordinary wheel and trackpad scrolling use native two-axis scrolling. Background
dragging pans the viewport. Ctrl-wheel pinch and Safari gesture events zoom around
the gesture position. Touch pointer events support single-finger panning and
two-finger pinch. Buttons, keyboard zoom shortcuts, keyboard navigation, and an
Overview action remain available. Narrow screens begin at a readable scale and
can pan horizontally; Overview fits the full map. Navigation disposes observers
and listeners before remounting.

## Delivery verification

The live homepage at `http://localhost:8010/` was tested against the active
`/api/labs` registry. All four served frontend assets match the local files, with
updated version query strings in the active HTML shell. The accompanying JSON
records source hashes, live metadata, and separate browser checks.

- Six desktop cards are fully visible, with their complete titles inside them.
- All seven registered connections are displayed; sampled SVG paths have zero
  crossings for the current graph.
- Normal wheel input does not zoom; zoomed content scrolls on both axes.
- Pinch keeps the world position under the cursor stable; drag pans both axes.
- Keyboard focus highlights relationships and Enter opens the intended Lab.
- Returning through SPA navigation mounts a single working set of controls.
- Chromium touch emulation passes pinch, pan without accidental navigation,
  Overview, and tapping a study to open it.
- Seven layout regressions and three existing reference tests pass; changed
  JavaScript files pass syntax checks.

Final screenshots are stored in `.tmp/evolution-audit/desktop.png`, `mobile.png`,
and `focus.png`; the original surface is retained as `before.png` there.
Physical macOS trackpad/Safari testing was unavailable. Safari event handling was
verified with synthetic gesture events; this is not a physical-device claim.
The zero-crossing result applies to the current graph, not every possible future
DAG.
