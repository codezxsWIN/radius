# Blast Radius Repository Review

**Find source-backed paths from a repository's deployment workflow to declared sensitive infrastructure.**

The active workflow is repository-first: a local checkout plus its GitHub slug, or an explicitly supported public GitHub URL. The initial profile connects GitHub Actions OIDC, literal AWS CloudFormation IAM trust and finite Secrets Manager read grants. It returns the assumed-compromise condition, concrete capability, source-file locations, coverage gaps and a non-applied remediation simulation. This is not a complete deployed-cloud scan or proof of exploitability.

## Start the Review App

In this checkout, open [start-review.cmd](start-review.cmd), or run it from this project directory:

```powershell
.\start-review.cmd
```

The app opens at **http://127.0.0.1:8765/**. If that port is occupied, use `.\start-review.cmd --port 8766`; it never stops another process. Choose a local checkout plus its `owner/repository` slug, or a public GitHub URL with an optional branch/tag/commit. Two explicitly labeled bundled examples are available: the single `acme/payments` path and the `acme/release-platform` shared deployment with three jobs, three secrets and alternate trusts.

The investigation workspace has a searchable job/resource queue, condition-level evidence inspector and staged change set. Inspect exact OIDC subjects/audience, provider account, requested role and finite permission with source coordinates. Stage multiple trust-statement removals and the server recomputes all modeled jobs, finding reach and distinct secrets together, preserving alternate routes. Filtering and navigation preserve the current change set. A comparison failure shows unknown impact, never a fabricated successful reduction.

The **Identities** view remains useful when no complete path can be established. It groups request variants by their source declaration, shows the job, matrix values, literal role or unresolved reference name, token permission and evidence status, and provides filters, keyboard navigation and pagination. An **Evidence needed to continue** section identifies missing role declarations, unresolved references and unsupported authentication semantics. Local action role inputs are observations only; they never inherit the known AWS action's behavior. These are coverage gaps, not vulnerability findings. Do not supply access keys or token/secret values to fill them.

In the shared example, removing one production trust leaves **5 -> 5** reachable findings through the alternate trust; removing both changes reach to **5 -> 1**, with the publisher job retained. Removing all three controls yields zero modeled findings. The **Coverage** view lists selected files, hashes, parse status, extracted facts, diagnostics and acquisition skips, and counts inventoried files outside the parser profile.

Download the baseline as HTML, Markdown, JSON or SARIF, or export the proposed change request as Markdown/JSON with a baseline hash, selected source statements and per-job impact. Change requests are review documents, not executable policy patches. HTML baselines reopen offline with searchable evidence/coverage and their saved **single-statement** comparison; arbitrary multi-control recomputation requires the local server. The retained graph is not embedded in the HTML. Local input needs no network; public input downloads an immutable source archive from GitHub, with no access token or third-party analysis service. The latest result/model stays in process memory until cleared or the service stops, unless you explicitly download a report. Reports may contain sensitive infrastructure names, source paths and trust conditions; review them before sharing.

