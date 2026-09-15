# Repository Review Delivery Slice

## Expanded Evidence Review: 2026-09-16

The latest user direction to improve the tool authorizes better coverage of the existing source boundary, not a new provider or live permission evaluator. The Identities tab is now a third review surface beside Paths and Coverage. It remains useful for no-path results: paginated/filterable grouped identity requests, per-job matrix variants, literal or unresolved role references, source links and an evidence-needed checklist. Matrix/environment substitution locations can be inspected. Results with unresolved identities and no findings open this view automatically. Static observations are not security findings.

JSON and Markdown exports retain the identity observations and guidance. SARIF places summaries/gaps in run properties and diagnostics, never inventing result findings for unknown roles. HTML uses the same inert source text handling, accessibility rules and offline assets. Tests cover 46 variants grouped into 23 declarations, paging, filtering, keyboard movement through all three tabs, and 320px/390px responsive views. The current full gate is 301 passes and one platform skip; 15 accessibility audits are clean. Earlier measurements below are historical milestones.

Status: implementation authorized by the user's 2026-09-16 direction to continue building the repository-first product. This slice completes a focused local review experience; it does not expand the supported provider or policy semantics.

Delivery verified locally: 273 Python tests passed with one platform skip; six real-browser accessibility audits passed with no violations; four export formats, offline reopening, SARIF schema validation, clean-wheel installation and token-free public GitHub acquisition passed. Hosted CI/publication is not performed or implied. Details: TEST_REPORT.md and HANDOVER.md.

## Investigation Amendment: 2026-09-16

The user's follow-up ("build ahead ... still slop") authorizes an evidence/decision workflow beyond the first report screen, not arbitrary provider expansion. The implemented increment adds exact matched predicate inspection, a finding queue with job/role/resource and reach-state filters, keyboard navigation, compact source switching/reanalysis, explicit inventory-vs-parser coverage, and staged multi-control comparison.

The server retains the latest graph/evidence in memory and recomputes copies for selected known trust IDs. Source cleanup is unchanged; no raw source text, executable patch, deployment change or graph engine in the browser is introduced. Comparisons include all modeled jobs, surviving findings and distinct resource counts; alternate trusts remain available until selected. Baseline hash guards prevent stale changes. Up to 128 distinct controls can be selected; JSON and neutralized Markdown change requests describe proposed scope and per-job deltas. Offline HTML has the saved single-statement comparison only.

Acceptance evidence: 280 Python tests passed with one platform skip, 12 real-browser accessibility audits with zero violations, shared/alternate trust regressions (5 -> 5, 5 -> 1, 5 -> 0), rapid-toggle/outage handling, four baseline and two change-request exports. Full details and unverified gates are in TEST_REPORT.md. Earlier first-delivery measurements above remain historical.

## User Promise

A platform/security engineer supplies a local checkout and GitHub slug, or a supported public GitHub URL. They receive declared paths to finite Secrets Manager resources, exact source evidence, unsupported coverage, and a tested trust-removal simulation. Local browser review and downloadable HTML/Markdown/JSON/SARIF use the same deterministic finding result. Deployed access and actual compromise are never claimed verified.

## Build and Acceptance

1. Add SARIF 2.1.0 review results with repository-relative source regions, related locations, code flows, stable fingerprints and explicit no-proof notifications. No-finding results must not become security assurance. Keep existing JSON and Markdown contracts compatible.
2. Check parser, job-identity and remediation boundaries with adversarial tests before presenting composed paths as reliable. Preserve frozen synthetic v0.1 conformance and additive repository v0.2 semantics.
3. Provide one local browser workflow: input -> coverage -> path evidence -> before/after simulation -> export. Use a loopback-only server for local acquisition; static exported reports need no server. The server must enforce host/origin/session boundaries, bounded requests, no permissive CORS, no external binding and no repository execution. No cloud credentials, repository tokens, telemetry or hosted storage.
4. Provide CI reuse with trusted analyzer code separated from untrusted PR source, isolated Python execution, read-only source acquisition and explicit output artifacts. Do not execute target workflows, install target dependencies or upload repository source. SARIF publication is opt-in and remains limited by GitHub permissions/fork behavior. Hosted execution is not claimed until performed.
5. Deliver fresh local example reports, browser interaction/accessibility checks, parser/CLI regressions, packaged asset checks and a runnable install/launch command. Preserve existing visual/research artifacts without adding tabs to the old instrument.

## Boundaries

The repository finding profile remains `repository-attack-path-v0.1`. New renderers do not change evidence confidence or create findings from missing data. The first supported source profile stays exact GitHub Actions OIDC plus literal CloudFormation JSON finite-secret grants; private remote authentication, live IAM verification, Terraform evaluation and arbitrary action execution remain unsupported. A "final" delivery means this tested bounded workflow, not universal cloud-security completeness.