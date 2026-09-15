# Spec: Repository Evidence Graph, Path Finding and Remediation

Module ids: `evidence-graph`, `path-analysis`, `findings-remediation`, initial `product-interface`

Status: **Approved for implementation by the user's continuing build direction**

Capability map: `WP_CAPABILITY_MAP.md`

Created: 2026-09-15

## Objective

Complete the first useful vertical slice. Convert only exact supported repository evidence into a truthful authorization graph, run the existing deterministic engine, and emit a plain-language finding showing a declared path from a compromised GitHub Actions job to a finite AWS Secrets Manager resource plus a simulated remediation that breaks that path.

The final user command is:

```powershell
blastradius analyze-repo C:\path\to\repository `
  --repository-slug owner/repository `
  --out C:\outside\repository-analysis.json
```

The output is repository/IaC analysis, not proof of deployed AWS access.

## Graph Versioning Decision

The frozen graph v0.1 schema requires `synthetic: true`, a fictional organization name and timestamp-based provenance. Repository-derived evidence may come from a real repository and must not be mislabeled fictional.

Add graph schema v0.2 without changing v0.1:

- `schema_version: "0.2"`.
- `synthetic: false` for this repository-derived profile.
- `source_kind: "repository-declared-configuration"`.
- `organization` contains the explicitly supplied repository slug.
- `observed_at: null`; determinism is anchored to the acquisition snapshot hash, not a fabricated timestamp.
- Provenance contains `connector`, `source_api`, `snapshot_hash` and `evidence_ref`.

`model.validate` selects the schema strictly by `schema_version`. Existing v0.1 conformance bytes and semantics remain unchanged.

## Exact Evidence-to-Graph Mapping

Create graph elements only when an OIDC request has `trust_match: exact-declared-configuration`.

Mapping:

- Workflow -> principal, subtype `workload_identity`.
- Workflow compromise start -> credential, subtype `federated_trust`, owned by the workflow principal.
- Credential -> workflow principal via `authenticates_as`.
- Matched CloudFormation IAM role -> principal, subtype `service_principal`.
- Workflow principal -> role principal via `can_assume`; provenance points to both the workflow role request and exact trust facts through a deterministic compound evidence reference.
- Role -> allow binding via `assigned`.
- Binding -> finite Secrets Manager resource via `grants` with `read_secret`.
- Secret ARN -> resource, subtype `secret_store`, actions `["read_secret"]`, sensitivity `1.0` under this explicit finite profile.
- Action weight for `read_secret` is `1`; the finding emphasizes concrete reach and does not market this one-resource denominator as a tenant-wide score.

Broad/potential trust, unmatched roles, unsupported policies and dynamic values do not create graph edges.

## Finding Contract

The output profile is `repository-attack-path-v0.1` and contains:

- Repository slug, acquisition snapshot hash and evidence hash.
- Coverage and diagnostics from evidence collection.
- A summary with finding count and declared reachable-secret count.
- Findings sorted by stable ID.

Each finding includes:

- Title and `priority: high` because the supported impact is secret-value read.
- `confidence: declared-configuration`.
- Explicit start condition: compromise of the named workflow job is assumed, not discovered.
- Concrete impact: declared `secretsmanager:GetSecretValue` on one finite ARN.
- Deterministic graph path with edge kind, source/target names and source evidence references/locations.
- Before reach, after reach and whether the path is broken.
- A remediation simulation that removes the workflow-to-role trust edge only in the model; it never edits source or AWS.
- `deployed_aws_state: unverified`.

No opaque aggregate score replaces the path or evidence.

## No-Finding Contract

If no exact complete path exists, emit a successful analysis with zero findings, preserved diagnostics and an explicit message:

> No complete path was proven within the supported repository profile; this is not evidence that the repository or deployed environment is safe.

Do not build or validate an empty-universe graph solely to manufacture a zero score.

## Determinism

- Graph IDs derive from evidence fact IDs and semantic identifiers.
- No wall-clock timestamp, random ID or ambient Git state enters output.
- Finding ID derives from snapshot hash, workflow/job, role and resource.
- The same bytes, slug and profile produce byte-identical canonical output.

## Public Python Boundaries

```python
def build_repository_graph(evidence: dict) -> tuple[dict | None, dict]:
    """Return a validated v0.2 graph when exact complete paths exist plus an evidence index."""


def analyze_repository(root: Path, repository_slug: str) -> dict:
    """Acquire, extract, map, analyze and simulate the bounded repository path."""
```

## Project Structure

```text
schema/blastradius-graph-v0.2.schema.json
src/blastradius/assets/blastradius-graph-v0.2.schema.json
src/blastradius/repository/graph.py
src/blastradius/repository/findings.py
tests/test_repository_graph.py
tests/test_repository_findings.py
```

## Testing Strategy

Required tests:

- Frozen v0.1 fixtures still validate and all existing conformance tests remain unchanged.
- v0.2 accepts repository-declared provenance and rejects synthetic/source-kind mismatches.
- Positive fixture maps to one workflow credential, role, binding, secret resource and four-edge path.
- Every graph edge has a resolvable evidence reference.
- Broad trust and unsupported evidence produce no graph path.
- Final finding contains the explicit compromise assumption and deployed-state limitation.
- Remediation removes only the modeled trust edge, changes reach from one to zero and reports `path_broken: true`.
- Analysis does not mutate the graph or source repository.
- Repeated output is byte-identical.
- CLI stdout/file/overwrite/internal-output behavior matches the acquisition commands.
- Full test suite and diff check pass.

## Boundaries

### Always do

- Keep v0.1 schema and conformance behavior byte-compatible.
- Validate every v0.2 graph before engine use.
- Map only exact supported evidence.
- Preserve source evidence and confidence in findings.
- State that deployed AWS was not checked.
- Simulate remediation without editing source or infrastructure.

### Never do

- Label real repository evidence synthetic or fictional.
- Turn broad/potential trust into a verified graph edge.
- Claim tenant-wide risk from the finite one-profile universe.
- Apply remediation automatically.
- Hide evidence diagnostics when a finding exists.
- Report zero findings as safe.

## Success Criteria

1. One command accepts a repository path and slug and emits a deterministic source-backed attack-path result.
2. The positive fixture shows the complete workflow -> OIDC -> role -> secret path.
3. A simulated trust removal breaks the path and reduces absolute reach from one to zero.
4. Real repository evidence is represented as non-synthetic v0.2 data without altering v0.1.
5. Missing/unsupported evidence produces an honest no-proof result, never a safe verdict.
6. All existing and new tests pass and changes are pushed to `WP_repository-input`.

