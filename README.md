# Blast Radius

**Find source-backed identity paths from CI/CD workflows to sensitive cloud resources.**

Blast Radius accepts a local GitHub repository checkout, safely inspects supported workflow and infrastructure declarations, and explains how an assumed-compromised automation identity could reach a sensitive resource. Its first end-to-end profile connects GitHub Actions OIDC configuration to AWS IAM roles and finite Secrets Manager grants, preserving the exact source locations behind every path step.

The repository also contains the deterministic graph engine, draft metric specification, conformance suite, synthetic research artifacts, offline connector profiles, and a self-contained visual instrument that the product direction builds on.

> [!IMPORTANT]
> Blast Radius is a research standard and reference implementation, not a production security product. It does not contact a tenant by default, does not collect secrets, and must not be treated as a compliance certification or proof of exploitability.

![Blast Radius visual instrument showing credential reach](ui/reports/screenshots/disc-desktop.png)

## Why Blast Radius?

Traditional scanners often stop at one file or one misconfiguration. Blast Radius asks a cross-layer question:

> If this repository's deployment workflow were compromised, which sensitive cloud resources do its declared identity and policy relationships make reachable—and which exact trust change would break that path?

The current repository profile follows this evidence chain:

```text
GitHub Actions workflow + id-token: write
    -> literal AWS OIDC role request
    -> exact CloudFormation trust subject and audience
    -> declared IAM role policy
    -> finite Secrets Manager ARN
```

Each result distinguishes repository syntax, declared infrastructure, and unverified deployed state. Missing or unsupported evidence is reported as “no complete path proven,” never as “safe.”

For synthetic and normalized graph inputs, the underlying engine also reports a family of exact metrics rather than a single opaque score:

The result is a family of exact metrics rather than a single opaque score:

| Metric | What it measures |
| --- | --- |
| Canonical radius | Reachable pairs divided by the fixed resource-action universe |
| Sensitivity-weighted radius | Reach weighted by the declared sensitivity of each pair |
| Action-weighted radius | Reach weighted by the relative impact of each action |
| Bounded radius | Reach attainable within an explicit escalation budget |
| Population statistics | Maximum, nearest-rank p95, threshold share, and Gini concentration |

The denominator and weights are frozen for permission-only comparisons. Duplicate paths do not increase a score, cycles terminate, and every reported path has deterministic evidence.

## Repository Status

The public conformance profile is **1.0-draft**. Synthetic graphs remain frozen at wire format **0.1**; source-backed repository graphs use the additive **0.2** profile.

- 40 frozen conformance fixtures across 3 required attacker models
- 120/120 conformance cases passing in both Python and JavaScript
- 231 integrated Python tests collected on the current repository-input branch: 230 passing and 1 platform-dependent skip
- One-command local repository analysis with deterministic source evidence and a non-mutating remediation simulation
- Dependency-free JavaScript reference implementation
- Offline Entra/Azure, AWS IAM, and Kubernetes normalization profiles with explicit limits
- Deterministic synthetic research runs and reconstruction dossiers
- Static, offline-first visual instrument with figure export and accessibility checks

These are repository test results, not independent certification. See [TEST_REPORT.md](TEST_REPORT.md) for commands, hashes, measurements, and caveats.

## Quickstart

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and Node.js for the optional JavaScript reference and UI tooling.

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[test]"

# Analyze a public repository at an immutable resolved commit.
.venv/Scripts/blastradius.exe analyze-github `
  https://github.com/owner/repository `
  --format md --out results/repository-analysis.md

# The synthetic standards/research workflow remains available.
.venv/Scripts/blastradius.exe synth `
  --principals 80 --resources 40 --seed 7 `
  --out results/tenant.json --force

.venv/Scripts/blastradius.exe analyze results/tenant.json `
  --constraint-model default `
  --out results/result.json --force

.venv/Scripts/blastradius.exe report results/result.json `
  --format html --out demo/index.html --force
```

Open `demo/index.html` directly in a browser. The report has no runtime server, CDN, or external font dependency. On macOS or Linux, replace `.venv/Scripts` with `.venv/bin` and use shell line continuations.

Generated outputs are never overwritten unless `--force` is supplied, and an input file cannot be replaced by its output.

## Analyze a GitHub Repository

For a public repository, pass its GitHub URL directly:

```powershell
.venv/Scripts/blastradius.exe analyze-github `
  https://github.com/owner/repository `
  --ref main `
  --format md `
  --out results/repository-analysis.md
