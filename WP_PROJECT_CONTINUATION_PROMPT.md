# Blast Radius Project Continuation Prompt

> Canonical continuity file for the product-refocus work started on 2026-09-15.
> Use this file to recover context after a model/context limit, a new chat, or a handoff.
> This file records intent and verified repository facts. It does not turn proposed features into implemented features.

## How to Use This File

When starting a new Codex or ChatGPT session, attach this repository and say:

> Read `WP_PROJECT_CONTINUATION_PROMPT.md` completely, then inspect the current Git state and the files it identifies. Continue from the first unfinished priority. Do not restart the product discussion from zero, do not assume proposed features already exist, and update this continuity file before ending the session.

If only a single prompt can be pasted, paste everything from **BEGIN CONTINUATION PROMPT** through **END CONTINUATION PROMPT**.

Before relying on any status in this document, the new session must run read-only checks equivalent to:

```powershell
git status --short --branch
git log -1 --format="%H%n%ad%n%s" --date=iso-strict
git remote -v
rg --files
pytest -q
```

The test command may be deferred only if dependencies are unavailable; record that explicitly. Repository state and test output override stale statements in this document.

---

## BEGIN CONTINUATION PROMPT

You are continuing a serious refocus of the **Blast Radius** repository located at:

```text
C:\Users\aksha\OneDrive\文档\ChatGPT\BLAST_RAD
```

Work as a candid senior product engineer, security architect, and technical research collaborator. Preserve verified work, challenge weak assumptions, and optimize for a coherent useful product rather than a large feature count. Do not flatter the project or disguise limitations. Never claim a feature, security property, provider behavior, or test result that has not been implemented and verified.

### 1. User's Objective

The user wants to turn this repository into a strong, credible project that can be demonstrated publicly and that benefits real users. The current implementation contains substantial technical work, but its input and user journey are confusing. The user has identified this as the major issue hindering the project.

The active working direction is to investigate and likely build a product where a **GitHub repository is a primary input**. The intended user-facing question is:

> If this repository, CI/CD workflow, deployment identity, or referenced credential were compromised, what sensitive infrastructure could an attacker reach, through which evidence-backed path, and which smallest change would break that path?

This is a working product direction, not yet an implemented capability. Validate it with a narrow end-to-end slice before attempting a broad rewrite.

### 2. Critical Terminology

Do not confuse these three things:

1. `https://github.com/codezxsWIN/radius` is the upstream source repository currently checked out in the workspace.
2. A GitHub repository supplied by a future end user would be an input to a new repository-analysis feature.
3. `https://www.blastradius.fail/` documents **Blast-RADIUS**, the unrelated CVE-2024-3596 RADIUS/UDP protocol attack.

The current project is about authorization reachability and compromised-credential impact. It is unrelated to the Blast-RADIUS protocol vulnerability. Public-facing naming and documentation must disambiguate them.

### 3. Verified Repository Baseline

As last verified on 2026-09-15:

- Upstream remote: `https://github.com/codezxsWIN/radius.git`
- Checked-out branch: `main`, tracking `origin/main`
- Verified commit: `8c4965d17614f224ff38fc7a609e4094aa85f4df`
- Python: 3.12.10
- Node.js: v24.18.0
- Upstream baseline test result before refocus: `179 passed in 16.48s`
- The working tree was clean before this continuity documentation was added.
- Approximate inventory at that commit: 660 tracked files, 56 Python files, 19 JavaScript files, 345 JSON files, and 87 Markdown files.

Always re-check these facts. They are a snapshot, not a promise about current state.

### 4. What the Existing Project Actually Does

The existing project is a deterministic research standard/reference implementation for measuring the authorization reach of a compromised credential.

Its current conceptual pipeline is:

```text
synthetic graph or bounded offline provider export
    -> structural and semantic validation
    -> normalized authorization graph
    -> credential-scoped reachability traversal
    -> exact metric family and deterministic witnesses
    -> JSON / SARIF / Markdown / self-contained HTML output
```

The canonical graph contains:

- Principals: human users, service principals, managed identities, workload identities, AI agents, and groups.
- Credentials: passwords, keys, certificates, tokens, passkeys, and federated trusts. Credential values are not supposed to be stored.
- Bindings: role assignments, policy attachments, group memberships, and sharing grants.
- Resources and declared actions.
- Constraints: device, approval, network, time, and PIM eligibility.
- Edges such as `authenticates_as`, `member_of`, `assigned`, `grants`, `can_assume`, `can_read_secret`, and `constrained_by`.

The engine can model direct and chained access, group inheritance, role assumption, secret-based credential acquisition, subtractive denies, constraint models, bounded escalation, deterministic evidence paths, and counterfactual binding changes.

Important files:

- `README.md`: public overview and commands.
- `ARCHITECTURE.md`: current system architecture and boundaries.
- `HANDOVER.md`: extensive historical standards/prototype handover. Preserve it as history, but do not blindly follow its older standards-only product direction.
- `DECISIONS.md`: accumulated technical decisions. Do not delete or rewrite historical decisions; supersede them explicitly when necessary.
- `DIRECTION.md`: the prior standards-only scope decision.
- `schema/blastradius-graph-v0.1.schema.json`: current internal graph wire format.
- `spec/METRIC_SPECIFICATION_v1.0-draft.md`: normative metric specification.
- `src/blastradius/engine.py`: reachability engine.
- `src/blastradius/analysis.py`: metric analysis and comparisons.
- `src/blastradius/model.py`: graph parsing and validation.
- `src/blastradius/cli.py`: existing file-oriented CLI.
- `src/blastradius/connectors/`: bounded provider normalizers.
- `tests/`: Python test suite.
- `reference-js/`: dependency-free JavaScript reference implementation.
- `conformance/`: frozen conformance fixtures and reports.
- `ui/`: static offline visual instrument and generated data.

