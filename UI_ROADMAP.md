# Visual Instrument Roadmap

Visual-session extension of Blast Radius, not an enterprise console. Status is evidence-based: shipped means implemented and checked; stubbed means a working partial surface with an unmet criterion; specified means this acceptance paragraph exists but the feature is not implemented; backlog is explicitly deferred without a current implementation. No real dataset or exclusive novelty claim is asserted.

## Status Summary

shipped: 7; specified: 61; stubbed: 32. T1 goals: 28. See UI_TEST_REPORT.md for actual executed evidence, not inferred completion.

## A. Foundations

### G1 T1: Static architecture

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: One self-contained file opens without a server; no telemetry or network dependency. The build records vendored asset hashes and leaves engine result v0.1 unchanged.

### G2 T1: Shared tokens

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: UI, SVG and paper exports consume the same JSON tokens. Color-vision simulations and contrast measurements are saved and any failed pair is repaired before a pass claim.

### G3 T1: Open icon vocabulary

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Principal, credential and constraint kinds resolve to attributed CC-BY SVG icons. Accessible names remain available without relying on the icon or color.

### G4 T1: Normative visual annex

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Publish Visual Vocabulary v0.1 with area, step, certainty, fixed-sensitivity and stamp rules. Every supported renderer is checked against the accompanying checklist.

### G5 T2: Component gallery

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A gallery renders each implemented view against an exercising result fixture. Empty, blocked, undefined and long-label states are included rather than only a flattering default.

### G6 T2: Semantic zoom

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Navigate only hierarchy explicitly present in input metadata. Acceptance requires stable breadcrumbs and reversible parent/child transitions; the current schema does not supply subscription/group hierarchy, so it is not fabricated.

### G7 T2: Search grammar

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Document type, radius comparison and name predicates with explicit error behavior. The same parsed predicate filters all relevant population visuals and their text tables without changing the full resource denominator.

### G8 T2: Shareable view state

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A URL fragment identifies the snapshot hash, view, model and ordinal selection. No tenant or credential names/IDs enter the fragment; reopening a known embedded snapshot restores the state.

### G9 T2: Deterministic pseudonyms

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: One control replaces all displayed names and relevant export labels with stable local pseudonyms. Acceptance includes titles, tables, tooltips, evidence, annotations and a visible redaction stamp; pseudonymization is not anonymity.

### G10 T2: Light dark print

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Light and dark UI tokens preserve contrast; figures remain a declared paper style. An A3 print portrait removes controls without omitting provenance or implying an independent report.

## B. Physical Reach

### G11 T1: Blast disc

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Disc area follows canonical radius on a fixed reference footprint; marks encode resource-action pairs by first escalation step and sensitivity. Zero reach has zero filled area and every mark has an evidence alternative.

### G12 T1: Step propagation

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Play, pause, backward/forward step and scrub expose the same step ordering. Reduced motion presents final state without losing manual step access; elapsed animation time never claims attack duration.

### G13 T1: Tenant treemap

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Rectangle area is absolute reach and color is principal type. A p95 outline has an explicit population/tie rule, zero-area credentials remain in the table, and selection opens the corresponding disc.

### G14 T2: Reach sunburst

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Partition one credential's unique pairs by resource type, sensitivity bin and action without duplicating paths. Acceptance requires conserved counts at each hierarchy level and a readable linear table fallback.

### G15 T2: Plane cross-section

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Separate principal, binding and resource strata using explicit node kinds. No implied cloud boundary or network distance is added; crossing links retain direction, provenance and escalation labels.

### G16 T2: Gravity layout

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Do not ship orbital distance as a second unexplained risk score. A proposed alternative is fixed-axis small multiples; acceptance requires a declared distance function and evidence that overlap does not hide small credentials.

### G17 T2: Egocentric graph

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Show selected-credential reachable states with deterministic layout and an explicit node budget. Bundling must expose the underlying multiplicity and cannot erase distinct actor contexts or deny semantics.