```

Blast Radius resolves the ref to an immutable commit, downloads only that public source archive from GitHub, validates and extracts it under fixed limits, analyzes it locally, and deletes the temporary checkout. It does not run Git, hooks, filters, workflows, package managers, or repository code. It does not request a GitHub token or upload the repository to a Blast Radius service.

The public URL profile accepts only HTTPS `github.com/owner/repository` inputs and only follows GitHub's archive redirect to `codeload.github.com`. Archive traversal, links, special entries, path collisions, excessive expansion, and unsupported compression fail closed. Oversized individual files are skipped and reported just as they are for local acquisition.

Use `--format md` for a review-ready human report. It leads with the compromise assumption and concrete impact, then shows the ordered path, exact `path:line:column` evidence, remediation counterfactual, skipped/unsupported coverage and deployed-state limitation. JSON remains the default deterministic format for CI and integrations.

### Analyze a local or private checkout

For private code, clone it using your normal trusted workflow and point Blast Radius at the local directory. This mode performs no network request and needs no repository credential. The explicit GitHub slug is required because it is part of the OIDC subject claim being evaluated:

```powershell
.venv/Scripts/blastradius.exe analyze-repo C:\path\to\repository `
  --repository-slug owner/repository `
  --format md `
  --out C:\path\outside\repository-analysis.md
```

For every complete supported path, the result names the workflow and job whose compromise is assumed, the exact AWS role and secret action, the source file/line evidence for every hop, and a counterfactual showing whether removal of the modeled OIDC trust edge breaks reachability. It does not modify the repository or AWS. Output must be outside the analyzed repository so it cannot contaminate the next snapshot.

This is intentionally a proof-oriented first profile, not a generic repository security scanner. It currently understands exact push branches, `id-token: write`, literal `aws-actions/configure-aws-credentials` role ARNs, literal CloudFormation JSON `AWS::IAM::Role` trust, and finite `secretsmanager:GetSecretValue` resource ARNs. Dynamic expressions, YAML aliases/tags/merge keys, wildcard secret resources, unsupported conditions, and stale snapshots are rejected or surfaced as diagnostics rather than guessed.

### Inspect the intermediate evidence

The acquisition command safely inventories a local checkout without executing or parsing its contents:

```powershell
.venv/Scripts/blastradius.exe inspect-repo C:\path\to\repository `
  --out results/repository-manifest.json
```

The deterministic manifest records normalized relative paths, byte sizes and SHA-256 hashes. It excludes common metadata/dependency trees, never follows links or Windows reparse points, enforces fixed file and byte limits, and reports skipped content so coverage is visible. Save `--out` outside the analyzed repository to prevent the manifest from becoming part of its own next snapshot.

No repository code, hook, workflow, package manager, or build command is executed.

The first bounded evidence profile can connect a literal GitHub Actions OIDC role request to a literal AWS IAM role, trust policy and finite Secrets Manager grant declared in CloudFormation JSON:

```powershell
.venv/Scripts/blastradius.exe inspect-repo-evidence C:\path\to\repository `
  --repository-slug owner/repository `
  --out results/repository-evidence.json
```

The evidence output retains one-based file/line locations, deterministic fact IDs, unsupported diagnostics and confidence labels. `repository-verified` means the workflow syntax is directly present; `declared-configuration` means supported IaC declares a relationship; `potential` means matching or external state remains incomplete. The command always reports deployed AWS state as unverified and never treats absence of a supported fact as proof of safety.

These lower-level commands are useful for auditing what was read and why a complete path was or was not proven. Most users should start with `analyze-github` for public code or `analyze-repo` for an existing/private checkout.

## Run Conformance

Validate the Python implementation against the public suite:

```powershell
.venv/Scripts/blastradius.exe conformance run `
  --tool ".venv/Scripts/python.exe -B -m blastradius conformance adapter"
```

Validate the independent-language implementation:

```powershell
node reference-js/verify.mjs

.venv/Scripts/blastradius.exe conformance run `
  --tool "node reference-js/reference.mjs" `
  --out conformance/reports/javascript
```

Each case checks exact rational metrics, reachable pair sets, deterministic witnesses, and repeatability. Read [CONFORMANCE.md](CONFORMANCE.md) for the protocol and [conformance/REQUIREMENT_COVERAGE.md](conformance/REQUIREMENT_COVERAGE.md) for the boundary between automated, partial, and manual claims.

## Explore the Instrument

The current visual instrument is a static, local application:

```powershell
node tools/build_ui.mjs
```

Then open `ui/index.html`. It includes credential paths, population and distribution views, attacker-model contrast, counterfactual analysis, privacy experiments, reconstruction evidence, conformance results, and SVG/PNG/PDF figure export.

The source is split across `ui/index.template.html`, `ui/app.js`, `ui/render.js`, and `ui/styles.css`. The generated `ui/index.html` embeds its data and dependencies for offline inspection.

