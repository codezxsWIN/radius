# Blast Radius: A Candidate Measurement Standard and Conformance Artifacts for Credential Authorization Reach

Working Paper1 draft,2026-09-09. Contributor attribution pending an explicit authorship agreement; no coauthors, affiliations, acceptance or DOI are invented. CC-BY-4.0 for original text. DOI: NOT ASSIGNED. This draft is not represented as an edit of the unavailable earlier Paper1 document.

## Abstract

Credential compromise is a starting condition, not a uniform measure of consequence. The same leaked key may authorize one operation or a broad set of sensitive resources, and tools may disagree because they count resources, actions, paths or policy assignments differently. We propose a candidate open standard for authorization reach over a declared finite resource-action universe, with explicit constraint models, exact canonical and weighted quantities, and mandatory absolute reach alongside normalized values. A public40-fixture suite exercises three required models and compares exact values, pair sets and explanatory witnesses through a language-neutral protocol. The reference passes120/120 cases. Public-source reconstruction dossiers show supported credential-use mechanisms while leaving all historical top-decile claims unidentified. A500-tenant synthetic privacy experiment finds every exact structural summary unique; a bounded tenant-level aggregate mechanism at epsilon ln2 retains96.8% of synthetic support with1.015 mean count error across21 cells. A prospectively specified NHI sanity check yields54/500 joint successes under a type-neutral population and the same result under a human-broader control, exposing a limitation of the concentration claim. These are artifact and synthetic findings, not validation on real tenants. The planned aggregate dataset remains gated on neutral stewardship, independent privacy review and contribution authority.

## 1. Introduction

Security teams frequently describe the potential consequences of a stolen credential as its blast radius. That phrase is useful but underspecified. A count of accessible services differs from a count of resource-action pairs; direct permissions differ from permissions reachable through role assumption; and a device-bound authentication requirement differs from a second factor already satisfied in a stolen session. Even a correct traversal can produce a misleading normalized score if the denominator includes only granted resources or silently changes between tenants. This creates a measurement problem before it creates an interface problem.

Our objective is an open, inspectable contract that existing tools can implement, not another security management product. The contract fixes the unit of observation, starting conditions, action and constraint registries, invalid-input behavior, exact arithmetic and output disclosures. A public conformance suite permits implementation comparison without a commercial certificate or a proprietary scoring service. The planned dataset would contain reviewed population aggregates derived from local structural summaries; no real dataset exists in this work. Code is Apache-2.0, specification/schema are CC-BY-4.0 and approved aggregate data are intended for CC0 release.

This framing separates three questions that are often conflated. First, does an implementation compute the stated metric on the supplied graph? Second, does a provider normalizer faithfully represent effective authorization, including deny and session semantics? Third, does the metric explain or predict security outcomes in real environments? Exact synthetic conformance addresses the first. Offline normalization fixtures give limited evidence for bounded parts of the second. Public incident narratives and the synthetic experiment expose assumptions relevant to the third but do not answer it empirically.

The primary contributions at this draft stage are a32-requirement candidate specification with eight scoped arguments; a40-fixture public core suite and independently structured expected-value oracle; a reproducible five-dossier reconstruction protocol separating reported facts from invented graph details; and a prospective synthetic study that challenges both summary anonymity and an NHI concentration hypothesis. Negative results are retained. In particular, removing identifiers does not make structural rows anonymous, and majority reach does not imply disproportionate privilege relative to humans.

The proposal makes no claim to invent attack graphs, credential paths, cloud entitlement analysis or risk scores. It also makes no unsupported claim to be the first or only public dataset. Adoption, independent normalizer validation, controlled red-team ground truth and a representative tenant sample remain future work. Neutral institutional custody and independent review are prerequisites before the first real aggregate, rather than branding to add after publication.

## 2. Related Work

The complete related-work section is in RELATED_WORK.md, intended to be incorporated verbatim into the submission. It covers Sheyner et al., MulVAL, Noel/Wang/Singhal/Jajodia, Zelkova, IAM Access Analyzer, Prowler, BloodHound, secret-leakage measurement, CIEM and aggregate privacy. REFERENCES.md and literature-review.csv record verified source scope and explicitly unavailable empirical tenant parameters. This is a newly assembled register, not a falsely recovered prior spreadsheet.

## 3. Metric

Let U be the finite inventory of supported resource-action pairs, declared independently of grants. For credential c and model M, let Q(c,M) be the resource-action projection of the least fixed point of enabled authorization transitions. State includes the acting principal, preventing a group's permission from being transferred between unrelated actors. Resolved denies are subtracted across all allow paths. A secret-acquisition transition requires a read_secret resource state in the appropriate actor context; metadata read is insufficient. A role assumption, credential acquisition or eligible activation adds one escalation step, while ordinary active assignments and membership add zero.