### G18 T2: Same-scale small multiples

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Render compatible tenant or declared-group results with a common full-universe reference area. Acceptance rejects incomparable resource granularities and labels every numerator and denominator.

### G19 T2: Granted versus used

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Usage is absent from the current result contract, so no inner usage ring is invented. A future version must define observation window, missingness and action-level matching before two rings can be compared.

### G20 T2: Model outlines

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Overlay only independently computed default, strict and session-aware discs with named outlines and a common reference area. Atomic model changes avoid implying that interpolated states are valid authorization models.

## C. Paths

### G21 T1: Subway witness

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Stations and directed edges represent the engine's chosen explanatory witness. Escalation interchanges, barriers, unknown/assumed segments and step versus hop counts must remain distinguishable.

### G22 T1: Station provenance

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Keyboard and pointer activation expose connector, source API, observed_at and evidence reference. Acceptance checks every node/edge station and restores focus when its evidence dialog closes.

### G23 T2: Alternative paths

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Show at most three independently enumerated valid alternatives with their actor contexts and divergence points. The current result includes one canonical witness; alternatives need verified enumeration rather than duplicated decorative routes.

### G24 T2: Path intervention

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A binding station can open the existing binding-removal counterfactual. Arbitrary edge deletion is not mislabeled a supported binding intervention; unsupported edge kinds explain the limitation.

### G25 T2: Deterministic narrative

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Build a factual sequence from witness edge kinds and provenance, with no language model. Copy exports plain text and retains the model, evidence and synthetic qualification rather than making a ticketing integration.

### G26 T2: Research summaries

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Replace the executive-sales framing with a data-derived research abstract for selected credentials. Acceptance requires exact reach, assumptions and limitations in exported Markdown, with no predicted-loss prose.

### G27 T2: Secret unfolding

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Reveal only explicitly modeled stored-credential links after the required read_secret capability is present. Metadata access must not unfold invented credentials or imply that all vault contents were read.

### G28 T2: Trust bridges

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Use platform regions only when an input extension provides authoritative boundary labels. Every bridge must map to an explicit assumption/federation capability; provider names in provenance are not sufficient.

### G29 T2: Guest crossings

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A versioned boundary/guest classification is needed before counting crossings. Acceptance excludes guessed guest status from names or domains and shows unknown classification separately.

### G30 T2: Witness by model

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Display the independently selected path or an explicit absence for each required model. Do not simply remove stations from a different model's witness and call the remnant a valid route.

## D. Interaction

### G31 T1: Model control

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Switch all credential results to the selected computed model and list every delta against a fixed baseline. Discrete redraw replaces misleading intermediate-model numeric tweening; reduced motion preserves all comparisons.

### G32 T1: Binding surgery

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Remove or add one validated binding and recompute per-credential and tenant metrics on a fixed universe. Restoring the source snapshot is reversible; invalid actions and graph shapes reject without retaining a misleading score.

### G33 T1: Evaluated changes

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Show five supplied single-binding evaluations and their before/after p95 discs. State candidate count and zero-improvement outcomes; never label the set globally optimal or multi-change minimal.

### G34 T2: Path choke points

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Count use by the selected canonical high-radius witnesses, not all possible paths. Acceptance labels that limited denominator and recomputes a proposed removal before claiming an actual effect.

### G35 T2: Weight policy editor

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Edit declared sensitivity weights with bounds and a visible policy-choice notice. The changed weights and result hash must be exported; no silently updated canonical radius or empirical-risk interpretation is permitted.

### G36 T2: Variant disagreement

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Compare ordinal rankings for canonical, sensitivity and action variants using deterministic tie rules. A flag explains the chosen threshold and is not a claim that a tool or tenant is gaming deliberately.

### G37 T2: Local annotations

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Notes remain in opt-in browser storage and export as a versioned JSON sidecar. They never modify engine evidence or silently enter public exports; redaction and deletion are testable.