For a new installation, Python 3.12+ and the pinned dependencies are required:

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe .
.\start-review.cmd
```

On macOS/Linux, install with `.venv/bin/python` and launch `.venv/bin/python -I -m blastradius review`. For a headless service use `--no-open`; it always binds to loopback, never a public interface. No Node dependency installation is needed for the app. The distributable wheel includes the source example, schemas, fonts/icons and their license notices.

## CLI and CI

```powershell
.venv/Scripts/python.exe -I -m blastradius analyze-repo C:/work/payments --repository-slug acme/payments --out C:/reports/payments.json
.venv/Scripts/python.exe -I -m blastradius render-repo C:/reports/payments.json --format html --out C:/reports/payments.html
.venv/Scripts/python.exe -I -m blastradius analyze-github https://github.com/owner/repository --format sarif --out C:/reports/public.sarif
```

Both analysis commands support `--format json|md|sarif|html`; JSON remains the default. `render-repo` verifies a saved result's content hash and exports without rescanning. The hash is integrity checking, not a signature or source attestation. Source and report paths must be separate; existing outputs require explicit `--force`. `--fail-on-findings` optionally returns 1 when supported declared paths exist. Exit 0 means completed, not safe; exit 2 means an input/analysis error.

[.github/workflows/repository-review.yml](.github/workflows/repository-review.yml) reviews PR declarations with the analyzer installed from the immutable **trusted base revision**, not the PR revision. The target checkout is data only. It runs isolated Python from the runner temporary directory, uses commit-pinned actions, read-only permissions, no AWS credentials, and exports all four formats plus a revision/hash manifest. Its job summary contains source-backed findings and uncertainty. Hosted execution is not claimed: the workflow has been locally policy-tested but has not been pushed or run on GitHub.

The workflow intentionally uses `pull_request_target` to obtain trusted workflow code; do not move target code into the install step, remove `-I`, add secrets, run target hooks, or make the analysis job writable. Fork reports use the base repository slug as the prospective merge identity, not proof that a fork PR can receive those permissions. SARIF upload is a separate opt-in **manual** job requiring GitHub code-scanning availability. It is never given write permissions during PR analysis. Artifacts are retained for seven days; only reports, not repository contents, are uploaded to GitHub. Review repository access before enabling this on private sources. In another repository, install a separately audited pinned analyzer artifact; do not assume its base branch contains trusted analyzer code.

For another CI system, [tools/repository_ci.py](tools/repository_ci.py) writes all reports from one analysis. Run it under `python -I` using the installed trusted package and keep its output outside the analyzed checkout.

## Verified Scope

On 2026-09-16 the expanded-evidence iteration passed **301 Python tests, one Windows symlink-privilege skip; 89.42% line coverage**. Fifteen real-browser accessibility audits passed at 1440px, 1280px, 390px and 320px plus offline reopening, with zero violations. Checks cover exact evidence, alternate/shared trust removals, rapid toggles, failed-comparison uncertainty, identity/queue/file filters, pagination of 46 request variants, keyboard navigation, four baseline formats and two change-request formats. Source/expression execution is not part of analysis. Exact verification and historical package/schema checks are in [TEST_REPORT.md](TEST_REPORT.md).

The supported path remains exact branch-based GitHub Actions OIDC -> literal CloudFormation IAM role trust -> finite Secrets Manager read grant. Different jobs and matrix variants do not pool permissions. Finite scalar matrices support Cartesian expansion and include/exclude entries, capped at 64 variants per matrix, 256 expanded jobs and 512 identity requests per workflow. Direct `matrix.NAME` and literal workflow/job/step `env.NAME` references can resolve role/audience strings; substitutions retain exact source coordinates. Dynamic functions, generated matrices, ambiguous numeric values and runtime environment changes are not evaluated. Environment values are not collected wholesale; only supported role/audience values and relevant source locations are emitted. Sensitive-named matrix fields are redacted, not a general anonymization guarantee.

CloudFormation accepts literal JSON or YAML with `.template`, `.cfn` or `.cloudformation` suffixes, conventional `template.json|yaml|yml` / `cloudformation.json|yaml|yml` names, and JSON/YAML files under `cloudformation/` or `cfn/`. Known intrinsic tags are kept opaque and diagnosed. They cannot become literal role names, principals or grants; independently literal declarations elsewhere in the file can still be analyzed. Aliases, duplicate/merge keys and arbitrary custom tags remain rejected. See [WP_SPEC_repository-evidence.md](WP_SPEC_repository-evidence.md) for exact scope.

Simulated removal removes every modeled use of the selected trust statement while preserving alternate statements. Explicit/unresolved denies, extra trust conditions, permissions boundaries, managed policies, ambiguous roles, environment subjects, dynamic/excessive matrices and unsupported credential/session options are not silently treated as a proven path. Account and role-path matching are checked. No remediation is applied and no secret value is read.

The same external `aws-actions/configure-aws-credentials` commit (`ec8e608231b771e3614fc6ea4edadab8703331a5`) now yields **33 expanded job variants and 36 source-backed identity-request variants across 17 declarations**, with **zero matrix exclusions**, versus the prior seven excluded matrix jobs. All role values remain unresolved, no matching IAM declarations are present and no cloud path is proven. The additional evidence exposes 17 unresolved role locations, 12 local-action sites and four unsupported credential/session-option sites instead of hiding them behind matrix exclusions. This is improved coverage, not a claim of new vulnerabilities or complete assessment.

**Zero findings means no complete path was proven within the profile, not that the repository is safe.** Live IAM state, Terraform/expression evaluation, private remote authentication, environment OIDC subjects, full policy composition and arbitrary providers remain unsupported. This is a bounded local review tool, not an assurance of production security. The local HTTP service is for a trusted workstation, not multiuser hosting or hostile-local-process isolation. See [SECURITY.md](SECURITY.md).

The current direction is in [WP_PROJECT_CONTINUATION_PROMPT.md](WP_PROJECT_CONTINUATION_PROMPT.md); this delivery is specified in [WP_SPEC_repository-review.md](WP_SPEC_repository-review.md). Existing visual/research artifacts and user changes are preserved rather than folded into this focused app. This project is unrelated to the Blast-RADIUS RADIUS/UDP protocol vulnerability.

## Historical Standards Overview

The material below records the earlier standards/research direction and its commands. It remains available as supporting infrastructure; its standards-only scope statement does not override the repository-first direction above.

Blast Radius is **not a product**. This directory contains a candidate cross-platform authorization-reach specification, free public conformance suite/reference implementation, and a planned aggregate-data protocol. The specification/profile is1.0-draft; the existing Python implementation and graph wire format remain0.1. No real tenant is contacted or represented, no paid tier or certification exists, and no neutral host or real dataset is claimed.

Start with `spec/METRIC_SPECIFICATION_v1.0-draft.md`, CONFORMANCE.md, PRIVACY_ANALYSIS.md, research/NHI_RESULTS.md, RECONSTRUCTION_METHOD.md and GOVERNANCE.md. LICENSING.md assigns Apache-2.0 to code, CC-BY-4.0 to specification/schema and CC0-1.0 to generated/approved aggregate data. The single existing `demo/index.html` is preserved as an illustrative reference aid, not an executive product roadmap.

## Standards Quickstart

```powershell
.venv/Scripts/blastradius.exe conformance run --tool '.venv/Scripts/python.exe -B -m blastradius conformance adapter'
.venv/Scripts/python.exe -B tools/build_reconstructions.py
.venv/Scripts/python.exe -B tools/run_research.py
.venv/Scripts/python.exe -B tools/verify.py
```

Run from this directory after installing the local package as below. The suite includes 40 frozen fixtures across three required models (120 cases), exact rational values, pair sets, deterministic witnesses and two executions per case. **Python and JavaScript both pass 120/120; the integrated Python suite passes 179 tests.** Reports are in conformance/reports/reference and conformance/reports/javascript. Re-running research validates the frozen protocol hashes before recreating the 500 paired synthetic populations.

Optional artifacts are complete within their stated bounds: `node reference-js/verify.mjs` checks the second-language reference; `tools/build_kubernetes_fixture.py` generates the offline read-only Kubernetes normalization fixture (17 tests); research/STATE_OF_BLAST_RADIUS_TEMPLATE.md is a future aggregate-report template, not a published industry finding. The clean wheel passed all 120 core cases under isolated Python outside the source tree. See TEST_REPORT.md for exact evidence and remaining gaps.

Measured:500/500 exact structural summaries were unique; rounding counts left161/500 unique. The prespecified epsilon ln2 aggregate had1.014762 count MAE including suppression and96.8% retained synthetic support. NHI primary joint successes were54/500 under the null,250/500 with deliberately broader NHI grants and54/500 with deliberately broader human grants. These are synthetic falsification/sanity checks, not real-population findings. The five reconstruction dossiers contain four supported incident mechanisms and one explicitly hypothetical MLflow post-acquisition scenario; historical top-decile ranks are unidentified.

## Five-Command Quickstart

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[test]"
.venv/Scripts/blastradius.exe synth --principals 80 --resources 40 --seed 7 --out results/tenant.json --force
.venv/Scripts/blastradius.exe analyze results/tenant.json --constraint-model default --out results/result.json --force
.venv/Scripts/blastradius.exe report results/result.json --format html --out demo/index.html --force
```

