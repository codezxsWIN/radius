# WP_ Task List: Safe Local Repository Acquisition

## Educational Audit Acceptance

- [x] Same edited/invalid graph survives model changes; explicit reset and input hash/model state are distinct.
- [x] Same-template attached deny cannot disappear; unknown targets fail closed; action spelling is preserved.
- [x] Build parity protects exact captions, figure choices and evidence-copy behavior.
- [x] Unmodeled trust alternatives qualify zero-reach outcomes, while declared capability is not automatically a vulnerability.
- [x] One offline lesson compares 1/4 -> 0/4 -> 2/4 -> 1/4 with required and excess access shown separately.
- [x] Equivalent trust removals reuse validation; cancellation/stages/deadlines are tested.
- [x] Package includes the offline lab; fresh launcher diagnoses prerequisites without destroying environments.
- [x] Metadata-only Terraform files preserve evidence, HCL is explicitly unassessed, and real reviews stay opt-in for retention.
- [x] CI source enforces installed/offline journeys, source/artifact parity and zero browser/a11y failures.
- [ ] Observe actual newcomers, run uncached OS installs and execute hosted CI before educational-readiness claims.

## Terraform JSON Evidence: WP_033-WP_036

- [x] `WP_033`: Recognize `*.tf.json` as a bounded source while leaving HCL and Terraform execution unsupported.
- [x] `WP_034`: Extract literal IAM role, GitHub OIDC trust and finite Secrets Manager grants with exact source evidence.
- [x] `WP_035`: Reject dynamic policy/reference values, wildcard resources and unresolved role restrictions from complete paths.
- [x] `WP_036`: Carry Terraform provenance and coverage through graph, reports and the review app.
- [x] Final checkpoint: 306 tests passed with one Windows privilege skip; all 15 browser audits passed with zero violations.

## Evidence Coverage Acceptance: WP_029-WP_032

- [x] Finite matrix assignments expand deterministically with include/exclude semantics and distinct job principals; dynamic/excessive input is not executed.
- [x] Literal env/matrix resolution respects scope, keeps supporting source marks and does not infer secret or runtime values.
- [x] Unresolved role/local-action observations survive as evidence, not graph grants or SARIF findings.
- [x] Common CloudFormation YAML/JSON source names work; known intrinsic nodes stay opaque, and aliases/arbitrary tags remain rejected.
- [x] Identities view groups and filters variants, paginates 23 declarations/46 test variants, supports keyboard navigation and displays evidence-needed guidance.
- [x] All 301 Python tests pass with one platform skip; all 15 browser audits are clean; same external commit expands 33 job variants and exposes 36 unresolved identity requests.

No credentials, provider expansion, actual deployed permissions or hosted publishing is included. Remaining references and absent IAM declarations stay explicitly unresolved.

## Investigation Acceptance: WP_025-WP_028

- [x] Inspector shows matched branch subjects/audience, role/provider account, action and source regions rather than generic endpoint names alone.
- [x] One job's multiple requests display the actual correlated role; regression reproduced and fixed the wrong-label case.
- [x] Arbitrary selected known trusts recompute copies of the retained model; shared uses and alternate routes are preserved correctly.
- [x] Unknown/duplicate/stale controls reject, and source archive deletion does not prevent model-only public-repository comparisons.
- [x] Finding/job/resource and reach-state filters, navigation, file coverage, staging/clearing and proposed change-request downloads work in the browser.
- [x] Failed or superseded computations cannot display fabricated impact; rapid toggling is coalesced and verified.
- [x] 280 Python tests pass with one Windows privilege skip; 12 desktop/laptop/mobile/offline accessibility audits pass.

No provider expansion, executed policy patch or hosted publication is included. Offline HTML shows its saved one-statement scenario; server-only multi-control planning is explicit.

## Repository Review Delivery: WP_020-WP_024

- [x] SARIF review findings retain source regions, witness flow, remediation numbers and no-proof diagnostics.
- [x] Saved JSON exports are integrity-checked; zero-finding exit status is completion, not safety.
- [x] Distinct workflow jobs do not pool privileges; unsupported explicit restrictions cannot silently create a complete path.
- [x] Counterfactual removal follows every modeled use of the selected trust statement, preserving alternate statements.
- [x] Local/Public GitHub input -> path evidence -> simulation -> HTML/Markdown/JSON/SARIF download is usable in the browser.
- [x] Service rejects invalid host/origin/token, oversized/duplicate requests, network paths, stale exports and concurrent analyses; no raw file-serving route exists.
- [x] CI installs the trusted base analyzer and treats target contents as data; target startup/shadow Python modules never execute in regression tests.
- [x] All 273 Python tests pass with one Windows symlink skip; six desktop/mobile/offline accessibility audits have zero violations.
- [x] SARIF schema, clean wheel/packaged example, one-click launcher and public immutable-commit acquisition were exercised.
- [x] README, security, decisions and continuity updated without rewriting historical research work.
- [ ] Hosted Actions/SARIF publication: not performed; requires a separate authorized commit/push and manual execution.