### G38 T2: Snapshot comparison

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Accept two compatible results and show added/removed capabilities with fixed population and universe qualifications. Unknown inventory coverage must prevent a false improvement claim from missing resources.

### G39 T2: Target planning

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: The engine evaluates single changes, not a global optimizer, so no minimal ordered plan is fabricated. A future planner needs a declared search objective, cost model and optimality bound; current evaluated choices remain separate.

### G40 T2: Command palette

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A keyboard command dialog exposes all supported view and export actions with focus return. Commands must mirror visible controls and never execute network or platform mutations.

## E. Population

### G41 T1: Lorenz and Gini

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Compute a sorted cumulative curve from per-credential reach and annotate the exact top share. The sum may overlap across credentials and must not be described as unique tenant surface.

### G42 T1: Typed histogram

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Use fixed canonical bins and grouped principal-type counts with a threshold marker. Linear and explicitly labeled log(1+count) scales preserve zero counts without deceptive log stacking.

### G43 T2: Benchmark position

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: No real anonymized comparison population exists in this artifact. A future percentile requires a compatible released cohort and uncertainty; synthetic distributions cannot be presented as enterprise percentiles.

### G44 T2: Public benchmark shell

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A static methodology/download view may render the approved aggregate file. It must visibly state synthetic or pending status, release budget and cohort limits, with no pretend contributor count.

### G45 T2: State report figures

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Generate report charts only from a released aggregate and preserve suppression/noise metadata. The existing report template remains a template until governance and real-data gates are satisfied.

### G46 T2: Reach flow

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Naive Sankey flows can double-count shared bindings and violate conservation. Redesign around an explicitly unique attribution scheme or pair-overlap matrix; acceptance proves conservation and explains overlap losses.

### G47 T2: Boundary chord

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A chord requires declared boundary metadata and a precise directed pair-count definition. It cannot infer subscriptions/accounts from resource names or convert duplicate trust paths into additional exposure.

### G48 T2: Team budgets

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Teams, budgets and time snapshots are not supplied by the current contract. Specify an optional policy sidecar and comparable history; no invented team scorecard or compliance status is shown.

### G49 T2: Resource shadow map

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Invert computed reach to count how many credentials reach each resource-action pair. Rank exposure with sensitivity and principal-type mix, keeping credential counts distinct from unique resources.

### G50 T2: Synthetic population explorer

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Parameter controls invoke a documented local synthetic generator with a fixed seed. Every resulting distribution says illustrative and never uses animation as a substitute for engine completion.

## F. Non-Human Identities

### G51 T1: Non-human lens

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Filter service, managed, workload and AI-agent identities while comparing human/NHI count, median and p95. The denominator and whether statistics concern credentials or principals are explicitly labeled.

### G52 T2: Agent budget

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A gauge needs an explicit policy ceiling with a version and scope. No default threshold is falsely described as a real agent task budget; missing ceilings show unavailable.

### G53 T2: Identity lineage

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Creation lineage is not inferred from an authorization edge. A future creator relation requires provenance and time, with unknown creators preserved rather than a fabricated branching story.

### G54 T2: Lifetime strip

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Validity and last-used windows require corresponding fields and observation coverage. Missing telemetry must not become never-used, stale or expired; absent data renders an unavailable state.

### G55 T2: Radius time-lapse

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Animate only a sequence of comparable, independently computed snapshots. Assignment attribution must be proven by a counterfactual, not assumed from a simultaneous timestamp.

### G56 T2: Threshold regressions

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Compare exact before/after radii for shared credentials and label inventory/model changes. New identities and missing observations form separate classes, not automatic regressions.

### G57 T2: Ephemeral timeline

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Task appearance and expiry require explicit validity evidence. A view must distinguish deletion, observation gaps and real expiration; no synthetic clock progression masquerades as recorded history.

### G58 T2: Federation lens

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Use explicit trust edges with declared source/target identity boundaries. The lens must retain credential scope and unknown OIDC conditions rather than treating every federation label as unconditional access.

