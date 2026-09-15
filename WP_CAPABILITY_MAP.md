# Capability Map: Repository-to-Production Attack Paths

Status: **Proposed for review**  
Created: 2026-09-15  
Active objective: make a GitHub repository a practical primary input without weakening the existing deterministic Blast Radius engine.

## Product Boundary

The first product slice will analyze a repository's GitHub Actions and a deliberately bounded infrastructure-as-code profile, translate supported evidence into the existing authorization graph, and report a deterministic path from an assumed workflow compromise to a declared sensitive resource. It will also simulate one path-breaking remediation.

This is not a generic secret scanner, a complete cloud authorization evaluator, or a system that executes repository code.

## Assumptions to Validate

1. The first user is a platform or security engineer reviewing CI/CD access to production.
2. The first acquisition mode is a local Git checkout; public GitHub URL acquisition follows after untrusted-input boundaries are tested.
3. The first provider slice should use GitHub Actions plus AWS OIDC/IAM declarations because the repository already has a bounded AWS policy normalizer and these relationships are explicit in common IaC.
4. The first interface is a deterministic CLI/JSON contract; the visual product flow follows once the analysis slice is proven.
5. The existing graph and analysis engine remain unchanged unless a documented incompatibility forces a versioned extension.
6. Repository source and IaC describe declared intent, not necessarily deployed reality; every result must expose that limitation.

## Modules

### `repo-acquisition`

Responsibility:

- Resolve and inventory one local Git repository without executing it.
- Establish repository root, commit/ref, file limits and safe path handling.
- Reject traversal, out-of-root symlinks and unsupported acquisition states.

Provides:

- A deterministic repository snapshot manifest containing safe relative paths, sizes, hashes and the observed Git revision when available.

Depends on: none.

### `repository-evidence`

Responsibility:

- Parse a bounded set of GitHub Actions constructs.
- Parse only the IaC/provider constructs required by the first scenario.
- Emit source-backed facts with file and line provenance.
- Record unsupported, ambiguous and missing semantics instead of guessing.

Provides:

- A versioned evidence document containing repository facts, assumptions, diagnostics and coverage.

Depends on: `repo-acquisition`.

### `evidence-graph`

Responsibility:

- Convert supported repository evidence into canonical Blast Radius principals, credentials, bindings, resources, constraints and edges.
- Preserve traceability from every derived graph element to source evidence.
- Validate the resulting graph through the existing model boundary.

Provides:

- A validated internal graph plus a source-evidence index.

Depends on: `repository-evidence`.

### `path-analysis`

Responsibility:

- Invoke the existing deterministic reachability and analysis engine.
- Define the supported repository-compromise starting credential and attacker-model mapping.
- Preserve existing conformance behavior and exact result determinism.

Provides:

- Reachable resource/action pairs, deterministic witnesses, blocked paths and before/after metrics.

Depends on: `evidence-graph`.

### `findings-remediation`

Responsibility:

- Turn engine output into an evidence-backed path story.
- Report impact, confidence, coverage, assumptions and unsupported semantics.
- Map one safe configuration change to a graph intervention and verify that it breaks or reduces the path.

Provides:

- A versioned finding document and deterministic remediation comparison.

Depends on: `path-analysis` and the source index from `evidence-graph`.

### `product-interface`

Responsibility:

- Expose repository analysis through a clear command and, after the slice is validated, a user-facing import/review/path/remediation flow.
- Never hide parser coverage or treat potential paths as verified deployed access.

Provides:

- Initial CLI and JSON output; later, a focused visual workflow and report export.

Depends on: `findings-remediation`.

## Dependency Direction

```text
repo-acquisition
    -> repository-evidence
    -> evidence-graph
    -> path-analysis
    -> findings-remediation
    -> product-interface
```

Dependencies flow in one direction. The existing engine must not import repository-parser or interface code.

## Build Order

1. `repo-acquisition`
2. `repository-evidence`
3. `evidence-graph`
4. `path-analysis`
5. `findings-remediation`
6. `product-interface`

The first end-to-end checkpoint spans all six modules but implements only one bounded GitHub Actions -> AWS OIDC/IAM -> sensitive resource scenario.

## First-Slice Acceptance Boundary

The capability map is successful when it supports a fixture repository in which:

1. A GitHub Actions workflow has an explicitly supported trigger and permission profile.
2. The workflow can request an OIDC token for a declared AWS role.
3. Terraform/IAM declarations define the trusted repository/ref and a finite resource/action grant.
4. One resource is explicitly classified as sensitive within the fixture's supported metadata profile.
5. The tool reports the source-backed path from workflow compromise to that resource.
6. The output distinguishes repository-verified facts from declared-IaC derivation and unknown deployed state.
7. A supported trust or grant restriction removes the path in a deterministic counterfactual.
8. Malicious repository content is treated as data and never executed.

## Explicitly Deferred

- Private GitHub authentication and token custody.
- Arbitrary remote repository cloning in a server environment.
- Full GitHub Actions expression evaluation.
- Runtime workflow behavior and third-party action execution.
- Full Terraform evaluation, modules, providers or state reconciliation.
- Full AWS IAM/Organizations/resource-policy semantics.
- Azure, GCP and broad Kubernetes support.
- Live cloud verification and drift detection.
- Automated remediation writes.
- Multi-repository portfolio dashboards.

## Review Gate

Approve or revise the module boundaries, dependency direction, build order and six assumptions before module specifications or implementation begin. Once approved, each module will receive a scoped specification and acceptance tests in dependency order.
