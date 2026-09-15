# Visual Session Verification

Session start: 2026-09-09 04:58:05 India time. This report records visual-layer work only; earlier engine tests and dataset results are not silently relabeled as new visual tests.

## Verified Milestone: 2026-09-13

The Meridian Visual Instrument remains the active visual implementation. This milestone improves evidence correctness and portable exports; it does not change the Python engine, result format, source snapshots, or the separate legacy demo dashboard.

| Check | Executed Result | Evidence |
| --- | --- | --- |
| Standalone build | 4,074,372 bytes; 176 embedded result files | `node tools/build_ui.mjs` |
| Workflow contracts | 30 passed; no browser exceptions or network requests | `ui/reports/contract-tests.json` |
| Desktop/mobile views | Nine views at 1440x1000 and 390x844; no page overflow or clipped export selections | `ui/reports/browser-tests.json` |
| Automated accessibility | 18 view audits; zero WCAG A/AA-tagged violations, plus the manual-copy dialog and contract workflow | Browser and contract reports |
| Screenshot repeats | 18/18 byte-identical repeats with the same browser, input, fonts and state | `ui/reports/screenshots/` |
| Renderer unit checks | Six geometry, ordering, determinism and escaping assertions passed | `node ui/test-render.cjs` |
| Shared tokens | Text contrast and three color-vision simulations passed | `ui/reports/color-vision.json` |
| Portable figures | Eight figure types, two widths, three formats: 48 files | `figures/manifest.json` |
| SVG repeatability | 16/16 byte-identical repeat exports | Figure manifest |
| Figure geometry | Physical SVG/PDF widths 88.9 mm and 182 mm; raster dimensions calculated at 300 DPI | Figure manifest |
| Figure integrity | Nonblank PNG samples, complete PDF structure with embedded TrueType font, full SVG hash and model stamps | Figure manifest |
| Figure text | No clipped text or path connector/station-label crossings in the declared fixture matrix; minimum tested text size 7.2 points | Figure manifest |

The standalone bundle SHA-256 is `d6d8a5bfbf44daebd4aec533540b948d9b5dbbd7437e118c1f3ee7021d75d522`.

Corrected behavior:

- Build Loom's bounded k1 caption now says 25 / 71 pairs, consistent with 35.21%, rather than incorrectly repeating the unbounded 45 / 71 count. Weighted captions identify their exact weighted ratios; absolute reach is explicitly a unique-pair count.
- Deterministic copied narratives include model, source hash, engine/schema versions, parameters, snapshot time, manifest qualification, witness edge provenance, blocked transitions, and synthetic-data limitations. No-path narratives retain the same context.
- Clipboard-unavailable and permission-denied paths open a selected, read-only text alternative and return focus correctly. Pseudonymized narratives retain evidence references and explicitly do not claim anonymity or complete redaction.
- The export selector distinguishes the reach disc from its path and the Lorenz curve from the histogram. Conformance and invalid-graph states disable exports instead of silently exporting another figure. Unsupported formats and widths reject.
- Path connectors route around station labels. Mobile export controls wrap without truncating their selected values.
- The visual-test target includes contract tests. Browser gates now fail on recorded accessibility violations, repeat mismatches, external requests or script errors instead of only writing a report.

G25 (deterministic narrative), G82 (IEEE export for the declared synthetic figure set), and G83 (paper figure command) are marked shipped in `ui/goal-status.json`. Other goals retain their prior state; these changes are not a completion percentage for the full research roadmap.

## Reproduce This Milestone

Run from the project directory with the installed Node.js runtime; no package download or server is required:

```text
node tools/build_ui.mjs
node ui/test-render.cjs
node tools/validate_tokens.mjs
node tools/test_ui_contract.mjs
node tools/test_ui_browser.mjs
node tools/make_figures.mjs
node tools/ui_roadmap.mjs
```

`make visual-test` and `make figures` are the corresponding optional Make targets. Figure generation replaces the declared artifacts and their manifest. PDF bytes are not claimed deterministic; SVG bytes are checked. Screenshot comparisons are repeatability checks within one run, not proof against a reviewed historical baseline.

## Current Limits

Chromium was exercised locally. Firefox, Safari, manual assistive-technology validation, large-population browser timing, complete pseudonymization, all fixture/input permutations, and independent scientific or privacy review remain open. Figure checks cover the declared eight-type synthetic matrix, not arbitrary long-label or large imported datasets, and are not a publisher's acceptance guarantee. The engine's earlier 179-test result was not rerun or relabeled as part of this JavaScript-only milestone.

Missing hierarchy, usage and task-scope data are not fabricated. Historical incident rank remains unidentified; structural summaries are explicitly not anonymous. No live collection, telemetry, submission or platform mutations were added.

## First Checkpoint (Historical)

- tools/build_ui_data.py executed132 fresh Python engine result runs, keeping result format0.1 unchanged. The versioned visual catalog references176 local JSON inputs with SHA-256 digests.
- Main illustrative tenant:40 credentials; maximum0.6338028169, p950.6197183099, Gini0.3470138889, share above1/4=0.675. Selected Build Loom reaches45/71 pairs; its disc radius151.262 on a190 full-universe reference gives the correct area ratio.
- The first HTML bundle is approximately4.1MB, fully embedded, including fonts and libraries. It opened from file:// without a server. Nine view controls render; complete interaction, export and regression gates remain in progress.
- First WCAG-tagged axe-core4.10.3 run on the reach/path screen:0 violations,29 passing rules. This is one automated view audit, not full WCAG certification.
- Initial categorical simulation FAILED: protanopia minimum DeltaE0.458. Palette corrected to Okabe-Ito colors; repeated severity100 Machado simulation passes the declared minimum DeltaE10 criterion: protanopia22.729, deuteranopia17.879, tritanopia16.972. Sensitivity lightness increases in all simulations. Body/muted text contrast14.99/6.41 against paper white.
- ui/test-render.cjs passes six initial area/ordering/determinism/escaping assertions. Additional fixture-driven rendering and all-view browser tests are in progress.
- A mobile first-viewport problem was found and fixed by a keyboard-operable collapsible credential selector. The updated mobile layout is pending the next screenshot check.

## Initial Checkpoint Limits (Historical)

No10k/50k browser performance measurement, full-view accessibility matrix, IEEE export verification, visual regression suite or cross-browser pass is claimed at this checkpoint. Missing hierarchy, usage and task-scope data are not fabricated. Historical incident rank remains unidentified; structural summaries are explicitly not anonymous.
