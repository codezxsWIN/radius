# Beacon CRM 2026 AWS key incident

Evidence grade: **A: primary final report, commissioned independent attestation and regulator corroboration**. All graphs are fictional and were executed by the reference engine.

## Public Record

Beacon's September final report preserves the assessment of a probable compromised AWS access key, potentially exposed in public JavaScript build artifacts. Pages5/17 describe a database copy and transfer-volume evidence suggesting a broad download, while retaining uncertainty about exact objects and definitive exfiltration. The commissioned CYFOR attestation on page21 confirms that the credential was disabled July29 and its account subsequently deleted; it expressly does not prove whether the copies ultimately left. The report supplies no complete preincident authorization inventory.

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

Two executed assumed completions add the SAME one unreported resource and nine credentials, holding the completed universe fixed at two pairs. Under session-theft-aware the target remains1/2. Nine zero-reach credentials put it uniquely rank1/10; nine credentials granted both pairs put it uniquely rank10/10. Input/output files for both completions are saved. Neither completion is observed; they demonstrate nonidentifiability rather than historical ranking.

## Sources

- [Cyber-security Incident Update](https://www.beaconcrm.org/incident) (2026-09-03 final update; 2026-08-12 technical assessment retained; accessed2026-09-09).
- [Beacon Cyber Security Incident Final Report - September 2026](https://www.beaconcrm.org/incident-report) (2026-09-03; attestation dated 2026-08-27; accessed2026-09-09).
- [Guidance for charities affected by the Beacon cyber security incident](https://www.gov.uk/government/news/guidance-for-charities-affected-by-the-beacon-cyber-security-incident) (2026-08-07; accessed2026-09-09).

See ../../RECONSTRUCTION_METHOD.md for the challenge and exclusion protocol.
