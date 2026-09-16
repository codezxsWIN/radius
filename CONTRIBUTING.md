# Contributing

## Small Educational Contributions

Start with the offline lesson in [ui/index.html](ui/index.html). A good first contribution is a clearer conceptual question, an independently computed fixture answer, an edit/model continuity regression, or a source-profile diagnostic that explains what remains unknown. Keep required access distinct from excessive access; do not label every capability a vulnerability.

Edit lab source, then regenerate with `node tools/build_ui.mjs`. `node tools/build_ui.mjs --check` must find no drift, and `make visual-test` runs the first lesson, lab interactions, both browser suites and accessibility assertions. Python checks run through `tools/verify.py`. Chromium and Node 25+ are developer prerequisites, not learner prerequisites. No new framework or registry dependency is needed for a lesson contribution.

The [educational audit](reviews/2026-09-17-educational-audit.md) remains a historical findings record. Add new verification evidence; do not rewrite failed observations as though they never occurred. Do not make all 520 backlog goals release requirements. Newcomer testing and untested operating systems remain explicit external validation work.

## Engine and Standards Contributions

Use Python 3.12+. Install pinned test extras from pyproject.toml and run `pytest --cov=blastradius --cov-report=term-missing`. Add a hand-computed fixture before changing reachability semantics. Preserve deterministic serialization, action-sensitive escalation guards, fixed denominators and actor-scoped deny behavior.

Only invented tenant exports and credential metadata belong in fixtures. Do not contribute secrets or real tenant records. Proposed live collectors must use documented GET endpoints, least-privilege permissions, pagination, throttling and explicit coverage notes; never execute escalation actions.

Follow GOVERNANCE.md and CODE_OF_CONDUCT.md. Normative proposals need requirement IDs, counterexamples, stable fixture revisions and unconflicted review; future public ratification requires the stated comment/vote process. Vendor-employed connector maintainers need an independent second reviewer. The founder has no employer-specific exception.

Code is Apache-2.0; specification/schema and original documentation are CC-BY-4.0; generated/approved aggregate data are CC0-1.0 as detailed in LICENSING.md. Contributions require authority to license the material. Metric properties remain subject to independent research review. Do not contribute product-management features, paid certification, SIEM/ticketing integrations, SSO, compliance packs or additional executive dashboards.

Run both public conformance adapters when changing core semantics and preserve failing counterexamples. Do not regenerate frozen fixtures merely to make a failing implementation pass. Raw real structural summaries are not eligible for public contribution; even identifier-free counts can fingerprint a tenant. Real intake remains blocked on neutral custody and independent privacy/ethics review.