### 5. Current Inputs and Why They Are a Product Problem

The current CLI accepts:

- A deterministically generated fictional tenant graph (`blastradius synth`).
- A graph JSON conforming to the internal schema (`blastradius analyze`).
- Bounded offline Entra/Azure export bundles.
- Bounded offline AWS IAM export bundles.
- Bounded offline Kubernetes RBAC bundles.

The current graph schema requires `synthetic: true` and a fictional organization profile. The provider connectors intentionally reject many unsupported semantics and do not constitute broad live-cloud collection. The visual instrument primarily displays generated/prebuilt result data; it is not a polished arbitrary-user-data upload application.

The central product failure is that the internal normalized graph has effectively become the user-facing input contract. Ordinary users do not want to manually define graph nodes, edges, action universes, provenance objects, attacker models, and constraint semantics. They want to point at an environment or repository and receive evidence-backed answers.

### 6. Brutally Honest Assessment

The project is **not implementation slop**. It contains real modeling, deterministic behavior, extensive tests, conformance work, provider fixtures, and careful limitations.

It is currently weak as a product because:

- There is no obvious user, input, decision, and output loop.
- Input is research-oriented and difficult.
- Real-data support is deliberately absent or narrowly bounded.
- The static dashboard is ahead of ingestion and operational workflow.
- The standards/governance/documentation surface is larger than the demonstrated user value.
- It risks looking like a standards body or enterprise product before real-world validation exists.
- Its name can be confused with the unrelated Blast-RADIUS vulnerability.

The correct response is not to add more metrics, figures, providers, or dashboard tabs. The response is to prove one useful end-to-end product loop.

### 7. Working Product Thesis

The promising product is **repository-to-production attack-path analysis**, initially focused on GitHub repositories and CI/CD.

The differentiator is not generic repository scanning. Many tools already find leaked secrets, vulnerable dependencies, insecure workflows, or broad IAM statements independently. This project should connect evidence across layers:

```text
repository file
    -> workflow trigger and permissions
    -> secret or OIDC identity
    -> cloud role or service account
    -> transitive permission/credential path
    -> sensitive infrastructure or business impact
    -> ranked path-breaking remediation
```

The product should answer decisions such as:

- Which workflows or repositories can reach production?
- If a pull request, workflow, runner, token, or deployment identity is compromised, what becomes reachable?
- Which paths are proven by repository evidence, which are inferred, and which require external cloud data?
- Which single change breaks the most dangerous path or reduces the most reach?
- What changed in blast radius in this pull request?

### 8. Why GitHub Repository Input Is Useful but Insufficient Alone

A GitHub repository can contain useful evidence:

- `.github/workflows/*.yml` workflow triggers, permissions, environments, actions, secret references, and OIDC use.
- Terraform, CloudFormation, Bicep, Pulumi, Kubernetes YAML, Helm, Dockerfiles, and deployment scripts.
- IAM policy and trust-policy declarations.
- Cloud role ARNs, service-account annotations, secret names, deployment targets, and environment boundaries.
- Repository-local relationships between code, automation, identity, and infrastructure.

A repository usually cannot prove the complete live authorization state. A workflow may reference a cloud role without containing that role's effective deployed permissions. Resource policies, organization policies, permission boundaries, session policies, runtime configuration, drift, secret contents, and external trust relationships may exist outside the repository.

Therefore every finding must carry an evidence/coverage status such as:

- **Verified from repository**: directly supported by parsed source or IaC.
- **Derived from declared IaC**: follows from modeled configuration but may differ from deployed state.
- **Potential path**: a reference exists, but external permissions are unavailable.
- **Verified with external snapshot**: repository evidence is joined with a read-only cloud/IAM export.
- **Unsupported/unknown**: the analyzer cannot soundly evaluate the relevant semantics.

Never convert absence of evidence into a safe result. Never market repository-only analysis as a complete cloud blast-radius scan.

### 9. Recommended Product Boundary

The first credible product promise should be:

> Analyze a GitHub repository's CI/CD and infrastructure configuration to identify evidence-backed potential paths from repository or workflow compromise to sensitive infrastructure, show coverage and uncertainty, and simulate path-breaking remediations.

Do not initially promise:

- Complete analysis of any GitHub repository.
- Complete effective AWS, Azure, GCP, or Kubernetes authorization.
- Live exploitation, credential validation, or secret extraction.
- Proof that a vulnerability is exploitable.
- Automated production changes.
- Compliance certification.
- A universal risk score.

### 10. Initial User and Job to Be Done

Primary initial user: a platform/security engineer responsible for GitHub Actions and cloud deployment access.

Primary job:

> Before merging or during review, determine whether a repository or workflow change creates or expands a credible path to production, understand the evidence and uncertainty, and identify the smallest effective remediation.

Secondary users can later include developers, AppSec engineers, DevOps teams, auditors, educators, and researchers. Do not design for all of them in the first vertical slice.

### 11. First Vertical Slice

Build one compelling scenario before broad architecture work:

```text
untrusted or overly broad GitHub Actions trigger
    -> workflow receives `id-token: write` or references a deployment secret
    -> workflow assumes a declared cloud role
    -> role reaches a declared sensitive resource
    -> user sees the exact source evidence and path
    -> user removes/restricts one relationship
    -> engine recomputes before/after reach
```

Prefer an example that can be verified entirely from a small fixture repository plus explicit declared IaC. AWS OIDC is a reasonable candidate, but provider choice remains a product/implementation decision until repository evidence and testability are reviewed.

The slice is complete only when a user can:

1. Provide a local Git repository path or an intentionally supported public GitHub URL.
2. See which files and constructs were recognized.
3. See coverage gaps and unsupported constructs.
4. Select a repository/workflow compromise scenario.
5. See an evidence-backed path to a sensitive resource.
6. Inspect source-file and line references for each derived relationship.
7. Simulate one remediation.
8. See a deterministic before/after result.
9. Export or share a self-contained report without exposing secret values.

### 12. Proposed Architecture

Preserve the existing engine and introduce explicit layers:

```text
Repository Acquisition
    -> safe local checkout / supplied local path / controlled archive
    -> no execution of repository code

Repository Discovery
    -> file inventory
    -> language/config recognizers
    -> size and unsupported-file limits

Evidence Parsers
    -> GitHub Actions
    -> one initial IaC/provider profile
    -> secret references and identity references, never secret-value output

Evidence Model
    -> source path, line/region, parser, confidence, assumptions
    -> preserve raw-to-normalized traceability

Graph Builder
    -> translate supported evidence into existing Blast Radius nodes/edges
    -> attach provenance to every derived relationship
    -> reject or record unsupported semantics

Existing Analysis Engine
    -> deterministic reachability, constraints, metrics, witnesses, what-if

Finding Layer
    -> path story, impact, confidence, coverage, remediation

User Interface / CLI / PR Output
    -> import review, path explorer, before/after comparison, report
```

Do not make the existing internal graph schema the ordinary user's primary input. Retain it as a canonical internal/developer/conformance format.

### 13. Security Requirements for Repository Analysis

Repository scanning is security-sensitive. At minimum:

- Never execute repository code, build scripts, package hooks, Terraform, workflows, containers, or macros during static analysis.
- Treat all repository content as untrusted data, including filenames, documentation, prompts, comments, workflow strings, generated files, and symlinks.
- Do not follow symlinks outside the acquisition root.
- Apply file-count, file-size, archive-expansion, recursion, and parser-complexity limits.
- Reject path traversal in archives.
- Do not print, store, or transmit detected secret values. Prefer detecting references and redact any unavoidable match.
- Avoid requiring users to provide GitHub personal access tokens for public repositories.
- For private repositories, define a minimal read-only access model and clear token handling before implementation.
- Do not send repository content to external services without explicit disclosure and user choice.
- Keep initial analysis local-first when practical.
- Distinguish static declarations from deployed reality.
- Produce deterministic results for the same repository commit and analyzer profile.
- Record repository commit/ref, parser versions, coverage, assumptions, and source evidence.

### 14. Trust, Attribution, and Licensing

The upstream repository is not to be silently rebranded as wholly original work.

Before public distribution:

- Preserve applicable Apache-2.0 notices for code.
- Review `LICENSING.md` because specifications, schemas, figures, and generated/aggregate data have different stated licensing.
- Identify the exact upstream commit used.
- State which components are inherited and which are newly developed.
- Maintain a change log or architecture page describing the new ingestion and product layer.
- Do not claim independent certification merely because inherited tests pass.
- Add independent tests and review for every new parser and graph mapping.

Transparent reuse is acceptable and can strengthen credibility. Concealing provenance or exaggerating production readiness will damage trust.

### 15. Product Output Contract

Every high-value finding should include:

- **Start condition**: what is assumed compromised and why that scenario is plausible.
- **Path**: each identity, credential/reference, trust, permission, and resource transition.
- **Evidence**: repository path and source region for every repository-derived transition.
- **Impact**: concrete reachable capability, not only an opaque score.
- **Coverage**: data sources present, missing, rejected, and unsupported.
- **Confidence**: verified, derived, potential, or unknown, with reasons.
- **Constraints**: approvals, branch/environment protections, device/session controls, and other blockers that were modeled or missing.
- **Remediation**: the exact relationship or configuration to change.
- **Counterfactual**: deterministic before/after path and reach comparison.

Scores may summarize findings, but a score must never replace the path, evidence, assumptions, and coverage.

### 16. Productivity Test

The project is valuable only if it reduces the time required to make a security decision. Evaluate the vertical slice against these questions:

- Can a new user provide a repository without learning the graph schema?
- Can they understand the most important path in under five minutes?
- Can they verify why each edge exists?
- Can they distinguish proven facts from assumptions?
- Can they identify one actionable change?
- Can they see whether that change actually breaks the path?
- Does the tool find a composed risk that a normal single-file linter would not communicate clearly?

If the answer is no, do not compensate by adding more dashboards or metrics.

### 17. Priority Order

Proceed in this order unless new evidence justifies a documented change:

1. Re-read this file and verify repository/test state.
2. Write a concise product specification for the one vertical slice, including non-goals and acceptance tests.
3. Audit the existing engine's callable boundary and decide the smallest adapter interface that preserves conformance behavior.
4. Define an evidence model that retains file/line provenance and uncertainty.
5. Design one deliberately bounded GitHub Actions parser profile.
6. Design one deliberately bounded IaC/provider profile needed by the fixture scenario.
7. Create malicious and benign fixture repositories.
8. Build repository evidence -> normalized graph conversion.
9. Run the existing engine without weakening its validation or deterministic guarantees.
10. Generate one evidence-backed finding and one working remediation counterfactual.
11. Expose the slice through a simple CLI first if that accelerates validation; then build the product UI.
12. Perform security, parser, license, and usability review before broadening inputs.