These legacy demo workflows have been executed. Private signing keys and local signed result files must not be committed; public synthetic conformance/research reports are intentionally versioned. Fictional names and credential metadata only. Existing output files require `--force`; input files cannot be overwritten. On macOS/Linux replace `.venv/Scripts` with `.venv/bin`. Do not regenerate a user-edited demo unless its changes have been reviewed.

Additional commands: `blastradius explain results/result.json --credential credential-principal-00001`, `blastradius whatif results/tenant.json --remove-binding shared-2`, and `blastradius verify-manifest results/result.json`. Reports support `--format json|sarif|html|md`. An external OS-random local HMAC key is created at the platform's local application-data directory; it is not shipped with artifacts. Another machine can regenerate its own signed result, but verifying an existing result requires trusted access to its original key.

See TEST_REPORT.md for actual fixture/coverage/benchmark results and demo/DEMO_SCRIPT.md for the exact five-minute walkthrough. No runtime server or CDN is required.

## Earlier Prototype Measurements

The earlier prototype session recorded108 passing pytest tests and94.81% Python line coverage; current standards-session checks are recorded separately in TEST_REPORT.md. The10000-principal,2000-resource,32119-edge synthetic pipeline completed in51.63 seconds; the50000-principal stretch completed in215.38 seconds. These historical scale runs were not repeated as research population observations. Benchmark scope and exclusions are in TEST_REPORT.md.

