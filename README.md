# Blast Radius: Metric Standard and Conformance Artifacts

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
