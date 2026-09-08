# Snowflake 2024 customer-account campaign

Evidence grade: **A: primary incident-response account**. All graphs are fictional and were executed by the reference engine.

## Public Record

Mandiant traced the incidents it investigated to compromised customer credentials, often from historical infostealer infections, and reported that the impacted accounts lacked MFA. The approximately 165 organizations were notified as potentially exposed; that number is not treated here as a confirmed compromise count or graph denominator.

## Explicit Assumptions

1. A single fictional customer account is the starting credential, not a representation of every notified organization.
2. One database-export resource/read operation abstracts the supported table access; real table/action inventory is unknown.
3. Sensitivity=1 and absence of other principals in the minimal graph are assumptions, not observed tenant properties.
4. A hypothetical independently possessed authentication device is assumed unavailable to the attacker; generic MFA presence alone is not equated with this guarantee.

## Modeled Boundary

The infostealer compromise precedes the model; platform vulnerabilities are not required for the modeled credential-use segment.

## Executed Outcomes

| Model | Absolute / Universe | Canonical | Sensitivity | Action | Bounded | Control Reach |
| --- | --- | --- | --- | --- | --- | --- |
| default | 1/1 | 1 | 1 | 1 | 1 | 0 |
| strict | 1/1 | 1 | 1 | 1 | 1 | 0 |
| session-theft-aware | 1/1 | 1 | 1 | 1 | 1 | 0 |

Control class: `device_required`. Every control graph is a hypothetical intervention, not proof of historical prevention.

## Ranking Assessment

No reviewed source supplies the full preincident credential population and action universe; rank1/1 in a minimal graph has no decile evidentiary value.

Two executed assumed completions add the SAME one unreported resource and nine credentials, holding the completed universe fixed at two pairs. Under session-theft-aware the target remains1/2. Nine zero-reach credentials put it uniquely rank1/10; nine credentials granted both pairs put it uniquely rank10/10. Input/output files for both completions are saved. Neither completion is observed; they demonstrate nonidentifiability rather than historical ranking.

## Sources

- [UNC5537 Targets Snowflake Customer Instances for Data Theft and Extortion](https://cloud.google.com/blog/topics/threat-intelligence/unc5537-snowflake-data-theft-extortion) (2024-06-10; accessed2026-09-09).

See ../../RECONSTRUCTION_METHOD.md for the challenge and exclusion protocol.