### G59 T2: Task containment

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Require a supplied task-scope set and compute set difference against reachable pairs. A missing task scope cannot yield zero out-of-scope access or a containment success badge.

### G60 T2: Human machine violin

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Use a declared bandwidth and enough observations for a meaningful density. For small fixture populations use an exact dot plot instead of a smooth distribution that implies unsupported precision.

## G. Evidence and Privacy

### G61 T1: Certainty overlay

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Dash explicit assumed edges and compute dependent reach by removing those allow transitions. Unknown metadata remains unknown; illustrative annotations, alternative exact routes and the ratio denominator are disclosed.

### G62 T1: Reproducibility stamp

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Every view and SVG/PNG/PDF includes snapshot hash, engine/schema, model, parameters, snapshot time and vocabulary version. Redaction and illustrative status persist through exports.

### G63 T2: Observation timeline

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Plot supplied observation times only, not inferred event occurrence. Staleness thresholds are declared policy choices and simultaneous fixture timestamps are not presented as a real history.

### G64 T2: Connector freshness

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Compute age relative to an explicitly selected reference time, not ambient time in deterministic exports. Unknown or mixed source coverage must not receive a healthy freshness badge.

### G65 T1: Structural silhouette

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Render the exact local dry-run payload and make raw JSON accessible. Rename the anonymized claim: exact structural summaries are not anonymous and the current instrument submits nothing.

### G66 T2: Local versus shared

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Compare the closed dry-run field allowlist with fields retained locally. No upload button or submission promise is added; the exact difference is inspectable in JSON and text.

### G67 T2: Linkage warning

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Show measured synthetic uniqueness with its population and limitations before any hypothetical submission context. It is not a real-company re-identification probability or a safety certificate.

### G68 T2: Network ledger

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Instrument or audit attempted runtime requests and report local file/embedded asset behavior. Acceptance includes a no-network test, not merely a decorative offline badge.

### G69 T2: Data and computation

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Every shipped chart exposes its tabular values and the specification clause/code path used. Truncation, pagination and filter scope are explicit; unsupported computations cannot borrow an unrelated definition.

### G70 T2: Assumption ledger

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Show declared sensitivity choices, visual approximation annotations and public-reconstruction assumptions. Ledger entries are evidence context, not engine permissions or externally validated facts.

## H. Teaching

### G71 T1: Fixture playground

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Edit a tiny graph, add resource/grant/constraint and recompute through the reference engine. Invalid presets and mutations suppress scores and show rejection; derivations remain attached to their original fixture, not falsely to edited graphs.

### G72 T1: Reconstruction gallery

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Each sourced minimal graph selects its credential and exposes control and assumption ledger. Historical rank remains unidentifiable; a toy first rank cannot become a real top-decile claim.

### G73 T2: Guided tour

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A short optional sequence walks through actual evidence states without blocking ordinary navigation. Each overlay is keyboard-dismissable and restores focus; no scripted number differs from the engine result.

### G74 T2: Reading overlay

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Provide optional encoding definitions and a text equivalent per view. It must not cover critical controls or turn the instrument into a marketing landing page.

### G75 T2: Specification browser

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Map numbered requirements to frozen fixtures and code paths. Manual requirements are identified as manual; a click must open the actual relevant fixture rather than a generic success page.

### G76 T2: Conformance viewer

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Show requirement-by-tool outcomes and explicit manual/uncovered cells. Any downloadable self-claim includes suite/tool version and never implies certification or external endorsement.

### G77 T2: Glossary

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Terms such as radius, absolute reach, p95 and escalation expose concise definitions on keyboard focus/activation. A tooltip cannot be the only way to obtain a critical definition.

### G78 T2: Talk mode

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Use deterministic pseudonyms, a declared larger layout and reversible prepared state sequence. No names remain in the DOM, figure metadata or evidence drawer when redaction is claimed complete.