### 18. Explicit Non-Priorities

Until the vertical slice is proven, deprioritize:

- More synthetic population research.
- More aggregate metrics.
- More static figures.
- More dashboard tabs.
- Multiple new cloud providers.
- Live tenant write access.
- Automated remediation changes.
- Multi-tenant SaaS, billing, SSO, SIEM, or ticketing integrations.
- AI-generated explanations that are not traceable to deterministic evidence.
- A broad claim that this replaces secret scanners, SAST, CSPM, CIEM, or cloud-native IAM tooling.

### 19. Decisions That Remain Open

Do not silently decide these without examining constraints and recording the rationale:

- Whether to retain the public name “Blast Radius” or adopt a less ambiguous product name.
- Whether the first provider-specific slice should be AWS OIDC, Azure workload federation, or Kubernetes/GitHub Actions.
- Whether public GitHub URL acquisition is in the first slice or whether local paths/fixtures come first.
- Whether the project remains a fork, becomes a clearly attributed derivative, or contributes changes upstream.
- Whether the existing `synthetic: true` schema is extended, versioned, or separated from a new evidence-ingestion schema.
- Whether source evidence is embedded in the graph, stored in a companion manifest, or represented through a versioned evidence schema.
- What exact threat scenarios are supported and how attacker preconditions are represented.
- What “sensitive resource” means and whether it is user-declared, inferred from IaC, or both.
- How private repository data is stored, retained, and deleted.

### 20. Working Rules for the Continuing Agent

- Begin each new session by reading `git status`, recent commits, this file, and the relevant source/tests.
- Preserve user changes and unrelated dirty-worktree files.
- Use the existing tests as a safety net; add tests before or alongside behavioral changes.
- Do not weaken validation to make a demo pass.
- Prefer explicit unsupported results over unsound inference.
- Do not execute analyzed repositories.
- Keep source evidence attached through normalization and analysis.
- Avoid broad rewrites until the narrow slice proves the architecture.
- Keep product claims narrower than verified capability.
- Record significant architectural decisions in the repository's existing `DECISIONS.md` convention; supersede old decisions instead of deleting history.
- Update relevant public documentation when behavior changes.
- At the end of every material work session, update this file's **Current Execution State**, **Decisions Made**, **Known Problems**, and **Exact Next Action** sections.

### 21. Current Execution State

#### Expanded evidence iteration verified on 2026-09-16

- Newest user request: **"imrpove it as much as possible"**, after testing a real external repository. Implemented WP_029-WP_032/D79-D81 to address observed evidence gaps, not another cosmetic reskin, provider expansion or secret-value collection.
- GitHub Actions now supports finite scalar matrices with Cartesian/include/exclude behavior, separate per-variant job IDs, direct matrix and literal workflow/job/step env substitutions, exact scalar handling and supporting source marks. Bounds: 64 variants per matrix, 256 expanded jobs and 512 identity requests per workflow. Dynamic/nested/oversized matrices stay excluded from proven role paths. Unknown child env values do not inherit resolved parents.
- Separate `facts.workflow_identities` / result `identity_requests` preserves unresolved role references, local-action inputs, permission state, matrix values/status, source marks and blockers. Only previously admissible resolved known-action requests enter the graph. Result `identity_summary` and `evidence_gaps` describe what is missing; they are not vulnerabilities. Sensitive-named matrix fields are redacted, not generally anonymized.
- Conventional CloudFormation literal JSON/YAML names/suffixes and cloudformation/cfn directories are recognized. Known intrinsic tags remain opaque and diagnosed; they cannot become literal identities or grants. Independently literal evidence in the same file remains usable. Arbitrary tags, aliases, duplicates, merges and parser limits stay enforced.
- New Identities view appears automatically for no-path results with identity evidence. It groups source declarations, paginates, filters by job/role/reference/state, supports three-tab keyboard navigation and lists evidence needed. Matrix provenance appears in path evidence. Markdown retains identity observations; SARIF puts summaries/gaps in run metadata and does not invent findings.
- Final `tools/verify.py`: **301 passed, 1 platform skip, 69.98s**, 3229/3611 covered lines (**89.421213%**). **15 browser accessibility audits, zero violations**, including 46 identity variants grouped into 23 paginated declarations, desktop/1280/390/320px, filters/keyboard and prior shared-path/error/export/offline tests. No page errors/offline HTTP.
- Same external commit `aws-actions/configure-aws-credentials@ec8e608231b771e3614fc6ea4edadab8703331a5`: 20 jobs, **33 expanded job variants**, **36 identity request variants / 17 declarations**, zero unexpanded matrices. All role values remain unknown and IAM declarations are absent: no complete path claimed. Diagnostic sites now show 17 dynamic roles, 12 local actions, 4 unsupported credential/session configurations. More evidence is not more vulnerabilities.
- Final current external result `results/aws-actions-expanded-evidence-20260916.{json,md,html}`, analysis hash `de5f8b91f9cb1456cd9867a6dd30f1e39081992b84e6a2e02d8737ed8dbef419`. Prior results below remain historical measurements. No source execution, AWS operations, credentials, commit/push or hosted CI was performed.
- Current wheel in `dist/repository-expanded-evidence-20260916/` has SHA-256 `fc75c19f6aa7cc0eb62a1f412dad1212615678572dcba1883b580af0840c4a42`. Clean installed-package checks from temporary cwd under `-I` passed matrix/env source resolution, intrinsic opacity, packaged shared example, external identity HTML and SARIF 2.1.0 validation. Playwright verified the external HTML offline with zero HTTP requests, then the same pinned repository through the refreshed app (36 request variants / 17 declarations / 33 job variants / 0 paths). The live app remains on http://127.0.0.1:8765/ with the real repository's Identities view open.

