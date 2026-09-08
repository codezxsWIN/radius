# Public Conformance Profile v1.0-draft

Conformance is free, trademark-free self-assessment against an immutable public suite. No certification authority, paid certificate, vendor endorsement or trademark permission is implied. The claim applies to the normalized core metric, not to a collector's completeness, a vulnerability model, a privacy guarantee or an organization's security.

## Third-Party CLI Contract

Run `blastradius conformance run --tool "COMMAND ARGUMENTS" --suite conformance --out conformance/reports/reference`. The runner invokes the supplied command without a shell, once per case, twice identically for determinism. A command is trusted local code supplied by the operator; this is not an untrusted-code sandbox. Do not run unknown commands against a workspace containing confidential data.

Each invocation receives exactly one UTF-8 JSON request on stdin and MUST emit exactly one UTF-8 JSON response on stdout with no logging/banner; diagnostic logs MAY go to stderr. Exit code MUST be zero even for a documented validation rejection; crashes/nonzero exits/timeouts fail that case. The default timeout is 10 seconds per invocation. The command MUST NOT depend on network access or a private reference signing key.

Request keys: `contract_version: "1.0-draft"`, `input: <graph>`, `parameters: {constraint_model, step_bound, threshold}`. Required models are default, strict and session-theft-aware. Threshold is an exact fraction string (fixtures use 1/4); step bound is a nonnegative integer.

Successful response keys: contract_version, status="ok", snapshot_hash, parameters, credentials, statistics, manifest_hash. Credential records sorted by credential_id contain absolute_reach, universe_size, exact reduced fraction strings for canonical_radius/sensitivity_weighted_radius/action_weighted_radius/step_bounded_radius, sorted reachable_pairs and bounded_pairs. Undefined sensitivity is null. Each metric's statistics contain credential_count, exact maximum/p95/Gini/share strings or null for an empty defined population. The manifest hash is SHA-256 of ASCII canonical JSON (sorted keys, compact separators) excluding manifest_hash. See the frozen expected response in every fixture for the exact contract.

Validation rejection response: `{"contract_version":"1.0-draft","status":"error","error":"INVALID_GRAPH_OR_PARAMETERS"}`. Unknown contract versions use UNSUPPORTED_CONTRACT. Unsupported required graph extensions MUST reject rather than silently drop semantics. Exact semantic JSON equality and identical repeated stdout bytes are both required.

Suite revision 2 adds the required `witness` record per credential: resource_id, action, escalation_steps, graph_hops and ordered edge_ids, or null if no pair is reachable. It also verifies every fixture's byte hash before running a tool. Revision 1 was an internal prepublication draft and did not fully exercise BR-R26; the change is recorded rather than relabeling it as the same frozen suite.

Archived revision1 digest: `1138993b9b993bf01bf3cc89b39cd642025597c0311fd18dc95fe477544c7f5b`. Revision2 digest: `9dc834236ba7cd22c9878705447117c3cc0625ffcb23d7327b57a9456403bfc4`. The runner rejects empty manifests, unsupported profiles, escaping/duplicate paths, missing/mismatched hashes and duplicate fixture IDs before invoking a tool. Operator-supplied commands run with that operator's privileges; this is not an untrusted-program sandbox, and the captured-output size check is post-execution rather than a streaming memory limit.

The wire numeric rule in BR-R24 rejects decimal tokens whose value would change on binary64 parsing; it does not silently round arbitrary-precision decimal input. The additional parser/21-credential p95 regressions are in tests/test_numeric_wire.py. The40-fixture finite suite does not exhaust every parser edge case. Both adapters reject duplicate properties, including escaped aliases; the JavaScript implementation first uses the native parser for syntax and source tokens, then checks decoded property names within object scopes. Broader parser equivalence still requires independent review.

Parameters are a closed object: `constraint_model` is a required-model string, `step_bound` is a nonnegative integer token (not boolean or floating1.0), and `threshold` is a rational STRING whose value is in[0,1], for example `"1/4"`. Numeric/boolean threshold coercion is forbidden. Tool stdout is parsed with duplicate-property and nonfinite/lossy-number rejection. Runner timeout must be finite and strictly positive.

## Claims

Permitted wording: "Tool X version Y passes all core cases in Blast Radius v1.0-draft conformance suite revision Z, SHA-256 H, using the published report at LOCATION." Do not say certified, officially approved, complete for Azure/AWS, private, or secure on the basis of this report. There is no fee or exclusive certification mark.

All fixture/model cases must pass, including invalid-input rejection cases, with no skips. The runner reports pass/fail per tested requirement. BR-R31 disclosure and BR-R32 governance/change-process obligations are manual requirements: attach the report, version, suite digest and any supported extension profiles. Process review is not falsely counted as an executable fixture.

## Expected-Result Independence

Fixtures combine explicit hand derivations with a separate whole-edge closure oracle. Expected Gini uses pairwise absolute differences, independent of the production sorted-rank expression. Expected pair sets and exact ratios are stored, not computed by the tested tool during the run. Changing a fixture requires a new revision and public rationale; running build_conformance.py is a maintainer action, not part of third-party evaluation.

The finite suite can refute a conformance claim but cannot prove all programs correct on all inputs. Cross-platform normalizers need additional platform ground-truth tests. The checked-in report is a reproducible self-test, not external peer review or a certificate.
