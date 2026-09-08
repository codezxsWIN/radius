# Beacon CRM 2026 AWS key incident

Evidence grade: **A: primary organization assessment plus regulator corroboration**. All graphs are fictional and were executed by the reference engine.

## Public Record

Beacon's retained August 12 assessment describes a probable compromised AWS access key, potentially exposed in public JavaScript build artifacts. The organization assessed that its customer database and attachment data were copied and likely downloaded readably, but explicitly said exact objects, destination and definitive object attribution could not be determined from available logs.

## Explicit Assumptions

1. One fictional backup-collection/read unit represents the assessed exposed collection; it is not 1000 independently enumerated databases.
2. The key is assumed to authorize that abstract read. Actual IAM role, bucket policy, KMS permissions and account inventory are unavailable.
3. Sensitivity=1 is an investigator choice; no claim is made about records, subjects or bytes.
4. Revocation removes this key's authentication transition; rotation latency and alternate persistence are not modeled.

## Modeled Boundary

Authorization-level backup access is modeled after acquisition of the key; the probable JavaScript exposure mechanism is not independently reenacted.

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

- [Cyber-security Incident Update](https://www.beaconcrm.org/incident) (2026-09-03 final update; 2026-08-12 technical assessment retained; accessed2026-09-09).
- [Guidance for charities affected by the Beacon cyber security incident](https://www.gov.uk/government/news/guidance-for-charities-affected-by-the-beacon-cyber-security-incident) (2026-08-07; accessed2026-09-09).

See ../../RECONSTRUCTION_METHOD.md for the challenge and exclusion protocol.