#### Real-repository test requested on 2026-09-16

- Latest user request: **"can u use a repo and test with it"**. Tested public inputs, not another feature iteration. No implementation code changed and no target code/AWS operation executed.
- Self-repo `codezxsWIN/radius` at `8a4f644877dc85b80e94a677e2350975ac416512`: 693 inventoried, 2 selected/parsed, 691 outside profile, 0 findings/diagnostics, one oversized archive file skipped. Selected IaC was a test fixture; this does not validate a production access path.
- External `aws-actions/configure-aws-credentials` at `ec8e608231b771e3614fc6ea4edadab8703331a5`: 57 inventoried, 13 workflows parsed, 44 files outside profile, 0 matching CloudFormation files, 12 coverage warnings (5 dynamic role references, 7 matrix exclusions), 0 complete paths proven. Pinned source inspection corroborated secret-based role references and matrices; secret values remain unknown.
- Both JSON/Markdown reports are in results/ using `radius-live-repository-test-20260916` and `aws-actions-live-repository-test-20260916` prefixes. The live app also analyzed the exact external commit and matched the counts. Browser is left on the external repository's Coverage view, not the example. This is real-input ingestion/coverage evidence, not a clean security verdict.

#### Investigation iteration verified on 2026-09-16

- Newest user direction: **"build ahead we are still left.. its still slop"**. The first screen was not accepted as a finished experience; this iteration improves evidence and decisions without restarting provider work or the old visual roadmap. WP_025-WP_028 and D77-D78 record the increment.
- New UI: searchable finding queue with job/role/resource and impact-state filters, keyboard/previous/next navigation, compact source switching/reanalysis, exact normalized OIDC/trust/permission inspector, staged multi-control change set with per-job impact, and file-level coverage/diagnostics/skips. Mobile path labels are vertical/readable. Prior user-edited research UI is untouched.
- `repository/scenarios.py` recomputes a copied retained graph for up to 128 selected known trust statements. The latest baseline graph/evidence stays server-side and is cleared on new analysis/reset. Public source archives are deleted before later comparisons. API baseline hashes reject stale operations; comparison and change-request exports are deterministic and no source/policy change is applied.
- The shared example is `acme/release-platform`: 5 findings / 3 jobs / 3 secrets / 3 controls. One production trust removal yields 5 -> 5 (alternate route); both yield 5 -> 1; all controls yield 5 -> 0. It is explicitly example data. The original single-path example remains available. Both fixtures are bundled with the package through tools/build_repository_assets.py.
- Inspector tests found/fixed a real multiple-request provenance defect: role fields now use the actual `can_assume` correlation's request. Baseline Markdown includes matched predicates and file coverage. New change requests export Markdown/JSON with selected controls, all-job deltas, baseline/comparison hashes and simulation-only statements.
- Full `tools/verify.py`: **280 passed, 1 platform skip in 55.57s**; 2983/3361 lines covered (**88.753347%**). Optional-context wrapper compatibility and a Windows inconsistent-body header-test race were resolved, not waived. Pylance scenarios diagnostics empty.
- Browser: **12 real-Chromium accessibility audits, zero violations** at 1440/1280/390/320px and offline. Exact evidence, queue/status/file filters, rapid toggles, failed comparison uncertainty, four baseline formats and two plan formats all pass. Generated reports/screenshots are in results/repository-review-browser/. No page errors/offline HTTP requests.
- Current wheel in `dist/repository-investigation-20260916/` passed isolated installed-package checks for the shared example, alternate/combined comparison and report assets. SHA-256 `1a46d48128c483945e9b01643fd1681df463316b2ec0e047543159eb0cd9dd50`. Shared example analysis hash `1df8e5e9a188ab11e8177a7aabf164785cf039c2fa4623fa65f24b7d9c5daf7e`. Regenerated SARIF schema passes. The updated app is running at http://127.0.0.1:8765/ with the shared baseline loaded; live Playwright verified 5 -> 5 -> 1 -> 5 staging and clear.
- HTML snapshots keep saved single-statement comparisons only, not a browser graph engine or arbitrary multi-control planner. Live planning needs the guarded local server. No new source execution, secret value read, AWS call, commit, push or hosted CI run was performed. Earlier hashes/test counts below are historical.

#### Repository review delivery verified on 2026-09-16