## CLI Workflows

```powershell
# Explain one credential's deterministic witness paths
.venv/Scripts/blastradius.exe explain results/result.json `
  --credential credential-principal-00001

# Recompute the graph after a hypothetical binding removal
.venv/Scripts/blastradius.exe whatif results/tenant.json `
  --remove-binding shared-2

# Verify a locally signed result manifest
.venv/Scripts/blastradius.exe verify-manifest results/result.json

# Normalize supported synthetic export bundles without cloud access
.venv/Scripts/blastradius.exe collect-entra-azure `
  --exports connectors/entra_azure/fixtures/rich `
  --out results/connector-tenant.json
```

Reports support JSON, SARIF, HTML, and Markdown. Local result integrity uses an external OS-random HMAC key; this is not public attestation, and the key is never included in repository artifacts.

## How It Fits Together

```mermaid
flowchart LR
  A[Synthetic graph or supported offline export] --> B[Schema and semantic validation]
  B --> C[Normalized authorization graph]
  C --> D[Reachability engine]
  M[Explicit attacker model] --> D
  U[Fixed resource-action universe] --> D
  D --> E[Exact metric family]
  D --> F[Deterministic path evidence]
  E --> G[JSON / SARIF / Markdown / HTML]
  F --> G
  E --> H[Counterfactual analysis]
```

The engine consumes effective authorization decisions; it does not attempt to reproduce every cloud provider's policy evaluator. Unsupported semantics are rejected or identified as coverage gaps rather than silently inferred.

For the formal definitions and implementation boundaries, read:

- [Metric Specification](spec/METRIC_SPECIFICATION_v1.0-draft.md)
- [Architecture](ARCHITECTURE.md)
- [Conformance Protocol](CONFORMANCE.md)
- [Decision Log](DECISIONS.md)
- [Reconstruction Method](RECONSTRUCTION_METHOD.md)

## Reproduce the Evidence

```powershell
# Full Python test, coverage, and artifact gate
.venv/Scripts/python.exe -B tools/verify.py

# Frozen historical reconstructions
.venv/Scripts/python.exe -B tools/build_reconstructions.py

# Preregistered synthetic privacy and NHI runs
.venv/Scripts/python.exe -B tools/run_research.py

# Offline Kubernetes normalization fixture
.venv/Scripts/python.exe -B tools/build_kubernetes_fixture.py
```

Research outputs use fictional tenants and investigator-designed distributions. They test methods and failure modes; they do not estimate a real-world population. See [PRIVACY_ANALYSIS.md](PRIVACY_ANALYSIS.md), [research/NHI_RESULTS.md](research/NHI_RESULTS.md), and [research/DATASET_CARD.md](research/DATASET_CARD.md).

## Safety and Scope

Blast Radius currently supports synthetic inputs and bounded offline export profiles. Before using real organizational data, the project still requires protected persistence, public-verifier signing, reviewed key custody, connector ground-truth studies, complete policy semantics, independent privacy review, and an authorized disclosure process.

The Entra/Azure live transport is library-only, disabled by default, and tested with fake responses. The AWS and Kubernetes adapters intentionally cover finite profiles rather than full provider semantics. Read each connector manifest before interpreting its output.

Never commit signing keys, `.env` files, live exports, or private result files. See [SECURITY.md](SECURITY.md) for the data boundary and reporting process.

## Project Map

| Path | Purpose |
| --- | --- |
| `spec/` | Normative draft metric specification and visual vocabulary |
| `schema/` | Versioned graph and result schemas |
| `src/blastradius/` | Python reference implementation and CLI |
| `reference-js/` | Dependency-free JavaScript reference implementation |
| `conformance/` | Frozen fixtures, manifest, requirements, and reports |
| `connectors/` | Explicitly bounded offline normalization profiles |
| `research/` | Synthetic protocols, outputs, and dataset documentation |
| `reconstructions/` | Public-incident mechanism dossiers and countermodels |
| `ui/` | Visual instrument source, generated app, and test evidence |
| `tools/` | Reproduction, audit, benchmark, and build scripts |

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md), then read [GOVERNANCE.md](GOVERNANCE.md), [NEUTRALITY.md](NEUTRALITY.md), and the [Code of Conduct](CODE_OF_CONDUCT.md). Contributions should preserve deterministic outputs, explicit uncertainty, and the distinction between validated structure and verified provider semantics.

## License

Licensing is split by artifact type:

- Code: [Apache License 2.0](LICENSE)
- Specification and schema: [Creative Commons Attribution 4.0](LICENSING.md)
- Generated or approved aggregate data: [CC0 1.0](LICENSING.md)

See [LICENSING.md](LICENSING.md) for the authoritative file-level policy.
