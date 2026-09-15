# WP_ Implementation Plan: Safe Local Repository Acquisition

## Overview

Implement the approved `repo-acquisition` module from `WP_SPEC_repo-acquisition.md`. The slice adds a dependency-free, deterministic and fail-closed inventory of a local repository, then exposes it through `blastradius inspect-repo`. It does not parse repository content or change the existing authorization engine.

## Architecture Decisions

- Add `src/blastradius/repository/` as an input-boundary package; the existing graph engine must not depend on it.
- Stream file hashing and enforce limits without loading repository contents into the manifest.
- Treat links/reparse points as skipped evidence and never follow them.
- Emit canonical JSON through the existing serializer and write through the existing overwrite-safe CLI helper.
- Keep limits fixed in the `safe-local-v0.1` profile for this module.
- Use the existing `GraphError` for controlled input failures.

## Dependency Graph

```text
WP_001 deterministic happy-path acquisition
    -> WP_002 exclusions, links and safety limits
    -> WP_003 CLI integration
    -> WP_004 documentation and final verification
```

## Task List

### Phase 1: Acquisition foundation

- [x] `WP_001`: Implement deterministic regular-file inventory, raw-byte hashes, summary and snapshot hash with focused tests.
- [x] `WP_002`: Add exclusions, oversized-file diagnostics, fail-closed global limits, depth/path checks and non-followed link/reparse handling with adversarial tests.

### Checkpoint: Acquisition boundary

- [x] Focused acquisition tests pass.
- [x] Repeated acquisition produces byte-identical canonical output.
- [x] No target content, absolute root or link target appears in the manifest.

### Phase 2: Executable vertical slice

- [x] `WP_003`: Add `blastradius inspect-repo`, stdout/file output, overwrite protection, in-repository output rejection and controlled CLI failures.

### Checkpoint: User flow

- [x] A local fixture repository can be inventoried from the CLI.
- [x] The command performs no network access and executes no target code.
- [x] Existing CLI behavior remains unchanged.

### Phase 3: Handover and verification

- [x] `WP_004`: Update user documentation, decisions, task state and continuity state; run targeted and complete verification.

### Checkpoint: Complete

- [x] All success criteria in `WP_SPEC_repo-acquisition.md` are satisfied.
- [x] Full pytest suite passes: 189 passed, 1 skipped.
- [x] `git diff --check` passes.
- [x] Changes are committed and pushed to the `WP_repository-input` branch (`daa4ede`).

## Risks and Mitigations

### Path escape through links or Windows reparse points

Impact: high. Repository traversal could inspect files outside user scope.

Mitigation: never follow links; inspect each entry with non-following metadata; treat reparse points as skipped; verify relative containment; include platform-specific tests where creation is supported.

### Resource exhaustion

Impact: high. A malicious repository could contain huge files or very large trees.

Mitigation: fixed profile limits; check size before hashing; stream hashes; fail closed on global count/byte overflow; report individual oversized files.

### False appearance of complete analysis

Impact: medium. Skipped directories or files could be mistaken for analyzed content.

Mitigation: emit explicit skipped diagnostics and summary counts; downstream modules must carry coverage forward.

### Platform-dependent path behavior

Impact: medium. Windows case folding and reparse points differ from POSIX links.

Mitigation: normalize output separators; detect case-folded collisions where applicable; keep OS-sensitive tests conditional and document unsupported fixture creation.

### Regression to existing research engine

Impact: medium.

Mitigation: keep the repository module one-way and isolated; run all existing tests; do not change graph schema or engine behavior.

## Verification Commands

```powershell
pytest -q tests/test_repository_acquisition.py tests/test_cli.py
pytest -q
git diff --check
```

---

# WP_ Implementation Plan: Evidence to Action

## Overview

Implement `WP_SPEC_evidence-graph.md` as the first complete product slice: additive truthful graph v0.2, exact evidence mapping, deterministic engine path, simulated trust removal and one-command output.

## Dependency Graph

```text
WP_009 additive graph v0.2 validation
    -> WP_010 exact evidence-to-graph mapping
    -> WP_011 finding + remediation simulation
    -> WP_012 analyze-repo CLI + complete verification
```

## Tasks

- [x] `WP_009`: Add and test v0.2 schema selection while freezing v0.1.
- [x] `WP_010`: Map only exact evidence into a validated graph and preserve evidence references.
- [x] `WP_011`: Run the engine, create path findings and simulate trust-edge removal.
- [x] `WP_012`: Add `analyze-repo`, update docs/state and run the complete regression gate.

## Verification

```powershell
pytest -q tests/test_repository_graph.py tests/test_repository_findings.py tests/test_cli.py
pytest -q
git diff --check
```

---

# WP_ Implementation Plan: Public GitHub Input