- The newest user instruction is **"JUST CONTINUE BUILDING AND GIVE ME THE FINAL PRODUCT"**. This authorized the next bounded delivery beyond recovery. WP_SPEC_repository-review.md and D73-D76 record the scope; do not reopen the old product-vs-standard discussion or restart the 100-goal instrument roadmap.
- The delivered app launches with `start-review.cmd` or the installed `blastradius review` command. It binds only `127.0.0.1`, accepts local checkout/slug or public GitHub input, renders selectable evidence paths, shows a before/after trust-removal simulation, coverage/no-proof/error states and exports HTML/Markdown/JSON/SARIF. HTML reopens offline with bundled licensed fonts/icons and no service requirement. The existing visual instrument was not rewritten.
- Added `render-repo` for content-hash-checked saved-result export and `--fail-on-findings` as an explicit opt-in exit policy. SARIF 2.1.0 uses review results, source regions, related locations, code flows, fingerprints and explicit uncertainty. A zero-finding result is never labeled safe. Result hashes are integrity checks, not signatures.
- Seven reproduced regressions identified cross-job privilege pooling and ignored restrictions. Fixed job-level graph principals, conservative unresolved-deny/boundary/managed-policy/trust-condition handling, account/role-path matching, ambiguous declarations, environments/matrices/alternate credential options, and trust-statement-wide counterfactual removal. Added regression coverage including multiple uses of one trust statement. The shared engine and frozen v0.1 schema remain unchanged.
- Implemented `.github/workflows/repository-review.yml` and `tools/repository_ci.py`: immutable trusted-base analyzer installation, untrusted target checkout only as data, Python isolation outside target cwd, pinned actions/read-only permissions, four artifacts and revision/hash context, separate opt-in manual SARIF upload. Hostile target `sitecustomize.py`/shadow-module regressions prove no target imports in this workflow. Hosted workflow execution remains unverified and unperformed.
- Full required verifier: **273 passed, 1 platform skip in 59.86s**, 2854/3224 Python lines covered (**88.523573%**). Skip is the same Windows file-symlink privilege limitation. Six real-Chromium desktop/mobile/offline accessibility audits returned zero violations; evidence selection, 1 -> 0 simulation, no-proof/errors, downloads and offline reopening passed without page errors or external local-analysis browser requests. SARIF passed the 2.1.0 schema.
- The wheel builds offline and installs in a clean venv with only declared runtime dependencies. From OS temporary cwd under `-I`, the installed package loads bundled fixtures/fonts, produces one path and a 1 -> 0 counterfactual, renders offline HTML and constructs the loopback service. `start-review.cmd --help` passed. Final wheel lives under `dist/repository-review-20260916/`; reports, screenshots and browser checks are under `results/repository-review-browser/`.
- Built-in example is explicitly marked `is_example: true`, current analysis hash `65a2f17d5565e2b6fdfe911262989f3f5ee70fa1d546544b2ad2866cf363f3d9`. This supersedes the recovery fixture hash only for the newly hardened/example-labeled artifact.
- A live token-free public GitHub smoke resolved `codezxsWIN/radius` at `8a4f644877dc85b80e94a677e2350975ac416512`, parsed two profile files and returned no complete path (0 findings, 0 diagnostics). No AWS credentials, secret value access, cloud change, target code execution, commit or push occurred.
- README, SECURITY, HANDOVER, TEST_REPORT, DECISIONS and WP_020-WP_024 task records describe the current delivery and limitations. Earlier user/UI edits remain dirty and preserved; do not bulk-stage or reset them. A current loopback app is intentionally left running for the user.

#### Local recovery verified on 2026-09-16

- Active workspace: `C:\Users\amitdamle\Downloads\radius\blast-radius-v0.1`; the path earlier in this handoff belongs to the other development machine.
- Branch `main` tracks `origin/main`; latest inspected commit is `8a4f644` (agent discussion notes). The remote is `https://github.com/codezxsWIN/radius.git`.
- All seven `WP_` direction/specification documents, `tasks/plan.md`, `tasks/todo.md`, and `tasks/basic-ai-agent-discussion.md` were read. The committed README, decision additions D67-D71, repository-report checkpoint and handover notice were also inspected separately from their locally modified copies.
- Initial local edits removed the four repository commands, graph-v0.2 selection, PyYAML declaration and six repository CLI tests; the first test attempt stopped with six missing-yaml collection errors. The user explicitly approved reconciling that boundary while preserving other changes.
- `inspect-repo`, `inspect-repo-evidence`, `analyze-repo`, `analyze-github`, strict v0.1/v0.2 schema selection and the existing repository CLI tests are restored. `PyYAML==6.0.3` is declared and installed from the offline cache into the project .venv. The environment helper selected the older parent venv, so installation used uv with the explicit nested interpreter instead; workspace settings were not changed.
- Focused checks passed (27 validation/conformance tests; 21 CLI/graph/finding/report tests). The current full suite passes **234 tests with 1 platform skip**, in 41.18 seconds with skip reporting and 33.54 seconds on a repeated run. The skip requires Windows file-symlink creation privileges; no elevation was attempted. Prior collection errors are resolved, not waived.
- The installed CLI generated `results/repository-recovery-20260916.md` and `.json` from the existing aws-oidc-path fixture with slug `acme/payments`: one four-edge declared secret-read path, exact workflow/IaC source locations, and non-applied trust removal reducing absolute reach from 1 to 0. Analysis hash: `8097766d2d4bde78c7377bf9bba660c530f6df2739ef38618e1b120c4d88b530`. This fixture run is not live AWS verification.
- README/HANDOVER/TEST_REPORT now lead with current repository-first behavior and verification while retaining the older standards history. D67-D71 are restored in DECISIONS.md, with D72 recording the authorized recovery.
- Unrelated local source/UI edits were preserved. No target code, live GitHub/AWS access, new feature, package release, commit or push was performed. The worktree intentionally remains dirty with existing user edits and these continuity updates.
- The newest user request is to follow the repository-first approach. The old 100-goal visual expansion is not the active next task. The new agent-discussion note is general background, not a specification authorizing an LLM component.

