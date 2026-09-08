# CircleCI 2023 2FA-backed session theft

Evidence grade: **A: primary organization incident report; additional supported case**. All graphs are fictional and were executed by the reference engine.

## Public Record

CircleCI reported malware theft of a valid 2FA-backed SSO session, impersonation of an engineer and use of the engineer's production-access privileges to exfiltrate a subset of stores containing customer variables, tokens and keys. It subsequently added production step-up controls, making this a supported counterexample to treating all MFA-gated identities as blocked after session theft.

## Explicit Assumptions

1. The completed second factor is represented by an explicit completed device factor on a token authenticator, an abstraction rather than a claim about CircleCI's exact MFA technology.
2. One production-secret-collection/read_secret unit abstracts the disclosed subset; its full storage inventory is unknown.
3. The already-authorized employee production path is collapsed into one binding; real token-minting and session details are not reconstructed.
4. A hypothetical fresh independent approval on production access is not satisfiable by the stolen session; no claim is made that this exact historical control existed.

## Modeled Boundary

Initial malware execution is outside scope. The contrast between default and session-aware models illustrates why the credential starting context must be declared.

## Executed Outcomes

| Model | Absolute / Universe | Canonical | Sensitivity | Action | Bounded | Control Reach |
| --- | --- | --- | --- | --- | --- | --- |
| default | 0/1 | 0 | 0 | 0 | 0 | 0 |
| strict | 0/1 | 0 | 0 | 0 | 0 | 0 |
| session-theft-aware | 1/1 | 1 | 1 | 1 | 1 | 0 |

Control class: `approval_required`. Every control graph is a hypothetical intervention, not proof of historical prevention.

## Ranking Assessment

No reviewed source supplies the full preincident credential population and action universe; rank1/1 in a minimal graph has no decile evidentiary value.

Assumed completions illustrate the issue: adding nine zero-reach credentials makes the target uniquely rank1/10; adding nine equal-reach credentials makes its tie-compatible rank range1-10/10. Neither completion is observed, and neither may be cited as evidence the target was historically in the top decile.

## Sources

- [CircleCI Jan 4, 2023 security incident report](https://circleci.com/blog/jan-4-2023-incident-report/) (2023-01-12; accessed2026-09-09).

See ../../RECONSTRUCTION_METHOD.md for the challenge and exclusion protocol.