## Overview

Implement `WP_SPEC_public-github-input.md` as a safe productivity layer over the local repository analyzer. Resolve an immutable public commit, enforce a fixed GitHub-only network boundary, extract a bounded ZIP without generic archive extraction, analyze locally and clean up automatically.

## Dependency Graph

```text
WP_013 strict URL + GitHub transport boundary
    -> WP_014 bounded archive validation/extraction
    -> WP_015 temporary end-to-end GitHub analysis
    -> WP_016 analyze-github CLI + checkpoint
```

## Tasks

- [x] `WP_013`: Parse only supported GitHub URLs and resolve refs to validated commit SHAs through an injectable transport.
- [x] `WP_014`: Validate and stream-extract GitHub ZIPs under cross-platform path and resource limits.
- [x] `WP_015`: Analyze the temporary checkout, attach immutable source metadata and prove cleanup/determinism.
- [x] `WP_016`: Add `analyze-github`, docs, decision record and complete regression verification.

## Verification

```powershell
pytest -q tests/test_public_github.py tests/test_cli.py
pytest -q
git diff --check
```

---

# WP_ Implementation Plan: Human Repository Report

## Overview

Implement `WP_SPEC_repository-report.md` as a deterministic presentation layer over the repository finding contract. Preserve JSON for machines and add neutralized Markdown for humans.

## Tasks

- [x] `WP_017`: Render positive and no-proof results with assumptions, impact, path and exact evidence locations.
- [x] `WP_018`: Include remediation delta, diagnostics, skipped coverage and deployed-state limitations; neutralize untrusted text.
- [x] `WP_019`: Add `--format md` to local/public commands, document the flow and pass full verification.

## Verification

```powershell
pytest -q tests/test_repository_report.py tests/test_cli.py
pytest -q
git diff --check
```

## Open Questions Resolved for This Plan

- Inventory present filesystem entries except fixed safe-profile exclusions; do not honor `.gitignore` yet.
- Permit a valid zero-file manifest.
- Skip and report individual files larger than 5 MiB.
- Do not invoke Git or emit revision metadata in this module.

---

# WP_ Implementation Plan: Repository Evidence

## Overview

Implement `WP_SPEC_repository-evidence.md`: reverify selected files against the acquisition manifest, safely parse a bounded GitHub Actions plus CloudFormation JSON profile, and emit deterministic facts, source locations, diagnostics, coverage and confidence. This phase does not create authorization graph edges yet.

## Architecture Decisions

- Add pinned `PyYAML==6.0.3` and use node composition with explicit structural validation; never construct arbitrary objects.
- Keep file reopening and hash verification in the acquisition boundary so all downstream parsers share one containment rule.
- Separate generic marked-node handling from GitHub Actions and CloudFormation extraction.
- Treat exact literals as evidence and dynamic/unsupported constructs as diagnostics.
- Carry repository slug as explicit user context; do not infer it from excluded Git metadata.

## Dependency Graph

```text
WP_005 verified snapshot reads + restricted marked nodes
    -> WP_006 GitHub Actions evidence
    -> WP_007 CloudFormation IAM evidence + correlation
    -> WP_008 evidence CLI + documentation + full verification
```

## Task List

### Phase 1: Safe parser boundary

- [x] `WP_005`: Add snapshot-file re-verification and restricted marked YAML/JSON nodes with adversarial tests.

### Phase 2: Evidence extraction

- [x] `WP_006`: Extract workflow, permission and literal OIDC role-request facts with exact locations and unsupported diagnostics.
- [x] `WP_007`: Extract literal CloudFormation role, GitHub trust and finite secret-grant facts; correlate exact role/subject matches without claiming deployment.

### Phase 3: Executable evidence flow

- [x] `WP_008`: Add an intermediate evidence command, deterministic output/hash, coverage summary, README/decision/continuity updates and full verification.

## Risks and Mitigations

### YAML ambiguity or unsafe features

Mitigation: node-only parsing, scalar-key handling independent of YAML 1.1 tags, duplicate/alias/merge/custom-tag rejection, node/depth limits and no object construction.

### Stale snapshot race

Mitigation: reopen only manifest-listed files beneath the same root and verify byte size/hash immediately before parsing; fail closed on mismatch.

### False deployed-state claim

Mitigation: confidence vocabulary is explicit; IaC remains `declared-configuration`; unmatched or broad trust is `potential`; coverage always states live AWS was not checked.

### Policy-semantic overreach

Mitigation: exact allowlist for OIDC trust and finite Secrets Manager grants; unsupported operators, conditions, intrinsic functions, denies and wildcards never become allow facts.

## Verification Commands

```powershell
pytest -q tests/test_repository_evidence.py tests/test_cli.py
pytest -q
git diff --check
```
