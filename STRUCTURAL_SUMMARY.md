# Structural Summary v1.0-draft

License: CC BY 4.0. This is the exact local `submit RESULT --dry-run` stdout contract, not an upload endpoint and not an anonymity claim. The command verifies the local result's integrity, then emits one JSON object and one newline, with no wrapper, names or narrative field. Current code accepts synthetic input only. Changing the payload requires a new schema and privacy review before real intake.

## Exhaustive Field List

Every object is closed (`additionalProperties:false`). Counts are integers in [0,1000000000]; missing fields, additional fields and inconsistent totals reject.

| Field | Exact allowed content |
| --- | --- |
| summary_version | constant `1.0-draft` |
| synthetic | constant true; no real tenant accepted |
| submission_enabled, privacy_reviewed, anonymous | constant false, independently of absence of names |
| schema_version | constant `0.1` (graph wire schema) |
| metric_profile | constant `1.0-draft` |
| normalizer_profile | constant `unasserted`; does not pretend the source was a conforming cloud collector |
| constraint_model | default, strict, session-theft-aware |
| action_profile | core-1-3-5 or custom-not-comparable |
| node_counts | principal, credential, binding, resource, constraint |
| principal_counts | human_user, service_principal, managed_identity, workload_identity, ai_agent, group |
| credential_counts | password, key, certificate, token, passkey, federated_trust |
| edge_counts | authenticates_as, member_of, assigned, grants, can_assume, can_read_secret, constrained_by |
| structural_features | shared_binding_count, eligible_binding_count, constrained_item_count |
| canonical_radius_histogram | exactly ten entries; each has lower, upper, upper_inclusive, count |

Histogram bucket i covers [i/10,(i+1)/10), except the final bucket includes1. Integer rational binning uses absolute_reach/universe_size, not rounded display floats. Shared bindings have more than one distinct assigned subject. Constrained items are distinct bindings/edges with a nonempty constraint list or a constrained_by annotation. All binding effects count structurally, not only reachable bindings.

Subtype counts must sum to the corresponding node kind, and histogram counts must sum to credential count. The machine schema is `schema/structural-summary-v1.0-draft.schema.json`, deterministically emitted by the tested `summary_schema()` function. `normalizer_profile` cannot identify a tenant or a private connector build; future registered collector versions require a new enum, not free text.

## Deliberately Absent

No organization identifier, cloud tenant/account ID, name, URL, email, ARN, path, principal/resource/credential/edge ID, timestamp, fingerprint/hash, signature, secret value, raw policy, free-text evidence, individual credential score, exact resource-action pair or user-agent string is permitted. The contributor's local graph and result retain those details; the summary never copies them. No network submission exists.

Exact aggregate counts and histograms can nevertheless identify a tenant by linkage to public size/composition data. Therefore raw summaries are NOT proposed for public release. Synthetic copies are published only as test data. The synthetic uniqueness experiment evaluates exact, rounded and deliberately minimal versions; it is not a claim that real enterprises share those distributions.

## Proposed Aggregate, Not Raw Dataset

The current research mechanism publishes a fixed21-cell histogram:20 cells are the cross of NHI-minority status and the tenant's binned canonical p95, plus an empty-credential-population cell. Each independently deduplicated tenant contributes exactly one count. NHI minority here refers to all non-group principals in the structural payload, not necessarily the credential-bearing denominator of the preregistered hypothesis; these MUST NOT be conflated. It is a coarse benchmark, not a replacement for the full metric output.

No raw counts, exact support tests, exact total tenant count or sparse selection of field names are released alongside noisy counts. Cells below a fixed threshold on NOISY counts appear as null in an otherwise fixed schema. The primary NHI weighted-union hypothesis cannot be reconstructed from this payload; see PREREGISTRATION.md. Neutral custody, deduplication, independent privacy review, reviewed contribution consent and a durable privacy-budget ledger are prerequisites for any real-data release, not implemented services.
