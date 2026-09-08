# Pre-Analysis Registration: NHI Concentration v1

Status: prospective analysis protocol frozen before this session's new population is generated or inspected. This is a local, timestamped research record, not an OSF registration, registered report, or externally witnessed commitment. Previous v0.1 synthetic demo data and its construction are known to the author and are excluded from this test.

## Real-Data Hypothesis

Among participating tenants with at least 20 credential-bearing non-group principals, non-human identities (service_principal, managed_identity, workload_identity, ai_agent) constitute fewer than half of credential-bearing principals, but can reach more than half of the tenant's sensitivity-weighted resource-action universe under the default model. This is a joint, per-tenant hypothesis; counting duplicate credential-pair exposures does not measure a majority of unique sensitive surface.

Primary statistic: fraction of eligible tenants satisfying both NHI principal share <0.5 and weighted union reach of NHI-owned credentials >0.5. Sensitive-surface reach uses the union of unique pairs across NHI credentials, divided by the full declared weighted universe; a pair reached by 50 credentials counts once. The human overlap and total covered-surface fractions are mandatory secondary statistics. All-zero weights, missing principal classifications, incomplete denominators and incompatible action/constraint versions are exclusion reasons, reported with counts.

Primary support criterion: the lower bound of a two-sided 95% Wilson interval for the tenant-level joint-success fraction exceeds 0.5 in a preregistered sample of at least 100 independently contributing eligible tenants. Falsification criterion: its upper bound is below or equal to 0.5. Otherwise the outcome is inconclusive. No optional stopping; analyze once at the preregistered sample/date limit after deduplication by a separately held opt-in contribution credential.

Secondary: NHI versus human per-principal median/p95 radius within each tenant; unique-surface overlap; agent-specific estimates only if at least 30 tenants have at least two classified agents. Weight profiles, eligibility rules, action universe and model version must be fixed before intake. Results are descriptive; selection bias precludes a general enterprise-population inference.

## Privacy Feasibility Correction

Counts/histograms alone cannot reconstruct overlap of reachable sets, so the current structural summary cannot test this primary union hypothesis. A future contributor must compute the joint statistic locally and submit a bounded, privacy-reviewed derived value under a separately versioned schema. It is not silently added to today's field list. The current benchmark can test distributional secondary hypotheses only; the primary real-data test remains pending that review.

## Illustrative Synthetic Sanity Check

Generate 500 new tenants with seed 20260909 and 20-80 credential-bearing principals, 10-30 resources, NHI share drawn from the fixed grid {0.2,0.35,0.5,0.65}, and grant degree drawn from a truncated rank distribution proportional to 1/k^2 for k=1..8. Sample at most one role binding per principal and no systematic type advantage in the null regime. A positive-control regime gives NHIs an explicitly designed broader grant distribution; a reversed control gives humans the broader distribution. The latter two are sensitivity controls, not evidence for the real hypothesis.

These ranges and mixture weights are investigator-designed experimental factors, NOT sourced estimates of real cloud tenants. Heavy-tailed topology is motivated by general graph/attack-graph literature, but no verified empirical identity-type distribution is available from the missing Literature Review Matrix; the claim of sourced real-world parameter distributions is therefore deferred rather than fabricated. The generator and analysis code must publish every parameter and run the unchanged joint criterion; all outputs must say illustrative/synthetic.

The script will record this document's SHA-256 before generating any new population. Changing the protocol afterward requires an amendment with its old/new hashes, reason and disclosure of any inspected data. A local hash is evidence of internal ordering, not independent proof of preregistration time.