### G79 T2: Embedded static demo

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Publish an embeddable fixture-driven visual with the same engine result and vocabulary stamp. It must remain useful offline and retain a text alternative in constrained hosts.

### G80 T2: Classroom exercises

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Questions compare learner predictions with exact fixture outcomes and explain counterexamples. Correctness is computed, not a hardcoded visual celebration; no personal learner telemetry is retained.

## I. Export

### G81 T1: Byte-identical SVG

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Same input, tokens, font bytes and options produce byte-identical SVG across repeated rendering. The test covers all renderers and input permutations allowed by the contract.

### G82 T1: IEEE export

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Export SVG, PNG and PDF at declared single/double-column widths with embedded open fonts and full stamps. Tests inspect dimensions, nonblank pixels and PDF font embedding; tiny illegible scaled labels are not a publication-quality pass.

### G83 T1: Paper figure command

Status: **shipped**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Provide make figures and a direct no-make equivalent that generate the complete declared figure set from result JSONs. Captions identify the input hashes, encodings, widths and synthetic limitations.

### G84 T2: Embeddable component

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A blast-radius custom element consumes a result and options with no network requirement. It retains keyboard/evidence alternatives and rejects unsupported result formats instead of silently rendering arbitrary data.

### G85 T2: Terminal view

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A tty formatter may show sparkline bins, ranked counts and ASCII witness with the same definitions. It must preserve undefined values and work without terminal color; no extra live collector is introduced.

### G86 T2: Notebook wrapper

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A notebook widget wraps the static component or embeds self-contained HTML safely. It needs a tested notebook frontend contract and cannot claim widget support from an unexecuted screenshot.

### G87 T2: Declarative charts

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Publish a versioned declarative chart description for statistical views, including data fields, transforms and scale domains. Community extensions must reproduce exact tables and stamps.

### G88 T2: View plugins

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A static manifest declares inputs, encodings, dependencies, licence and review status. Loading arbitrary untrusted script plugins is out of scope; review must cover truthfulness, privacy and accessibility.

### G89 T2: Markdown deltas

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Export per-credential before/after Markdown from compatible results, with evidence and fixed-universe qualifications. This is a local artifact, not a ticketing or CI service integration.

### G90 T2: Headless screenshots

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: A local command opens a view, waits for fonts/engine readiness and saves a reproducible viewport capture. Screenshot state and viewport metadata are recorded; hidden-tab animation artifacts are not mistaken for UI failures.

## J. Quality

### G91 T1: Accessibility gate

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Run WCAG2.2 AA-tagged automated checks with zero critical issues on all shipped views and keyboard workflows. Report full results and manual gaps; zero automated violations alone is not full WCAG certification.

### G92 T1: Text alternatives

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Every chart has a narrated description and inspectable data table; paths have deterministic prose. Optional speech is opt-in and never required to access evidence.

### G93 T2: Reduced motion

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: The operating-system preference disables propagation animation and all optional transitions without omitting a reachable step. Manual step/scrub and before/after evidence remain available.

### G94 T1: Large-population budget

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Use canvas for10000 credentials and explicit aggregation for50000, based on fresh engine results. Report observed frame/render timings, hardware/runtime and scope; do not assert60fps from a static screenshot.

### G95 T1: Visual regression

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Save and compare screenshots for every shipped view on explicit fixtures at desktop/mobile dimensions. Tests report count and pixel differences with deterministic state/fonts; baselines are review artifacts, not unexplained golden files.

### G96 T2: Browser matrix

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Record actual Chromium, Firefox and Safari execution status separately. An unavailable engine is not marked pass; compatibility limitations and a viable external test plan remain visible.

### G97 T2: Internationalization

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Externalize English strings and use locale-aware formatting under a declared locale option. Deterministic figure exports fix the locale and do not silently depend on the host machine.

### G98 T2: UI threat model

Status: **stubbed**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: No telemetry, eval or runtime CDN; strict CSP blocks connections and unsafe content insertion. Document the inline static-bundle exception, dependency versions, hash inventory and private-signature verification limitations.