#### Historical checkpoint on 2026-09-15

Status reported after the first complete repository-analysis vertical slice on the other development machine; the local verification above supersedes these statements as claims about the current working tree:

- The upstream repository has been pulled into the workspace.
- The latest full Python suite passes `234 passed, 1 skipped`; the skipped test requires Windows symlink creation privileges and the link-like non-read path is separately covered without that privilege.
- The repository has been studied at a high level.
- The user and assistant identified the confusing/synthetic input model as the primary product weakness.
- GitHub-repository input is now the implemented primary product direction, beginning with a local checkout plus explicit `owner/repository` slug.
- `WP_CAPABILITY_MAP.md` defines the approved module boundaries, dependency direction, first AWS OIDC vertical slice and explicit deferrals.
- `WP_SPEC_repo-acquisition.md` is approved and implemented.
- `blastradius inspect-repo <local-directory>` now emits a deterministic `safe-local-v0.1` manifest with normalized paths, raw-byte hashes, explicit exclusions/skips and fixed fail-closed limits.
- Repository acquisition does not execute target code, invoke a subprocess or use the network; links/reparse points are not followed or read.
- CLI output inside the analyzed repository is rejected so the manifest cannot change its own next snapshot.
- The frozen synthetic graph v0.1 schema, analysis semantics and conformance behavior remain backward-compatible; additive graph v0.2 truthfully represents non-synthetic repository declarations.
- The repository-acquisition implementation checkpoint is commit `daa4ede` on `WP_repository-input` and is pushed to `origin/WP_repository-input`.
- `WP_SPEC_repository-evidence.md` is approved and implemented locally: GitHub Actions OIDC requests and literal CloudFormation IAM trust/finite Secrets Manager grants produce deterministic source-backed facts.
- Evidence files are reverified against acquisition hashes before parsing; duplicate mappings, aliases, merge keys, custom tags and parser resource limits fail closed.
- `blastradius inspect-repo-evidence` provides the intermediate evidence flow and always labels deployed AWS state unverified.
- `WP_SPEC_evidence-graph.md` is approved and implemented: only exact workflow/OIDC/trust/finite-secret evidence maps into graph edges.
- `blastradius analyze-repo <local-directory> --repository-slug owner/repository` now performs the complete safe acquisition, evidence, graph, path and remediation-simulation flow.
- Findings embed source locations, state the assumed-compromise starting condition, name concrete Secrets Manager impact and label deployed AWS state unverified.
- Broad or incomplete evidence emits an explicit no-proof conclusion rather than a safety verdict.
- The new behavior is covered by graph, finding and CLI tests, including deterministic output, source immutability, protected output and duplicate secret declarations.
- `WP_SPEC_public-github-input.md` is implemented: `blastradius analyze-github https://github.com/owner/repository [--ref REF]` resolves an immutable public commit and analyzes its bounded source ZIP locally without Git, tokens or source upload.
- URL, network and archive boundaries reject confused authorities, unapproved redirects, traversal, links, special entries, path collisions, excessive expansion and unsupported compression. Temporary source is deleted after analysis and oversized files are reported as skipped.
- A live public smoke run against `codezxsWIN/radius` commit `8c4965d17614f224ff38fc7a609e4094aa85f4df` completed successfully and returned the explicit no-proof conclusion for the supported profile.
- `WP_SPEC_repository-report.md` is implemented: both repository commands accept `--format md` and render an inert evidence-first report with assumptions, impact, exact source locations, remediation delta, diagnostics, skipped coverage and deployment caveats. JSON remains the default machine format.

### 22. Decisions Made During the Refocus

- Preserve and evaluate the existing deterministic analysis engine rather than discarding it reflexively.
- Treat the normalized graph as an internal/developer contract, not the default end-user input.
- Use GitHub repository analysis only if it leads to cross-layer attack paths; do not build a generic secret/SAST scanner.
- Make evidence, coverage, uncertainty, and remediation counterfactuals central product outputs.
- Validate one narrow CI/CD-to-sensitive-resource slice before expanding providers or UI surface.
- Be transparent about upstream attribution, licensing, and inherited versus new work.
- Make repository acquisition a dependency-free, local-first, non-executing boundary with explicit skipped coverage and deterministic hashes.
- Require saved manifests to live outside the analyzed repository to preserve repeatability.
- Keep synthetic graph v0.1 frozen and introduce repository-declared graph v0.2 rather than mislabeling real source evidence as fictional.
- Make the useful result a source-backed path plus remediation counterfactual; do not expose an unexplained aggregate risk score as the repository product.
- Keep public GitHub acquisition token-free and pinned to an immutable commit; route private repositories through the no-network local-checkout command.
- Keep JSON as the deterministic integration contract and use a separate neutralized Markdown view for human review rather than mixing presentation fields into findings.
- On 2026-09-16, the user approved reconciliation of the locally disabled repository-analysis boundary. Restore only that boundary and its tests, install the already approved pinned dependency in the correct venv, preserve unrelated changes and demonstrate the existing narrow workflow before new CI or UI work. This recovery is now verified; no historical test count is substituted for current execution.
- The subsequent instruction to deliver a final usable workflow authorized WP_020-WP_024. Keep the local app and SARIF/CI adapters separate from the engine, reuse licensed assets, isolate each job's access, and fail conservatively on unsupported restrictions. The resulting local delivery is verified; universal provider/security completeness is not implied.
- A local workstation service has exact host/origin/token guards, bounded request bodies, one analysis at a time and no persisted result or path unless exported. It is not an authenticated multiuser or hostile-local-process boundary. CI uses trusted-base workflow/analyzer code and isolated target data; no write scope is granted to the PR analysis job.
- After the user rejected the first UI as unfinished, prioritize exact evidence, selectable cross-job counterfactuals and explicit coverage rather than another visual skin or extra providers. Retain graph/facts server-side, remove only copied trust edges and preserve alternate paths. Pending/failed recomputation is unknown, not a successful baseline result. D77-D78 describe this iteration.
- For the subsequent real-repository test, report ingestion success separately from assessment completeness: dynamic secret references and absent supported IaC prevent a complete path claim. Do not treat parser coverage warnings as vulnerabilities or zero findings as safety. Do not invent role values to force a positive result.
- The next explicit improvement request authorizes finite-matrix/static-context coverage, unresolved identity evidence and conventional literal CloudFormation YAML. Keep exact source provenance, bounds and graph isolation; opaque expressions do not become literals. A no-path identity/evidence-needed view is useful without guessing secret values or broadening permissions.