The dashboard's 80 fictional credentials have a maximum canonical radius of 51.26%, p95 34.45%, and Gini 0.026. Every number is generated by the analyzer; 90 single-binding removals were actually evaluated. The best modeled change reduces p95 to 27.73%. These are constructed-tenant results, not claims about real organizations.

## Reproduce and Inspect

```powershell
.venv/Scripts/python.exe -B tools/verify.py
.venv/Scripts/python.exe -B tools/build_demo.py
.venv/Scripts/blastradius.exe collect-entra-azure --exports connectors/entra_azure/fixtures/rich --out results/connector-tenant.json
.venv/Scripts/blastradius.exe collect-aws-iam --exports connectors/aws_iam/fixtures/basic --out results/aws-tenant.json
.venv/Scripts/blastradius.exe submit results/result.json --dry-run
```

Existing output files need `--force`. The Entra/Azure adapter and optional bounded AWS adapter are offline-verified only; read their connector manifests and limitations. The Graph/ARM live transport is library-only, disabled by default and mock-tested, not a live tenant scanner. The structural preview is explicitly not anonymous and cannot submit anything. CI workflow source is included but has not run on GitHub in this session.

See ARCHITECTURE.md, DECISIONS.md, HANDOVER.md, SECURITY.md and tests/fixtures/README.md for module boundaries, technical criticisms, deferred work and independent hand calculations.

The five-command demo quickstart is for a freshly extracted copy; skip environment creation if a working environment already exists. `--force` deliberately replaces only generated outputs, never input files. A clean wheel installation of the earlier prototype was tested under Python `-I` from outside the source tree; it is not a claim that an old wheel includes subsequent standards additions. Public conformance needs neither cloud access nor the private HMAC key.