### G99 T2: Design-system guide

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Document tokens, accessible component states, encoding rules and contribution checks. New visuals need an exercising fixture, common-scale proof, text alternative and deterministic export test.

### G100 T1: Complete goal register

Status: **specified**. Owner: Unassigned; maintainer/reviewer slot.

Acceptance: Maintain all100 stable goal IDs with shipped/stubbed/specified/backlog status, acceptance paragraph and owner slot. Include ten new theme proposals, explicit rejected redesigns and a visual-conformance checklist.

## Proposed

### A: Denominator ruler

Show the full-universe footprint beside every disc so dilution is physically visible. Acceptance: unchanged absolute reach with a larger universe shrinks only the ratio disc, and both denominators remain visible. Status: built in the disc reference outline. Owner: unassigned.

### B: Step-mass strip

A compact strip records newly reached pair counts at each escalation cost. It makes a large one-step jump visible without suggesting elapsed attack time; acceptance compares each bin with minimum path costs. Status: proposed. Owner: unassigned.

### C: Witness receipt

Hash the ordered witness edge IDs and display a compact receipt next to the path. It exposes path changes even when the final score is unchanged; acceptance checks stable receipts and changed-route counterexamples. Status: proposed. Owner: unassigned.

### D: Zero-effect intervention ledger

Show evaluated changes that do not affect p95 alongside changes that do. This prevents the top-five display from hiding redundant paths; acceptance uses actual exhaustive single-binding results and avoids a global optimum claim. Status: proposed. Owner: unassigned.

### E: Overlap dual ledger

Place summed credential-pair exposure beside the unique pair union. The gap physically demonstrates why a Lorenz annotation is not total exposed surface; acceptance derives both from exact reach sets. Status: proposed. Owner: unassigned.

### F: Count-versus-reach dumbbell

Compare NHI population share with its share of summed exposure, with human overlap separately labeled. Acceptance avoids interpreting an extensive union as disproportionate individual privilege. Status: proposed. Owner: unassigned.

### G: Unknown-evidence floor

Reserve a visible unknown band when certainty metadata is absent rather than drawing an empty uncertainty overlay. Acceptance tests a result with no ledger and prohibits an automatic0% confidence burden. Status: built as explicit unknown state. Owner: unassigned.

### H: Rank countermodel switch

Toggle two source-consistent population completions that move the same compromised credential from first to tenth. Acceptance labels both invented backgrounds and keeps actual historical rank unidentified. Status: proposed. Owner: unassigned.

### I: Reproduction receipt

A one-click local proof compares two SVG byte streams and exposes their digest and options. Acceptance detects a changed token or option and never uses a visual similarity score as byte identity. Status: proposed. Owner: unassigned.

### J: Truthfulness lint

Automated checks inspect marks for declared denominators, fixed scales, stamps and unknown states before visual review. Acceptance fails deliberately malformed SVG metadata and pairs a machine report with manual review gaps. Status: proposed. Owner: unassigned.

## Visual-Conformance Checklist

- Disc area ratio and full-universe guide; zero area at zero reach.
- Ring k equals escalation cost, not graph hops or time.
- Fixed sensitivity bins and categorical icons/text.
- Assumed edges dashed; missing certainty unknown.
- Common before/after scales, population and denominator disclosures.
- Summed versus unique reach explicitly distinguished.
- Every view/export carries complete reproducibility stamp.
- Keyboard evidence, focus restoration and data alternatives.
- Reduced-motion parity; deterministic SVG bytes and reviewed screenshots.
- Embedded fonts and tested physical figure dimensions.
- No runtime network, telemetry, invented usage or historical rank.

## Decisions for Amit

Ratify the visual vocabulary only after independent review; choose whether the illustrated uncertainty sidecar belongs in a future standard profile; provide approved usage/hierarchy/task-scope data before time/budget views; arrange human assistive-technology and Safari/Firefox testing where local engines are unavailable.
