# Decisions

| ID | Decision and One-Line Rationale | Confidence |
| --- | --- | --- |
| D01 | Isolate this build in `blast-radius-v0.1/` with src layout; preserve the previously verified G0 project. | High |
| D02 | Use the located charter plus the compressed specification; Metric v0.2, Engineering v0.1, its fixtures, Paper 1 and the specific literature matrix were not found in the designated folders. | High |
| D03 | Save checkpoints outside the read-only Cowork-managed folder, under OneDrive/Blast-Radius-Build/2026-09-09. | High |
| D04 | Guard can_read_secret with an explicit actor-local read_secret resource capability; a principal-to-credential edge alone would overstate vault metadata permissions. | High |
| D05 | Freeze resource/action universe for permission-only properties and publish absolute reach; normalization otherwise permits denominator dilution. | High |
| D06 | Use snapshot observed_at as deterministic result generation time, not wall-clock analysis time; runtime timing belongs in TEST_REPORT. | High |
| D07 | Use stdlib HMAC-SHA256 with a generated, external local key; repeatability holds for the same graph, parameters and signing key, and HMAC is not public-verifier attestation. | High |
| D08 | Keep zero sensitivity valid; when every resource weight is zero the weighted radius is undefined, reported null rather than a misleading zero. | High |
| D09 | PIM eligibility permits activation unless gated; activation is modeled as one escalation step, unlike an already-active assignment. | Medium |
| D10 | Denies subtract actor-local capabilities across all allow paths and remain independent of attacker-satisfiable constraints; otherwise a stricter model could accidentally remove a deny and increase reach. | High |
| D11 | Normalize the entire analysis graph before constructing report witnesses; a permutation regression exposed that hashing normalization alone was insufficient for signed byte determinism. | High |
| D12 | Evaluate every allow-binding removal for small demo graphs; explicitly defer exhaustive recommendations above 200 credentials or 5000 edges instead of sampling and claiming a global optimum. | High |
| D13 | Reconstruct the charter's classic canonical cardinalities on a declared 48000-pair graph; its absent topology and weighting profile do not justify claiming its illustrative weighted numbers were reproduced. | High |
| D14 | Delegated OAuth grants are inventoried, not treated as app-only access; a consent record alone does not establish a compromised user session or token context. | High |
| D15 | Require explicit synthetic applicability/approval maps for complex CA and PIM; missing context must not silently become unconditional access. | High |
| D16 | Use the corrected, fetched Key Vault list API version 2024-11-01; keep any unverified endpoint/permission pair labeled in the manifest. | High |
| D17 | Separate vault access-policy and RBAC modes; a data-plane grant in the inactive authorization system must not create reach. | High |
| D18 | HMAC verification runs before report export; static HTML carries no secret and cannot independently authenticate itself or verify a signature without the separately held key. | High |
| D19 | The demo's shared nesting intentionally produces 100% above-threshold credentials and low Gini; these measured synthetic statistics are not evidence about real organizations or the research thesis. | High |
| D20 | Keep a library-only live GET transport disabled by default and no live CLI path until protected persistence and authorization semantics are reviewed; this is an explicit G4 limitation, not a hidden stub. | High |
| D21 | Preserve full schema validation in both scale runs; it dominates runtime, but removing validation to meet a headline target would weaken the claim. | High |
| D22 | Do not retain the 113 MB stretch result in every zip; retain reproducible commands, topology, timing and verification summary instead, while the demo and classic results remain available. | High |
| D23 | Canonical and weighted metrics use exact fractions internally; nearest-rank p95 and strictly-above-threshold share are explicit definitions, not library-default guesses. | High |
| D24 | Restrict what-if additions to the new binding's own assignments/grants/constraints; otherwise an input could smuggle an unrelated escalation change into a claimed one-binding scenario. | High |
| D25 | Define principal reach as the union of independently evaluated owned credentials; conjunctive multi-credential authorization can exceed such a union and is explicitly outside this prototype claim. | High |
| D26 | Use single-pass HTML placeholder substitution; recursively replacing template markers inside embedded data can corrupt JSON or create injection risk. | High |
| D27 | Keep the static dashboard as the deliverable of record and do not publish a hosted app without a need or deployment plan; it is already fully interactive offline. | High |
| D28 | AWS stretch support is explicitly bounded; reject conditions, boundaries, nontrivial SCP/RCP and unsupported trust instead of claiming a union of identity policies is full IAM evaluation. | High |
| D29 | Structural dry-run output is not called anonymized: exact counts can identify a tenant, and no differential privacy, release accounting or submission endpoint exists. | High |
| D30 | Separate access-qualified group closure from static deny membership; a device-gated membership cannot supply secret-acquisition authority, while stronger constraints must not erase an applicable deny. | High |
| D31 | Ship a read-only GitHub Actions workflow but label hosted execution unverified; only its underlying local commands have actually run in this session. | High |
| D32 | Permit deliberate deny changes in explicit what-if and show positive risk deltas; keep automatic risk-reduction recommendations restricted to allow-binding removals. | High |
| D33 | Test the wheel with Python -I outside the source tree; an editable install alone would not prove schema/template assets were packaged. | High |
| D34 | Reject malformed signature/manifest object shapes explicitly; security verification must fail with a controlled error rather than an accidental traceback. | High |
| D35 | Standards direction supersedes the product roadmap: retain only metric/reference/conformance/data artifacts and the single existing demo; no commercial integrations or management plane. | High |
| D36 | Do not claim an existing or uniquely public real-world dataset: this session contains synthetic/public evidence only, with no real submissions or novelty census. | High |
| D37 | State monotonicity only for fixed-universe, fixed-deny effective-allow changes; group-deny applicability and Gini furnish counterexamples to broader claims. | High |
| D38 | Add session-theft-aware only for explicitly completed token-authentication device factors; fresh approval and resource controls remain binding. | High |
| D39 | Freeze the NHI protocol before new population generation; counts/histograms cannot identify union overlap, so the real-data primary test needs a separately reviewed bounded local statistic. | High |
| D40 | Report incident top-decile position as unidentifiable when the public record lacks a preincident credential population; arbitrary background credentials would manufacture support. | High |
| D41 | Use OneDrive/blast-radius for this standards extension while preserving the earlier prototype checkpoints; the requested documents remain missing and are not reconstructed as if authoritative. | High |
| D42 | Revise the prepublication suite to include witnesses and verify fixture hashes/paths; revision1 did not fully exercise BR-R26 and is retained by its recorded digest. | High |
| D43 | Reject raw structural-summary publication:500/500 exact synthetic profiles were unique, and rounding still left161 unique; absence of names is not anonymity. | High for this experiment; unknown real-world rates |
| D44 | Prespecify one-tenant sensitivity1, epsilon ln2 and support target k10 with NOISY threshold20; support screening is not k-anonymity, and real release remains disabled. | High mathematical mechanism; production review pending |
| D45 | Keep the NHI primary result unchanged despite an inconclusive positive control: the minority fraction imposes a population ceiling, and the reversed control exposes the difference between extensive and disproportionate reach. | High |
| D46 | Retain MLflow as a vulnerability-supported hypothetical scenario, not a named incident; add the primary-source-supported CircleCI session-theft case as the fourth actual incident dossier. | High |
| D47 | Treat historical top-decile positions as unidentified in all five dossiers; a minimal1/1 synthetic graph cannot establish a real credential ranking. | High |
| D48 | Preserve requested CC-BY specification and CC0 data licences; OpenSSF's default specification/data licences differ, so seek an exception or another neutral home rather than silently relicense. | High; legal/admission decision pending |
| D49 | Report EuroS&P2027/CCS2027 paper deadlines as not published in the retrieved official pages; conference dates are not submission deadlines. Use a relative workback plan. | High for reviewed pages as of2026-09-09 |
| D50 | Propose five steering seats with one vendor/affiliate maximum, founder employer recusal, independent second connector review and25% sponsor cap; unfilled seats and absent neutral host remain explicit. | High design intent; community ratification pending |
| D51 | Make a local Git commit because the user explicitly requested a committed conformance report; use the already configured identity and do not create a remote or publish. | High |
