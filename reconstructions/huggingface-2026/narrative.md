# Hugging Face 2026 publicly exposed credential pivot

Evidence grade: **A: primary incident account; credential-use segment only**. All graphs are fictional and were executed by the reference engine.

## Public Record

OpenAI's August 26 account reports recovery and sharing of publicly exposed write-capable Hugging Face credentials on July 10, followed by several software exploits and production-worker credential compromise. This minimal graph includes only a representative leaked token's declared write authority; it does not convert zero-days into legitimate privilege-escalation grants.

## Explicit Assumptions

1. One representative fictional write token and one hosted-project/write operation abstract the disclosed credential category.
2. The report's 14 recovered credentials do not establish a complete credential population, resource inventory or uniform scope; they are not a ranking denominator.
3. Sensitivity=1 and exact target scope are assumptions.
4. Revocation of this representative token cuts its modeled write path; it is not claimed to prevent every later exploit or every agent's access.

## Modeled Boundary

The reported zero-day chain, arbitrary code execution and multi-agent collaboration exceed the single-credential authorization-only model. That is an explicit limit of the metric, not evidence that it predicted all impact.

## Executed Outcomes

| Model | Absolute / Universe | Canonical | Sensitivity | Action | Bounded | Control Reach |
| --- | --- | --- | --- | --- | --- | --- |
| default | 1/1 | 1 | 1 | 1 | 1 | 0 |
| strict | 1/1 | 1 | 1 | 1 | 1 | 0 |
| session-theft-aware | 1/1 | 1 | 1 | 1 | 1 | 0 |

Control class: `revoke`. Every control graph is a hypothetical intervention, not proof of historical prevention.

## Ranking Assessment

No reviewed source supplies the full preincident credential population and action universe; rank1/1 in a minimal graph has no decile evidentiary value.

Assumed completions illustrate the issue: adding nine zero-reach credentials makes the target uniquely rank1/10; adding nine equal-reach credentials makes its tie-compatible rank range1-10/10. Neither completion is observed, and neither may be cited as evidence the target was historically in the top decile.

## Sources

- [The Hugging Face incident and the road ahead](https://openai.com/index/hugging-face-incident-and-the-road-ahead/) (2026-08-26; accessed2026-09-09).

See ../../RECONSTRUCTION_METHOD.md for the challenge and exclusion protocol.
