# Spec: GitHub Actions and AWS OIDC Repository Evidence

Module id: `repository-evidence`

Status: **Approved for implementation**

Capability map: `WP_CAPABILITY_MAP.md`

Created: 2026-09-15

## Objective

Parse one deliberately bounded repository configuration profile and emit source-backed facts—not vulnerability verdicts—from:

- GitHub Actions workflow YAML under `.github/workflows/`.
- AWS IAM roles declared in CloudFormation JSON templates.

The profile connects a workflow that can request a GitHub OIDC token to a literal AWS role ARN and a declared role trust/permission policy. It preserves exact source locations, explicit unsupported diagnostics and the acquisition snapshot hash so downstream graph construction can distinguish repository evidence from deployed-cloud verification.

The first user is a platform or security engineer reviewing whether a repository's declared CI/CD identity can reach a declared AWS Secrets Manager resource.

## Scope Revision from the Capability Map

The capability map proposed Terraform as the initial IaC source. This specification proposes **CloudFormation JSON first** for the executable slice because:

- IAM trust and inline permission documents can be represented as literal JSON objects.
- Parsing does not require evaluating HCL expressions, modules, providers or Terraform state.
- A single safe YAML/JSON node parser can retain line and column marks for workflow and policy evidence.
- Unsupported intrinsic functions and dynamic values can be rejected explicitly.

Terraform remains the next IaC profile after this slice. This is a scope reduction, not a claim that CloudFormation is more popular or complete.

## Authoritative Semantics

The profile follows these external contracts:

- GitHub requires `permissions: id-token: write` at workflow or job level before a job can request an OIDC token. This permission allows token request; it does not itself grant cloud-resource write access: <https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws>
- The supported credential-exchange step is `aws-actions/configure-aws-credentials` with a literal `role-to-assume`: <https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws>
- AWS role trust must allow `sts:AssumeRoleWithWebIdentity` for the GitHub OIDC provider and constrain `token.actions.githubusercontent.com:sub`; `aud` is expected to be `sts.amazonaws.com`: <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html>
- GitHub workflow trigger and branch syntax follows the GitHub Actions workflow syntax reference: <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax>

Documentation establishes syntax and mapping rationale. Repository declarations do not prove deployed AWS state.

## Proposed Dependency

Add exactly one runtime dependency:

```toml
PyYAML==6.0.3
```

Use the node-composition API rather than object construction so source marks are retained. Use a restricted loader/resolver profile that treats GitHub's top-level `on` key as a string, rejects custom tags and merge keys, limits node count/depth and never constructs Python objects.

The dependency is already available in the current development environment but is not declared by the project. The user directed implementation to continue on 2026-09-15, approving this bounded dependency and scope.

## Inputs

The evidence collector receives:

```python
collect_repository_evidence(
    root: Path,
    manifest: dict,
    repository_slug: str,
) -> dict
```

Requirements:

- `root` is the same local repository acquired by `safe-local-v0.1`.
- `manifest` is a structurally valid acquisition manifest.
- `repository_slug` is explicitly supplied as lowercase-or-case-preserved `owner/repository` metadata and must contain exactly one slash with GitHub-compatible nonempty components.
- Every parsed file must appear in the manifest.
- Before parsing, the collector reopens the file without following links and verifies its current size and SHA-256 against the manifest.
- A mismatch fails the entire evidence collection as a changed snapshot; stale evidence must never be silently produced.

The repository slug is treated as user-supplied context for a local checkout. It is not claimed to have been verified against `.git/config` or GitHub. A future URL-acquisition profile will derive and verify it.

## Selected Files

### GitHub Actions

Select only regular manifest entries matching:

```text
.github/workflows/*.yml
.github/workflows/*.yaml
```

Nested directories under `.github/workflows/` are not part of GitHub's workflow-file profile and are reported as ignored.

### CloudFormation

Select only regular manifest entries ending in one of:

```text
.template.json
.cfn.json
.cloudformation.json
```

A selected document must have an object root and a `Resources` object. Unsupported or malformed selected templates produce controlled diagnostics; malformed documents do not become partial trusted evidence.

## Supported GitHub Actions Profile

Support only:

- Object-root workflow documents.
- Literal workflow `name` or path fallback.
- Top-level or job-level `permissions` objects.
- `id-token: write` inherited from top level or overridden at job level.
- `on: push` with a literal `branches` list containing exact branch names without glob metacharacters.
- Job objects with literal identifiers.
- Optional literal job `environment` string.
- Step lists.
- `uses` values matching `aws-actions/configure-aws-credentials@<reference>`.
- Literal `with.role-to-assume` AWS IAM role ARN.
- Optional literal `with.audience`, defaulting to `sts.amazonaws.com` when omitted according to the supported action profile.

Record but do not interpret other triggers, permissions, steps and job fields.

Reject one job from the supported OIDC path, while continuing to inspect other jobs, when it contains:

- A dynamic/expression-based role ARN.
- Dynamic permissions.
- Matrix-dependent values.
- Reusable workflow `jobs.<id>.uses` semantics.
- An unsupported environment object.
- YAML aliases, merge keys or custom tags.
- Duplicate mapping keys.
- Excessive node count/depth or malformed YAML.

The collector must not infer that `pull_request`, `pull_request_target`, or any trigger is exploitable. Trigger facts are evidence only. The downstream threat scenario begins with an explicitly assumed compromised workflow/job.

## Supported CloudFormation IAM Profile

Support only `AWS::IAM::Role` resources with:

- Literal `Properties.RoleName`.
- Literal object `Properties.AssumeRolePolicyDocument`.
- Literal list `Properties.Policies` containing literal object `PolicyDocument` values.
- Optional literal `Properties.Tags`; a tag with key `BlastRadiusSensitivity` and value `critical` can mark granted resources as sensitivity `1.0` only when the resource ARN itself is literal.

Trust-policy support is limited to statements with:

- `Effect: Allow`.
- `Principal.Federated` ending exactly in `oidc-provider/token.actions.githubusercontent.com`.
- `Action` equal to or containing `sts:AssumeRoleWithWebIdentity`.
- `Condition.StringEquals` for `token.actions.githubusercontent.com:aud` equal to `sts.amazonaws.com`.
- `Condition.StringEquals` or `Condition.StringLike` for `token.actions.githubusercontent.com:sub`.

The first verified declared match requires a subject exactly equal to:

```text
repo:<repository_slug>:ref:refs/heads/<supported exact push branch>
```

`StringLike` wildcard subjects are recorded as broad-trust evidence and potential matches, never as an exact verified-repository match. Conditions using intrinsic functions, variables or unsupported operators are reported as unsupported.

Permission-policy support is limited to statements with:

- `Effect: Allow`.
- No `Condition`, `NotAction`, `NotResource`, or unsupported policy element.
- Action equal to or containing `secretsmanager:GetSecretValue`.
- One or more literal Secrets Manager resource ARNs without wildcard characters.

Explicit denies and all unsupported statements are preserved as diagnostics and not converted into allow facts. The collector does not claim that absence of a supported allow means no access.

## Role Matching

A workflow's literal role ARN must have the shape:

```text
arn:aws:iam::<12-digit-account-id>:role/<role-path-or-name>
```

The final role-name segment must equal a declared literal CloudFormation `RoleName`. The profile does not evaluate `Fn::GetAtt`, `Fn::Sub`, `Ref`, AWS partitions other than `aws`, path ambiguity, cross-stack references or generated role names.

No match produces a `ROLE_DECLARATION_NOT_FOUND` diagnostic and a workflow-role reference fact with `confidence: potential`; it does not create a verified trust fact.

## Evidence Location Contract

Every fact and diagnostic tied to source contains:

```json
{
  "path": ".github/workflows/deploy.yml",
  "start_line": 12,
  "start_column": 7,
  "end_line": 16,
  "end_column": 1
}
```

Lines and columns are one-based. End positions are exclusive. Locations must come from parser node marks, not substring search. No absolute path appears in evidence.

## Output Contract

The collector emits canonical JSON-compatible data:

```json
{
  "format_version": "0.1",
  "profile": "github-actions-aws-cfn-v0.1",
  "repository": {
    "slug": "acme/payments",
    "snapshot_hash": "<acquisition snapshot hash>"
  },
  "facts": {
    "workflows": [],
    "oidc_role_requests": [],
    "aws_roles": [],
    "aws_trusts": [],
    "aws_secret_grants": []
  },
  "diagnostics": [],
  "coverage": {
    "selected_files": 0,
    "parsed_files": 0,
    "unsupported_files": 0,
    "workflow_files": 0,
    "cloudformation_files": 0
  },
  "evidence_hash": "<sha256 of canonical output without evidence_hash>"
}
```

Each fact has a stable deterministic ID derived from its fact kind, source path, semantic key and source location. IDs must not depend on traversal order or wall-clock time.

Confidence vocabulary:

- `repository-verified`: literal repository syntax directly establishes the fact.
- `declared-configuration`: supported IaC declares the relationship, but deployment is not verified.
- `potential`: a reference exists but required matching or external state is unavailable.

No fact may use a higher confidence than its weakest required source.

Diagnostics contain stable machine codes, severity, plain-language message and optional source location. Messages do not echo secret values, absolute paths or arbitrary source content.

## Commands

During this module, expose an intermediate diagnostic command only if it materially improves testing:

```powershell
blastradius inspect-repo-evidence C:\path\to\repository `
  --repository-slug acme/payments `
  --out C:\outside\evidence.json
```

The preferred final product command remains a later orchestrated command such as `analyze-repo`; users should not ultimately need to manually chain manifest and evidence files.

Development verification:

```powershell
pytest -q tests/test_repository_evidence.py tests/test_cli.py
pytest -q
git diff --check
```

## Project Structure

```text
src/blastradius/repository/
    acquisition.py       existing safe snapshot boundary
    yaml_nodes.py        restricted YAML/JSON node parsing and locations
    evidence.py          workflow/CloudFormation selection and evidence output
    github_actions.py    bounded workflow facts
    aws_cloudformation.py bounded role/trust/secret-grant facts

tests/
    test_repository_evidence.py
    fixtures/repositories/aws-oidc-path/
        .github/workflows/deploy.yml
        infra/identity.template.json
```

No parser module imports or mutates the existing analysis engine.

## Code Style

Use small pure extraction functions returning facts and diagnostics. Never use truthiness to distinguish a missing YAML node from a false-like scalar.

```python
def location(path, node):
    return {
        "path": path,
        "start_line": node.start_mark.line + 1,
        "start_column": node.start_mark.column + 1,
        "end_line": node.end_mark.line + 1,
        "end_column": node.end_mark.column + 1,
    }
```

Stable sorting keys and diagnostic codes are part of the output contract and require tests.

## Testing Strategy

Create a hand-auditable positive fixture and independent expected facts. Do not generate expected evidence by running the implementation under test.

Required positive tests:

- Workflow-level and job-level `id-token: write` inheritance/override.
- Literal configure-credentials role request.
- Exact push-branch subject match.
- Exact audience and GitHub federated principal match.
- Literal Secrets Manager grant.
- One-based source locations.
- Deterministic fact IDs, sorting and evidence hash.
- Repeated byte-identical output.

Required negative/adversarial tests:

- No `id-token: write`.
- Dynamic role expression.
- Role declaration missing or ambiguous.
- Subject mismatch.
- Broad wildcard subject labeled potential.
- Missing/wrong audience.
- Unsupported trust condition operator.
- Explicit deny not treated as allow.
- Wildcard secret resource not treated as finite grant.
- Duplicate YAML/JSON mapping key.
- Alias, merge key and custom tag rejection.
- YAML node-count/depth limit.
- Manifest hash/size mismatch after acquisition.
- Selected file changed to a link/reparse point before parse.
- Parser/diagnostic output contains no absolute paths or source values.
- Repository content cannot trigger object construction, subprocesses or network access.

Regression requirement: all existing tests and conformance cases remain unchanged.

## Boundaries

### Always do

- Reverify every selected file against the acquisition manifest before parsing.
- Preserve parser-derived source locations.
- Label repository declarations separately from deployed state.
- Emit unsupported diagnostics instead of silently approximating.
- Require exact literal values for the first verified path.
- Keep deterministic output and controlled errors.

### Ask before changing

- Add `PyYAML==6.0.3` as a runtime dependency.
- Support Terraform/HCL or execute any IaC evaluator.
- Read Git configuration or invoke Git.
- Infer exploitability from a GitHub event trigger.
- Add live GitHub or AWS API access.
- Expand the action/resource catalog beyond the specified secret-read case.

### Never do

- Execute a workflow, action, script, package or IaC command.
- Construct arbitrary YAML tags or Python objects.
- Resolve CloudFormation intrinsic functions by guessing.
- Treat a repository declaration as proof of deployment.
- Emit secret values or unredacted arbitrary source content.
- Create a graph edge from unsupported or ambiguous syntax.
- Report “safe” merely because no supported fact was found.

## Success Criteria

1. A positive fixture yields deterministic workflow, OIDC role request, exact trust and finite secret-grant facts with source locations.
2. A stale or changed acquisition snapshot fails closed.
3. Unsupported and dynamic constructs produce explicit diagnostics without creating verified facts.
4. No repository content is executed or emitted.
5. Evidence distinguishes `repository-verified`, `declared-configuration` and `potential` confidence.
6. The output states that deployed AWS state is unverified.
7. Targeted parser tests and the full existing suite pass.
8. The module does not change existing graph/analysis semantics.

## Open Questions for Review

1. Approve adding the pinned `PyYAML==6.0.3` runtime dependency?
2. Approve CloudFormation JSON as the first IaC slice, with Terraform explicitly next?
3. Should wildcard GitHub subject trust produce a potential fact plus high-severity diagnostic, or only a diagnostic? This spec proposes both because the broad trust is material but not an exact repository match.
4. Should a malformed selected file fail the entire evidence collection or produce an unsupported-file diagnostic while parsing other files? This spec proposes a diagnostic and continued parsing, except duplicate keys, unsafe YAML features, resource-limit failures and snapshot mismatches fail the whole collection.

## Approval Record

The user directed implementation to continue on 2026-09-15, approving the dependency, CloudFormation-first scope and proposed open-question defaults. Cross-model review was offered and skipped in favor of continued implementation. Behavioral claims require failing-first tests and full regression verification.
