# Test Report

## Repository Product Refocus Checkpoint

On 2026-09-15, the first complete local-repository analysis slice passed **212 tests with 1 platform-dependent skip in 15.77 seconds**. The new tests cover safe acquisition, marked-node workflow/IaC evidence, non-synthetic graph v0.2 validation, exact evidence-to-path mapping, duplicate secret declarations, deterministic findings, non-mutating remediation simulation, no-proof wording, CLI stdout/file behavior, overwrite refusal, and rejection of output inside the analyzed repository.

The source-tree CLI smoke command successfully produced one four-hop GitHub Actions workflow -> AWS role -> finite Secrets Manager path from the checked-in fixture, with source locations and a trust-removal counterfactual reducing absolute reach from 1 to 0. Deployed AWS state remains explicitly unverified.

Package build was not rerun in this host session: `uv` and the Python `build` module are unavailable, and the fallback pip invocation could not load the pinned setuptools backend from the active interpreter. This is an environment/tooling limitation, not a successful packaging claim; package-data inclusion remains covered by the existing `assets/*` configuration and must be rechecked in the release environment.

## Standards Session: Executed Gate

On 2026-09-09, the final `tools/verify.py` run completed **179 tests in 39.07 seconds, all passing; 1641/1757 Python statements covered (93.397837%)**. This supersedes the intermediate 132-test standards gate and earlier prototype counts. Coverage is not branch coverage or a formal correctness proof; standalone generator/runner execution is additionally recorded below.

- Public conformance revision 2: **both Python and JavaScript passed 120/120 cases**, each run twice, over 40 fixtures and default/strict/session-theft-aware models. Suite SHA-256 `9dc834236ba7cd22c9878705447117c3cc0625ffcb23d7327b57a9456403bfc4`. Exact rational scores, pair sets, population statistics and witnesses are compared. Manifest integrity/path failures reject before invoking a tool. Detailed partial/manual boundaries are in conformance/REQUIREMENT_COVERAGE.md.
- Five reconstruction dossiers and all 30 baseline/control/model outputs were generated and replayed. Four primary-supported incident families plus one explicitly hypothetical MLflow post-acquisition scenario. Ten additional executed rank countermodels keep the target at 1/2 but change its rank from 1/10 to 10/10 under different invented background grants. No actual tenant graph or historical top-decile estimate is claimed. Beacon's 22-page final report was text-extracted and read; its primary-source uncertainty remains explicit.
-500 type-neutral synthetic summaries:500 unique exact profiles,161 unique after rounding,0 unique under the minimal projection but16 rows in groups below10. Selected epsilon ln2/k10/noisy-threshold20:200 seeded trials, mean21-cell count MAE1.014761905 including suppression;96.8% true synthetic support retained.
-500 paired tenant configurations across three regimes (1500 modeled graphs): joint NHI successes54/500 null,250/500 NHI-broader,54/500 human-broader. Protocol/run-plan hashes were saved before generation; all output hashes and selected graph/outcome reproductions pass tests. Synthetic results cannot accept/reject a real-population hypothesis.
- Paper Related Work measured1227 whitespace-delimited words. Governance/specification/paper/research documents passed editor diagnostics. No neutral home, elected steering group, privacy review, real intake, live red-team run, DOI or paper submission exists.
- The single user-edited demo HTML was preserved, not regenerated in this standards session. Historical browser/scale results below remain prior evidence, not new measurements.

### Final Package and Stretch Gates

- JavaScript's dependency-free reference passed `node reference-js/verify.mjs` plus the external runner. Parser checks cover escaped duplicate keys, lossy decimal rejection, large integer preservation and exact canonical-number bytes. This is not independent authorship or a general JSON Schema implementation.
- Kubernetes offline read-only profile: **17 tests passed**, with observer reach 4/6, worker 3/6, both zero-step reach 3/6; sensitivity radii 5/8 and 3/8. Namespace scope, Secret list/watch value access, explicit stored credentials and unsupported-input rejection are tested. No kubeconfig or cluster call is made.
- `uv build --offline` succeeded. `tools/smoke_wheel.py` installed the wheel and only declared cached dependencies in a fresh temporary venv, removed source-path influence and ran isolated Python `-I` outside the source tree: **120/120 public cases and Kubernetes normalization passed**. Tested wheel SHA-256: `1c88ba492753fe5f292fb019e0d0c21413efafd08a38ba0fde38c1d0107c6f68`; any subsequent documentation rebuild receives a new archive hash and is separately audited.
- `tools/audit_release.py` passed 42 checks covering 38 required artifacts, reports, protocol/output hashes and eight theorems. Source-archive inspection found all required artifacts and no keys, virtual environments, live exports or source PDFs. Final checkpoint ZIP bytes are audited against the current source separately.
- Core specification/report/research artifacts were committed locally as `51cb0d1`. Final extension/documentation commits are recorded in the final handover; no remote, public push or GitHub-hosted CI execution occurred.
- Preserved demo SHA-256: `3a73122a30a84d31732e33454ede34b65767f4ed2e1af4f18ba2fb979f869408`. It remains unmodified and is included in the archive and final commit without regeneration. Text line endings are pinned to LF, except the two prospectively hashed protocol documents, whose original CRLF bytes are preserved with `-text`; their pre-data commitments are not rewritten.