$$B(c,M)=\frac{|Q(c,M)|}{|U|},\quad B_s(c,M)=\frac{\sum_{(r,a)\in Q(c,M)}s_r}{\sum_{(r,a)\in U}s_r},\quad B_w(c,M)=\frac{\sum_{(r,a)\in Q(c,M)}w_a}{\sum_{(r,a)\in U}w_a}.$$

The bounded variant restricts Q to paths whose escalation cost is at most k but retains the full denominator. U must be nonempty; all-zero sensitivity yields an undefined/null sensitivity radius, not zero. Every normalized output is accompanied by absolute reach, universe size, model, parameters and coverage. Decimal input weights become exact fractions; display rounding cannot determine rank.

The default model blocks independently required devices and approval, while treating declared network/time restrictions as satisfiable. Strict additionally blocks network/time. Session-theft-aware permits reuse only of an explicitly completed authentication device factor on an issued token, not a new resource gate or independent approval. These are attacker-assumption profiles, not predictions of control bypass. Audience, expiry, arbitrary OR policies and conjunctive credential collaboration require new profiles.

The candidate specification proves bounds by set inclusion, effective-allow monotonicity for fixed denies/universe, independent-source union under unary transitions, constraint inclusion, bounded ordering, finite termination, isomorphism invariance and determinism. It also supplies counterexamples to unqualified monotonicity and collaboration claims. Gini can increase when reach decreases: changing(1,1) to(0,1) raises Gini from0 to1/2. Thus reducing a concentration statistic is not a universal security objective.

Conformance serializes reduced rational strings and deterministic witnesses. A SHA-256 snapshot digest binds canonical graph bytes; the result digest excludes itself. Neither hash establishes completeness or truth of the source. Private HMAC signing in the legacy demo is separate and not required for third-party conformance.

## 4. Four-Arm Evaluation

### Arm A: Synthetic Structure and Property Stress

Completed: stable edge-case fixtures, property/adversarial tests and500 paired tenant configurations under three registered grant regimes. Graph hashes, protocol hashes and per-tenant outcomes are published. The earlier prototype scale runs are retained separately:10000 principals and2000 resources in51.63 seconds;50000 in215.38 seconds. Those are one-machine synthetic timings, not new research samples or production throughput guarantees.

Failure criterion: any counterexample to a stated property within its assumptions, an incorrect reachable pair, incorrect bounded cost or sensitivity to an input permutation requires a model/code correction and a permanent regression. The new population omits complex groups and denies; it complements rather than replaces adversarial fixtures. The NHI joint-success criterion is prospectively fixed: fewer than half the principals are NHI and their weighted union exceeds half the universe, evaluated per tenant with a Wilson interval. Null54/500 and reversed54/500 outcomes demonstrate that the claim alone does not measure disproportion relative to humans. Positive control250/500 remains inconclusive under the unchanged majority-of-tenants rule.

### Arm B: Public Conformance

Completed:40 stable fixtures with human derivations, all three required models, exact canonical/sensitivity/action/bounded outputs, population statistics and witnesses. The independent expected-value path uses whole-edge relaxation and a pairwise Gini formula, not the optimized engine's queue or rank-sum statistic. Shared schema/serialization code and a common author remain correlated-error risks. The external CLI runner compares120 cases twice, rejects malformed/tampered suite manifests, and reports per-requirement outcomes. Reference result:120/120 passes for revision2 digest recorded in CONFORMANCE.md.

Failure criterion: any mismatch, crash, timeout, invalid JSON, nondeterministic bytes or required-model omission fails the claim. A finite suite is not a formal proof or comprehensive provider certification. Manual disclosure/governance obligations require separate review. A JavaScript reference written in this session now also passes 120/120 external cases, using BigInt rational arithmetic and whole-edge relaxation without invoking Python. This provides implementation diversity but not independent authorship. Its schema-keyword subset and wire-number compatibility profile remain review boundaries. The final Python regression suite passes 179 tests, including malformed protocol/runner input and a 21-credential p95 case.

### Arm C: Controlled Red-Team Ground Truth

NOT PERFORMED. No cloud tenant, credential or live endpoint was probed in this session. A future preregistered evaluation should create researcher-owned isolated test environments with known allow/deny/conditional boundaries, independently enumerate permitted resource-action outcomes, and compare predicted paths with explicitly authorized benign access checks. No production exploitation, secret exfiltration or third-party account testing is authorized by this artifact.

Before execution, fix at least30 distinct scenarios per proposed provider profile, independent reviewers, complete expected denominators, permitted read-only probes and stop conditions. Report false-positive/negative pair counts, coverage gaps and collector provenance. Any unsupported condition silently emitted as an allow is a failure, even if aggregate scores appear plausible. Record unsuccessful probes separately from proof of policy denial: network errors and stale tokens can otherwise manufacture false negatives. This arm cannot be claimed complete from synthetic fixtures or incident stories.

### Arm D: Public-Incident Reconstruction

