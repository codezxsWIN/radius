# Architecture

Blast Radius v0.1 is a local, synthetic-only Python prototype. The src-layout package is `blastradius`; `jsonschema==4.26.0` is its only direct runtime dependency. CLI entry point: `blastradius`. There is no hosted service, no live collection CLI, no secret extraction and no platform mutation.

```mermaid
flowchart LR
    A[Seeded fictional tenant generator] --> G[Graph JSON v0.1]
    X[Synthetic Graph and ARM exports] --> C[Offline Entra/Azure adapter]
    C --> G
    G --> V[Schema and semantic validation]
    V --> E[Actor-scoped reachability engine]
    E --> M[Exact metric arithmetic and tenant statistics]
    M --> W[Exhaustive small-graph binding removals]
    W --> S[Deterministic manifest and external-key HMAC]
    S --> J[Signed result JSON]
    J --> R[Signature verification and report exporters]
    R --> H[Self-contained HTML dashboard]
    R --> O[JSON / Markdown / SARIF]
    A --> Q[Independent whole-edge oracle]
    Q --> T[Hand fixtures and property tests]
    E --> T
    K[Caller-supplied credential provider] -.-> L[Disabled-by-default GET-only transport]
    L -.-> U[Unexecuted live collection contract]
```

## Ownership

| Module | Responsibility |
| --- | --- |
| model.py | Strict draft-2020-12 JSON validation, reference invariants, synthetic boundary, canonical JSON and snapshot hash |
| synthetic.py / oracle.py | Feature-complete seeded generator and classic illustration; separate repeated whole-edge set iteration for small-graph truth |
| engine.py | Priority-queue fixed point over `(node, action, actor)`; actor-local deny subtraction; guarded secret acquisition; zero/one escalation costs |
| analysis.py | Fraction-based arithmetic, absolute reach, weighted/bounded variants, p95/Gini/type summaries, explanations and actual what-if candidates |
| signing.py | OS-random external local HMAC key; content hash and HMAC validation; no key enters result artifacts |
| reports.py / assets/dashboard.html | Verified-source JSON/MD/SARIF/HTML export; all dashboard numbers derive from the signed result |
| connectors/entra_azure.py | Synthetic export envelopes, finite operation mapping, groups, scope/deny exclusions and explicit reviewed app/PIM/CA sidecars |
| connectors/transport.py | Gated GET-only transport, safe origins/paths, pagination limits, timeout/retry/redirect controls; fake-response tested only |
| cli.py | File-oriented workflows, input validation and overwrite protection |

## Core Semantics

The universe is every declared `(resource, action)` pair, including ungranted actions. Permission scenarios preserve it and all weights. Sensitivity weights are exact decimal fractions in [0,1]; an all-zero sensitivity denominator is undefined/null. Canonical and action-weighted denominators remain positive. Absolute reach is always published alongside normalization.

Static membership and already-active assignments cost zero escalation steps. Assumption, explicit secret acquisition and PIM activation cost one. Default constraints block device/approval, permit network/time, and permit eligibility only when no blocking constraint applies. Denies subtract actor-local actions across allow paths before counting; they are not merely nontraversable edges. Different acquired identities keep distinct deny contexts.

Explanatory paths minimize escalation count, hops and stable edge IDs to the highest-sensitivity reachable resource. This is a shortest-escalation witness, not every reachable path. The graph is finite and nonnegative costs plus increasing hop count prevent cycle improvements forever. Independent oracle tests use repeated whole-edge closure rather than the production priority queue.

## Reproducibility and Boundaries

Sort all unordered graph collections before analysis, retain snapshot observation time, and avoid ambient timestamps in results. The same graph, parameters and signing key produce byte-identical signed JSON. HMAC is local integrity protection, not a public-key research attestation; signed artifacts do not prove their input was complete or truthful.

Synthetic reports intentionally contain identifiers and graph topology. They are not anonymized benchmark submissions. General live authorization, encrypted tenant persistence, token/session claims, conjunctive multi-identity permission rules, resource action-catalog completeness and external review remain deferred. Exhaustive recommendation search is bounded explicitly to small demo graphs; benchmark timing excludes that search and any cloud collection.

Both scale targets were measured without replacing schema validation with a shortcut: 10000 principals/2000 resources/32119 edges in 51.63 s; 50000 principals/2000 resources/152119 edges in 215.38 s. These are synthetic workload measurements on recorded hardware, not a claim about arbitrary or live tenants.