## Historical Prototype Session

The previous release recorded **108 tests in16.56 seconds and94.8148% Python line coverage (1152/1215 statements)**. The entries below retain that session's checkpoint history. Only executed measurements are claimed.

## Foundation Checkpoint: Executed

- Command: `../.venv/Scripts/python.exe -B -m pytest tests -q` (also run from parent with the project test path).
- 35 tests passed in 1.06 seconds: 13 hand-computed fixtures, five property tests, schema validation, ground-truth parity, signed-byte determinism and tamper rejection.
- `tools/materialize.py` generated schema/example.json, its independently computed expected file and all thirteen conformance JSON documents.
- A failing permutation test exposed unsorted action arrays in report path evidence; normalizing at the analysis boundary fixed it. The complete suite was rerun successfully.
- Later measured coverage and benchmark records supersede this initial checkpoint below.

## Demo Checkpoint: Executed

- `pytest tests --cov=blastradius --cov-report=term-missing --cov-report=json:results/coverage.json -q`: 41 tests passed in 16.63 seconds; terminal rounded coverage 88% (759 statements, 93 missed; exact percentage is in coverage.json).
- Required workload: 10000 principals, 2000 resources, 32119 edges, 5999 resource-action pairs. Generation 1.408 s; schema validation 36.612 s; analysis 12.983 s; serialization 0.623 s; total 51.626 s. No recommendation search or cloud collection is included. Sparse-tail formula assertions passed.
- Classic workload: 48000 pairs; finance 1240/48000, CI/CD 9600/48000, legacy 31200/48000, Copilot 14400/48000, all asserted. Total 34.127 s. Weighted values derive from the documented constructed graph, not the charter's absent weight profile.
- Dashboard: actual 80-credential result; max 51.2605042%, p95 34.4537815%, Gini 0.0263474682, 100% above 25%. All 90 eligible allow-binding removals evaluated; best `shared-2` lowers p95 to 27.7310924%.
- Browser checks executed at 1440x1000 and 390x844: all 80 rows, 10 histogram bins, search, 20-row agent filter, numeric sort, credential detail and second what-if values. Mobile document width <= viewport. Screenshots inspected.
- Browser tests found and fixed a missing filter assignment and a mobile grid min-width overflow. HTML was regenerated from the same signed result after each fix.

## Connector Checkpoint: Executed

- Integrated suite: 59 tests passed in 23.52 seconds; 1054 executable Python statements, 132 missed (87.48% line coverage). Browser JavaScript is validated by separate interaction assertions, not included in Python line coverage.
- Fifteen initial connector/transport cases and additional artifact tests use only local synthetic exports and fake responses. Basic import: 1/4 and 1/4. Rich import default: 0/6, 2/6, 3/6; permissive: 2/6, 3/6, 4/6.
- GET-only transport checks cover disabled-by-default behavior, method/body restrictions, URL allowlists, redirect refusal, pagination, hostile nextLinks and bounded Retry-After handling. No real tenant call or authentication was performed.
- The installed `collect-entra-azure --exports connectors/entra_azure/fixtures/rich --out results/connector-tenant.json` command ran successfully.
- Microsoft Learn references and explicitly unverified endpoint/permission details are in connectors/entra_azure/manifest.json and PERMISSIONS.md. Corrected Key Vault list API version: 2024-11-01.

## Stretch Benchmark: Executed

Command: `.venv/Scripts/python.exe -B tools/benchmark.py --principals 50000 --resources 2000 --seed 7 --out results/benchmark-50000.json`.

50000 principal/credential records; 2000 resources; 152019 graph nodes; 152119 edges; 5999 resource-action pairs. Generation 9.654 s; schema validation 158.499 s; analysis 45.331 s; serialization 1.902 s; total wall time **215.385 seconds**, below the five-minute target. The serialized full result is 113419685 bytes; only the timing summary is retained for this stretch to keep checkpoint artifacts small. Top ten paths were included; exhaustive intervention search and live collection were excluded. All ordinary principal IDs >=80 matched their independently known sparse-tail counts. The spotlight topology is covered by smaller oracle/conformance fixtures.

Environment for both scale measurements: CPython 3.12.10, Windows 11 build 26200, Intel64 Family 6 Model 170 Stepping 4, 22 logical CPUs. Timing uses perf_counter; no artificial waits or extrapolated estimates. These are not worst-case graph or live-tenant guarantees.