Acceptance records and exact hashes are in TEST_REPORT.md. No live IAM state, full-provider support or production security clearance is implied by delivery.

## `WP_001`: Deterministic acquisition core

Description: Add the repository package and the smallest working acquisition path for regular files.

Acceptance criteria:

- [x] Manifest contains profile/source metadata, sorted file records, raw-byte SHA-256 values, summary and stable snapshot hash.
- [x] Empty directories and Unicode/space-containing relative paths are handled deterministically.
- [x] Output does not contain the supplied absolute repository root.

Verification:

- [x] `pytest -q tests/test_repository_acquisition.py -k "basic or deterministic or empty or unicode"`

Dependencies: none.

Files likely touched:

- `src/blastradius/repository/__init__.py`
- `src/blastradius/repository/acquisition.py`
- `tests/test_repository_acquisition.py`

Estimated scope: medium, three files.

## `WP_002`: Fail-closed safety profile

Description: Enforce exclusions, file/path/tree limits and non-followed links while preserving explicit coverage diagnostics.

Acceptance criteria:

- [x] Fixed excluded directories are not traversed and are reported.
- [x] Oversized files are skipped and reported; global count/byte overflow fails closed.
- [x] Links/reparse points are not followed or read, and depth/path/collision failures are controlled.

Verification:

- [x] `pytest -q tests/test_repository_acquisition.py`

Dependencies: `WP_001`.

Files likely touched:

- `src/blastradius/repository/acquisition.py`
- `tests/test_repository_acquisition.py`

Estimated scope: small, two files.

## Checkpoint: Acquisition boundary

- [x] Focused acquisition tests pass.
- [x] Repeated acquisition output is byte-identical.
- [x] Security assertions cover content, absolute-path and link-target non-disclosure.

## `WP_003`: CLI vertical slice

Description: Wire acquisition to an overwrite-safe `inspect-repo` command and verify stdout, file output and controlled errors.

Acceptance criteria:

- [x] `blastradius inspect-repo <directory>` emits canonical JSON to stdout or `--out`.
- [x] Existing-output protection and `--force` match current CLI behavior.
- [x] A manifest output path inside the analyzed repository is rejected to preserve repeatability.
- [x] Invalid input returns code 2 without echoing an absolute user path.

Verification:

- [x] `pytest -q tests/test_repository_acquisition.py tests/test_cli.py`

Dependencies: `WP_002`.

Files likely touched:

- `src/blastradius/cli.py`
- `tests/test_cli.py`

Estimated scope: small, two files.

## Checkpoint: User flow

- [x] CLI inventories a fixture repository end to end.
- [x] No network access or target execution occurs.
- [x] Existing CLI round trip still passes.

## `WP_004`: Documentation and release verification

Description: Record behavior, limits, decisions and verified state, then run the full regression gate.

Acceptance criteria:

- [x] README explains the safe local input workflow and explicitly states that parsing/analysis is not yet included.
- [x] Continuity and decision records distinguish completed acquisition from proposed downstream features.
- [x] Full tests and diff checks pass before push.

Verification:

- [x] `pytest -q` — 189 passed, 1 skipped in 21.35s.
- [x] `git diff --check`

Dependencies: `WP_003`.

Files likely touched:

- `README.md`
- `DECISIONS.md`
- `WP_PROJECT_CONTINUATION_PROMPT.md`
- `tasks/todo.md`

Estimated scope: medium, four files.

## Checkpoint: Complete

- [x] Every success criterion in `WP_SPEC_repo-acquisition.md` is met.
- [x] Branch is committed and pushed to `origin/WP_repository-input` (`daa4ede`).

---

# WP_ Task List: Repository Evidence

## `WP_005`: Verified reads and restricted marked nodes

Acceptance criteria:

- [x] Selected bytes are reread beneath the root and must match manifest size/hash.
- [x] Mapping keys, source locations, duplicate keys, aliases, merge keys, custom tags, node count and depth are handled deterministically and safely.
- [x] No YAML object construction, subprocess or network access occurs.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py -k "snapshot or yaml or location"`

Dependencies: completed `repo-acquisition` module.

## `WP_006`: GitHub Actions evidence

Acceptance criteria:

- [x] Workflow/job permissions and literal configure-credentials role requests are extracted with source locations.
- [x] Exact push branches are retained for subject matching.
- [x] Missing token permission and dynamic/unsupported constructs produce diagnostics rather than verified role requests.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py -k "workflow or oidc"`

