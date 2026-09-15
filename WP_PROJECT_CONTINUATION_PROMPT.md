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

Status after the first complete repository-analysis vertical slice:

- The upstream repository has been pulled into the workspace.
- The latest full Python suite passes `212 passed, 1 skipped`; the skipped test requires Windows symlink creation privileges and the link-like non-read path is separately covered without that privilege.
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

These are working decisions for the refocus. If implementation evidence contradicts them, document the reason and superseding decision.

### 23. Known Problems

- The older `HANDOVER.md` and `DIRECTION.md` describe a standards-only direction that conflicts with the user's current product-refocus exploration. Preserve those documents as history; do not silently erase them.
- Repository graph v0.2 currently supports one narrow GitHub Actions/AWS CloudFormation profile; it is not a general source graph.
- Existing connectors are bounded offline profiles, not complete live-provider evaluators.
- Repository-only evidence cannot establish complete deployed cloud permissions.
- JSON is currently the only final repository-analysis presentation; a concise terminal/Markdown report and visual path are still missing.
- Local acquisition exists, but public GitHub URL acquisition, Git revision metadata and private repository authentication are intentionally deferred.
- The current acquisition profile inventories present filesystem content rather than honoring `.gitignore`.
- Product naming conflicts conceptually with the unrelated Blast-RADIUS vulnerability site.
- A clear ownership/fork/upstream contribution strategy has not been chosen.

### 24. Exact Next Action

Specify the next productivity slice: safe public GitHub URL acquisition that remains local-first and non-executing. Define strict GitHub URL/ref parsing, bounded archive download and extraction, redirect/host policy, archive integrity/revision metadata, temporary-directory cleanup, rate-limit/error behavior, SSRF and zip-slip/zip-bomb defenses, and an end-to-end `analyze-github` command. Keep private-repository tokens and server-side uploads out of this first URL profile. After that, add a concise Markdown/terminal report over the existing deterministic finding contract.

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