## Hardened Prototype Gate: Executed

`.venv/Scripts/python.exe -B tools/verify.py` ran 87 pytest tests successfully in 31.22 seconds. Coverage: 1014 of 1074 executable statements, **94.4134% Python line coverage**. The entry-point and some subprocess-only lines are not covered by the in-process coverage collector; subprocess workflows were nevertheless actually executed. Branch coverage and JavaScript percentage coverage are not claimed. Saved machine records: results/coverage.json, results/junit.xml and results/pytest-output.txt.

The suite includes 13 small hand-computed fixtures, four classic cardinality checks, two saved connector bundles and six property test functions covering the five requested property categories, including independent-source and same-principal composability. Additional tests check malformed/secret-bearing inputs, unknown semantics, signed tampering, actor-local denies, what-if addition scope, failure retry/exhaustion and safe HTML embedding.

`tools/build_demo.py` re-executed all public demo commands after hardening, verified the HMAC and compared repeated signed result bytes. Manifest hash remained `5e840d2e4fe81cfe54bcbb03a947915957cb6dba01023e63166c96da6331d6c6`; source snapshot hash remained `eba49065f6a70a90c43c6fa7bbe2f452bb60d2dcbed2bf216708a97fe13d584d`.

`uv build --offline --directory . --out-dir dist --quiet` produced a wheel and source archive using cached setuptools 80.9.0. No publication or registry push was attempted. Package-install verification is recorded at the final handover checkpoint.

## Final Integrated Code Gate: Executed

After the bounded AWS adapter, privacy preview and final actor-scoped membership regression, `tools/verify.py` ran **103 tests in 29.11 seconds, all passing**. Coverage: 1151 of 1215 executable statements, **94.7325% Python line coverage**, rounded to 95% by the terminal. The saved coverage/JUnit/output records supersede earlier counts in this checkpoint history.

The AWS fixture asserts user 4/4 and role 2/4, with user zero-escalation reach 2/4. Tests remove either identity permission or trust, reject conditions/boundaries/SCP ambiguity and credential material, and compare decoded versus URL-encoded policy normalization. The structural dry run is socket-blocked in tests and explicitly rejects a real-data marker or non-dry-run invocation.

The final engine regression proves a device-gated group membership cannot authorize a group-derived credential-acquisition edge; both the production queue and independent whole-edge oracle agree. Static membership for deny applicability remains separate, so a stricter attacker model cannot remove a deny to invent access.

## Release Verification: Executed

Final full suite after explicit deny what-if support: **104 passed in 28.97 seconds**. Coverage JSON reports **1149 covered lines / 1213 statements = 94.72382522671063%**; 64 missed lines. The earlier checkpoint counts above are historical. No known failing tests or editor diagnostics remain.

Clean-wheel smoke: installed dist/blastradius_prototype-0.1.0-py3-none-any.whl with only declared runtime dependencies in a fresh temporary venv, removed PYTHONPATH and invoked isolated `python -I -B -m blastradius` from a separate temporary directory. Synth, schema validation, signed analysis, manifest verification, HTML report assets and saved AWS offline ingestion all passed. The wheel includes schema and dashboard assets; the source archive includes hand fixtures, connector manifests and permissions. No signing keys, local environments or real exports were packaged.

Final tools/build_demo.py execution preserved the identical manifest hash and verified every public demo artifact. Desktop (1440x1000) and phone (390x844) checks include the fifth what-if row, exact after-p95 values, no page-width overflow and no external script/style/image dependency. JavaScript was disabled through the browser protocol and all 80 static credential rows remained visible; JavaScript was then restored and the page reloaded.

Benchmark times are the executed session measurements recorded above, not extrapolations or timing claims for arbitrary graphs. The later input/deny/HTML hardening did not change demo values; it was validated by the final suite and full public demo rebuild. Full independent oracle analysis is intentionally limited to small fixtures; the large benchmark uses independently known sparse-tail counts plus small spotlight conformance.

## Final Save Gate: Executed

The release audit added controlled rejection of malformed signature objects and nonobject manifest files; four regression cases were added. The exact tools/verify.py command above then completed with **108 passed in 16.56 s, 1152 covered / 1215 statements, 63 missed = 94.81481481481481%**. The installed verify-manifest command verified the unchanged demo manifest afterward. All editor diagnostics are clean.

OneDrive checkpoint ZIP integrity, required members, SHA-256 receipt, loose-file equality and exclusion of keys/environments were programmatically checked at the release checkpoint. Final copies retain these same checks. Cloud synchronization is not independently verified. No GitHub publication or workflow execution, Azure resource operation, AWS account operation, or real tenant access occurred.