These are working decisions for the refocus. If implementation evidence contradicts them, document the reason and superseding decision.

### 23. Known Problems

- **Resolved local blocker (2026-09-16):** the approved command/schema/dependency recovery is verified. Unrelated dirty-worktree files remain; do not use a broad reset or assume those edits can be discarded.
- Older sections of `HANDOVER.md`, the historical README material and `DIRECTION.md` describe standards-only scope. Current repository-first notices explicitly supersede that direction; preserve the history instead of restarting the old roadmap.
- Repository graph v0.2 currently supports one narrow GitHub Actions/AWS CloudFormation profile; it is not a general source graph.
- Existing connectors are bounded offline profiles, not complete live-provider evaluators.
- Repository-only evidence cannot establish complete deployed cloud permissions.
- The focused review app and HTML/Markdown/JSON/SARIF outputs are implemented and locally verified. CI artifact workflow and optional manual SARIF upload are implemented but not yet run on GitHub; publication/activation needs the user's separate commit/push authorization and a trusted baseline containing the additions.
- The app is local single-user software, not hardened public hosting; unsupported policies and runtime conditions remain gaps, not implied allows. Browser automated accessibility checks do not replace manual assistive-technology/Firefox/Safari testing. Private remote authentication and OS-enforced resource isolation remain outside this delivery.
- The investigation increment addresses the reported workflow deficiencies but does not establish broader product acceptance. Offline HTML deliberately lacks arbitrary multi-control recomputation; change requests are review documents, not validated executable CloudFormation patches. Controls expose modeled all-job impact, not deployed availability or permission consequences. Large-review usability/performance and source-profile breadth are not proven by the small shared fixture.
- The earlier external 7-matrix exclusion is resolved for this input's finite matrices: 33 job variants and 36 identity observations now appear. The deeper gap remains: 17 role-reference sites cannot resolve secret-backed ARNs, local actions have unverified semantics and the repository contains no matching supported IAM declarations. No complete cloud-path assessment is claimed.
- Dynamic/generated matrices, object axes, arbitrary GitHub expressions, runtime env changes, environment subjects and template intrinsic evaluation remain unsupported. Sensitive-named matrix masking is not a universal secret detector. Identity observations being repository-verified means their syntax was observed, not that authentication or deployed access is verified.
- Public GitHub URL acquisition exists; private repository authentication, GitHub Enterprise and server-side analysis are intentionally deferred. Private repositories can be analyzed from a local checkout without network access.
- The current acquisition profile inventories present filesystem content rather than honoring `.gitignore`.
- Product naming conflicts conceptually with the unrelated Blast-RADIUS vulnerability site.
- A clear ownership/fork/upstream contribution strategy has not been chosen.

### 24. Exact Next Action

Hand over the improved evidence workflow with the actual external repository loaded in Identities, showing what was recovered and what remains missing. Demonstrate 33 expanded job variants / 36 unresolved request variants and the specific evidence-needed list, not a fabricated positive path. Further end-to-end cloud-path validation requires an authorized repository with matching resolvable role/trust/permission source or a separately scoped evidence extension. Publishing/hosted CI still requires commit/push authorization; do not silently add a provider, hosted service or LLM.

### 25. End-of-Session Continuity Protocol

Before ending a substantial session:

1. Run `git status --short --branch` and the relevant tests.
2. Update the verified commit/test snapshot if it changed.
3. Update **Current Execution State** with only completed, verified work.
4. Append or revise **Decisions Made During the Refocus** with rationale.
5. Update **Known Problems** rather than hiding unresolved gaps.
6. Replace **Exact Next Action** with one concrete first action for the next session.
7. Add links to any new specification, ADR/decision, test, fixture, or implementation file.
8. Never record secrets, access tokens, private repository contents, or sensitive customer data in this file.

When context is short, prioritize updating this file over producing a lengthy chat summary. This repository file is the durable source of continuation context.

## END CONTINUATION PROMPT

---

## Maintainer Notes

This document intentionally combines product context, verified baseline, constraints, and a copy-paste continuation prompt. Once the product specification and implementation mature, split stable decisions into `DECISIONS.md` and stable public behavior into `README.md`/architecture documentation. Keep this file focused on current state, unresolved problems, and the next executable action.