Completed as bounded mechanism dossiers: Snowflake2024, Beacon2026, Hugging Face2026 and CircleCI2023 have primary incident support; MLflow CVE-2026-64849 is explicitly a vulnerability/post-acquisition scenario without a named victim IAM graph. Every case separates facts, assumptions, minimal graph, three-model output and a hypothetical control. Four minimal models have1/1 baseline reach; CircleCI has0/1 under default/strict and1/1 under session-aware. Controls reduce the represented capability to0. These trivial ratios are deliberate abstractions, not estimates of historical scope.

All historical top-decile results are unidentified because full preincident populations and inventories are absent. Ten executed assumed countermodels hold each completed universe fixed and place the same target at rank 1/10 or 10/10 by changing only unreported background grants. They establish nonidentifiability, not estimates of historical background permissions. The protocol accepts reviewer countermodels and conflicting sources. Falsification occurs if a claimed authorization path requires unjustified capability, an asserted control does not change the modeled pair, or evidence contradicts a stated fact. Hugging Face software exploits and MLflow initial SSRF are outside the core; concealing that boundary would overstate explanatory coverage.

## 5. Data and Privacy Evaluation

The exact37-field count/histogram vectors were unique in500/500 synthetic tenants; rounding counts in tens left161 unique and490 rows in groups below10. The minimal release projection had no unique rows, but16 rows were in groups of7 or9. Structural coarsening is therefore not treated as an anonymity guarantee.

The prespecified aggregate uses a fixed21-cell histogram with one contribution per deduplicated tenant. Difference-of-geometric integer noise with q1/2 gives epsilon ln2 for add/remove-one adjacency. Noisy threshold20 targets support k10 with a family small-cell release bound below1%; suppression is postprocessing, not an exact-support side channel. Across200 seeded trials, mean count MAE including suppression was1.014762, p95 MAE1.285714 and retained true support96.8%. The rare tail is lost and the many zero cells make overall MAE look favorable; neither fact is hidden.

This mechanism's proof assumes independent randomness and enforced contribution bounds. Public seeds protect no real data, and the in-memory budget ledger is not durable production enforcement. Neutral custody, consent, deduplication, legal/ethics review, a private reporting channel and independent privacy review are unmet publication gates. Counts/histograms cannot recover the overlap required for the NHI primary union statistic, so the planned payload cannot yet test that real-data hypothesis.

## 6. Limitations and Research Claims

The current reference accepts synthetic graphs only, provider adapters cover bounded offline profiles, and the source literature does not supply empirical identity-count/degree distributions for the generator. The additional Kubernetes profile covers only explicit read-only RBAC collections and rejects writes, impersonation and unsupported authorizers; 17 tests do not establish full-cluster parity. Conformance expectations and implementations share an author and some intended semantics. Formal arguments are human-readable, not mechanized or externally reviewed. Public disclosures select unusual events and do not provide representative controls. A scalar radius can be diluted by an enlarged universe, motivating mandatory absolute reach and declared granularity. Sensitivity assignments encode judgments, not objective harm.

The defensible current claim is artifact reproducibility and explicit semantics, not industry adoption, predictive incident ranking, complete IAM analysis or an existing public enterprise dataset. These limitations shape the next study rather than disappearing into an unqualified headline.

## Appendix A: Artifact

Environment: Windows, CPython3.12.10, jsonschema4.26.0; pytest9.0.3 and coverage tooling recorded in project configuration. The repository provides an offline src-layout package named blastradius. Run from the project directory:

```powershell
.venv/Scripts/blastradius.exe conformance run --tool '.venv/Scripts/python.exe -B -m blastradius conformance adapter'
.venv/Scripts/python.exe -B tools/build_reconstructions.py
.venv/Scripts/python.exe -B tools/run_research.py
.venv/Scripts/python.exe -B tools/verify.py
```

Specification: spec/METRIC_SPECIFICATION_v1.0-draft.md and registries.json. Conformance: conformance/manifest.json, fixtures and reports/reference. Privacy: STRUCTURAL_SUMMARY.md, PRIVACY_ANALYSIS.md, schema/structural-summary-v1.0-draft.schema.json and research/privacy-results.json. Prospective protocol: PREREGISTRATION.md, research/RUN_PLAN.md and reproducibility-receipt.json. Reconstructions: RECONSTRUCTION_METHOD.md and reconstructions/. Governance: GOVERNANCE.md, NEUTRALITY.md and CODE_OF_CONDUCT.md.

No cloud credentials, real tenant exports or private signing keys are required for these commands. The single existing self-contained HTML demo is supplementary and has not been regenerated over user edits. Exact source and report hashes, local commit identity and final verification are recorded in TEST_REPORT.md/HANDOVER.md. Existing checkpoint ZIPs preserve prior states; local OneDrive saves do not prove cloud synchronization. Public archival deposit, DOI, venue submission and neutral-host acceptance have not occurred.
