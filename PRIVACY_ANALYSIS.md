# Structural Summary Privacy Analysis

Status: reproducible synthetic experiment and mathematical mechanism specification, NOT independent privacy certification or permission to collect real data. All500 generated tenants are fictional. No real summary, network intake or public real-data release exists.

## Threat Model and Measured Linkage

An adversary may know an organization's identity mix, rough size and some permission structure, obtain repeated releases, or correlate external disclosures. Removing names does not remove a structural fingerprint. We evaluated exact37-dimensional count/histogram vectors, counts rounded down in units of10, and the proposed21-cell aggregate projection. Nearest-neighbor distance is Euclidean distance divided by sqrt(dimensions), after each column is divided by its observed synthetic maximum (at least1). This normalization is a diagnostic, not a privacy transformation.

| Representation | Distinct profiles | Unique rows /500 | Rows in equivalence classes below10 | Median nearest-neighbor distance |
| --- | --- | --- | --- | --- |
| Exact allowlisted summary | 500 | 500 (100%) | 500 | 0.01998085 |
| All counts rounded down by10 | 282 | 161 (32.2%) | 490 | 0 |
| Minimal aggregate cell | 6 | 0 (0%) | 16 | 0 |

For exact summaries the minimum nearest-neighbor distance was0.00302575 and p95 was0.04365306. These are actual computed values in research/privacy-results.json. A unique synthetic profile is vulnerable to exact matching when all attributes are known; it is not a measured probability of identifying a real company. Conversely, zero uniqueness is not anonymity: homogeneity, attribute disclosure, auxiliary information and differencing can still expose contributors. Two populated projected cells had only7 and9 tenants.

**Decision:** exact/raw structural summaries are not a public dataset format. Rounded raw summaries are also rejected. Public outputs must be population-level aggregates under a reviewed release policy; only this fully synthetic test corpus is openly distributable row by row.

## Bounded Aggregate Mechanism

The release has21 predeclared cells: NHI-minority/not-minority crossed with ten tenant canonical-p95 buckets, plus an empty-population cell. A deduplicated tenant contributes one1 and twenty0s, regardless of its numbers of principals, credentials or resources. Adjacent datasets differ by addition/removal of one tenant, giving L1 sensitivity1. Replacing a tenant is TWO such changes and consumes twice this epsilon. Identity classification and p95 bucketing are computed locally under the fixed profile. A real collector must reject incompatible profiles and enforce one accepted row per tenant before aggregation.

For q=1/2 sample independent geometric random variables X,Y on nonnegative integers, each with probability `(1-q)*q^n`, and add Z=X-Y to every cell count. The integer implementation uses exact rational Bernoulli trials with uniformly sampled integer draws; it does not approximate inverse-CDF noise with floating point. Then:

$$P[Z=z]=\frac{1-q}{1+q}q^{|z|}.$$

For vectors h,h' differing in L1 norm at most1, the ratio of probabilities of any output is at most `q^-1=2`, by the triangle inequality for absolute distances. Independent vector noise therefore satisfies pure tenant-level epsilon-DP for epsilon=`ln(2)=0.69314718056`, delta=0, assuming correct independent random bits and enforcement of the stated adjacency. This is a proof for the mechanism, not an audit of this software's operating environment or intake identity system.

The budget was chosen before observing utility: a single release bounds the membership likelihood ratio by2. This is not universally "safe"; a sensitive rare tenant or strong prior knowledge may still suffer disclosure. The design compares epsilon ln(4/3) and ln4, but does not select the most flattering result after inspection. Repeated releases compose; the default annual cohort budget proposal is ln2 TOTAL, not ln2 per query. No fine-grained query interface is proposed.

## Support Target and Suppression

Target k=10 is a policy floor motivated by avoiding reporting very small cohorts, not a guarantee of k-anonymity. Checking actual count>=10 and releasing a suppression bit would itself leak information. Instead clip noisy counts to nonnegative integers and release only cells with noisy count>=20; all other cells are null in the SAME fixed21-cell schema. This is postprocessing of the DP vector, as is clipping.

For a true count below10, the worst case is9. With q=1/2 the chance of passing threshold20 is at most `q^11/(1+q)`. A union bound across21 cells is `7/1024=0.0068359375`, below the prespecified1% family target. This is a bound on accidental small-cell publication, NOT the delta in the DP guarantee. Some genuinely large cells will also be suppressed; no observed-support correction is published. An empty dataset is allowed and can theoretically produce a spurious released cell, a normal limitation of noisy-count mechanisms.

## Observed Utility

Each row below summarizes200 seeded synthetic releases of the SAME500-tenant null population. All21 fixed cells are included in MAE, and a suppressed cell is treated as0, so suppression error is counted rather than omitted.

| Epsilon | q | Noisy threshold | Mean count MAE | p95 count MAE | True support retained | Maximum absolute cell error |
| --- | --- | --- | --- | --- | --- | --- |
| 0.287682 | 3/4 | 34 | 1.410714 | 1.952381 | 96.8% | 23 |
| 0.693147 | 1/2 | 20 | 1.014762 | 1.285714 | 96.8% | 12 |
| 1.386294 | 1/4 | 15 | 0.862857 | 1.000000 | 96.8% | 9 |

At the selected budget, mean total absolute histogram error is21*1.014762=21.31 counts, about4.26% of the experimental population. Four large cells remain useful for this coarse summary, but the two rare tail cells lose all16 underlying contributions to suppression in these trials. The large number of empty cells makes the all-cell MAE small; it MUST NOT be mistaken for fine-tail accuracy or preservation of full credential-radius distributions. More granular cross-platform comparisons need a new prespecified utility/privacy study.

## Inspectability and Release Controls

- `src/blastradius/summary.py` defines the closed payload and exact binning; `tests/test_summary.py` verifies exact CLI stdout and no network call.
- `src/blastradius/aggregation.py` defines fixed cells, contribution mapping, rational noise, support threshold and an in-memory budget ledger. Tests cover schema rejection, sensitivity1, deterministic test streams, noise symmetry, bounds and repeated-budget rejection.
- `src/blastradius/research.py` performs uniqueness, nearest-neighbor and utility measurements. `tools/run_research.py` saves protocol hashes BEFORE generating data and all artifact hashes after execution.
- `research/noisy-aggregate.json` is an illustrative seeded release. Publishing its seed is acceptable only because every input is fictional. A known seed cancels the noise and offers NO protection for real inputs.

Production would require a durable, transactionally enforced budget ledger, cached immutable release outputs, independent deduplication and consent handling, secure random generation, access controls for raw summaries, retention/deletion policy and independent review. The in-memory ledger is an inspectable example, not a multi-process service. A user could label real inputs synthetic; software flags cannot replace research governance. No production deployment or cryptographic RNG audit was performed.

## Residual Risks and Gates

DP protects participation, not every fact about an organization inferable from a population. It does not cure selection bias, malicious submissions, wrong classification, collusion, correlated subsidiaries, repeated publication under new project names or weak custody of raw summaries. A tenant privacy unit may not protect each individual within it when the contributor's consent and lawful authority are absent. Neutral institutional custody, ethics/legal review, independent privacy review and an externally reviewable release ledger are hard gates before the FIRST real aggregate.

Background: Cynthia Dwork and Aaron Roth, [The Algorithmic Foundations of Differential Privacy](https://www.cis.upenn.edu/~aaroth/privacybook.html), provides the formal DP, sensitivity, postprocessing and composition framework. No claim is made that its authors reviewed this project. No custom cryptographic primitive is introduced.