Dependencies: `WP_005`.

## `WP_007`: CloudFormation IAM evidence

Acceptance criteria:

- [x] Literal role, exact GitHub trust and finite Secrets Manager grant facts are extracted.
- [x] Role/subject correlation is deterministic and confidence never exceeds declared configuration.
- [x] Wildcards, denies, intrinsic functions and unsupported conditions do not create allow facts.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py -k "cloudformation or trust or grant"`

Dependencies: `WP_006`.

## `WP_008`: Evidence command and checkpoint

Acceptance criteria:

- [x] Intermediate CLI emits canonical deterministic evidence and protects output paths.
- [x] Coverage says deployed AWS state is unverified.
- [x] Docs, decisions and continuity state match completed behavior.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py tests/test_cli.py` — 19 passed.
- [x] `pytest -q` — 203 passed, 1 skipped.
- [x] `git diff --check`

Dependencies: `WP_007`.

---

# WP_ Task List: Evidence to Action

## `WP_009`: Additive graph v0.2

- [x] Repository-declared non-synthetic graphs validate under v0.2.
- [x] v0.1 schema, fixtures and conformance behavior remain unchanged.
- [x] Unknown versions and source/synthetic mismatches fail closed.

Verify: `pytest -q tests/test_repository_graph.py tests/test_model.py tests/test_conformance.py`

## `WP_010`: Exact evidence-to-graph mapping

- [x] Positive evidence maps to workflow credential, role, binding, finite secret and exact edges.
- [x] Every mapped edge resolves to source evidence.
- [x] Potential/broad or incomplete evidence creates no analyzable graph path.

Verify: `pytest -q tests/test_repository_graph.py`

## `WP_011`: Finding and remediation simulation

- [x] Finding explains assumed compromise, declared impact, path and source evidence.
- [x] Removing only the modeled trust edge changes reach from one to zero.
- [x] Zero findings explicitly means no path proven, not safe.

Verify: `pytest -q tests/test_repository_findings.py`

## `WP_012`: Product command and checkpoint

- [x] `analyze-repo` works through stdout and protected file output.
- [x] README, decisions and continuity state match verified behavior.
- [x] Full suite and diff check pass; branch is pushed.

Verify: `pytest -q tests/test_repository_graph.py tests/test_repository_findings.py tests/test_cli.py`, then `pytest -q` and `git diff --check`.

---

# WP_ Task List: Public GitHub Input

## `WP_013`: Strict URL and network boundary

- [x] Accept and normalize only HTTPS `github.com/owner/repository` URLs.
- [x] Resolve a requested ref to an immutable commit using the public GitHub API.
- [x] Allow only the documented API-to-`codeload.github.com` archive redirect.
- [x] Bound response bytes, timeouts and controlled errors without reading tokens.

## `WP_014`: Safe ZIP extraction

- [x] Reject traversal, links, special entries, encryption, duplicate/colliding paths and unsafe Windows names.
- [x] Enforce compressed, per-file, total-byte, file-count, path-length and depth limits.
- [x] Stream members beneath a fixed temporary root without `extractall`.

## `WP_015`: End-to-end public repository analysis

- [x] Analyze only the pinned extracted commit and attach URL/ref/commit/archive-hash metadata.
- [x] Recompute deterministic result integrity after metadata attachment.
- [x] Prove temporary source cleanup and no repository execution.

## `WP_016`: Product command and checkpoint

- [x] Add `analyze-github` with optional `--ref` and protected JSON output.
- [x] Update README, decision log, test report and continuity state.
- [x] Run the full suite and diff check, commit with `WP_` prefix and push.

Verify: `pytest -q tests/test_public_github.py tests/test_cli.py`, then `pytest -q` and `git diff --check`.

---

# WP_ Task List: Human Repository Report

## `WP_017`: Evidence-first Markdown

- [x] Render repository identity, finding summary, assumptions, impact and ordered path.
- [x] Show primary and compound workflow/trust `path:line:column` evidence.
- [x] Reproduce the no-proof/not-safe conclusion for zero findings.

## `WP_018`: Honest limits and safe display

- [x] Show remediation applied state, before/after reach and path-broken result.
- [x] Show parser diagnostics, archive skips, coverage and deployed AWS state.
- [x] Neutralize control characters and Markdown metacharacters from untrusted source fields.

## `WP_019`: CLI and checkpoint

- [x] Add `--format md` without changing default JSON behavior.
- [x] Test deterministic/non-mutating rendering and CLI source locations.
- [x] Update docs/state, run full verification, commit with `WP_` prefix and push.

Verify: `pytest -q tests/test_repository_report.py tests/test_cli.py`, then `pytest -q` and `git diff --check`.
