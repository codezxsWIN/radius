# Hand-Computed Conformance Fixtures

Every small fixture has four declared resource-action pairs: r0/read, r0/write, r1/read, r1/write. Secret-store cases replace the two r0 actions with read_metadata and read_secret, keeping four pairs. The alpha credential is the subject of each calculation below. No expected count is obtained from the production engine.

| Fixture | Reach Derivation | Absolute Reach | Canonical |
| --- | --- | --- | --- |
| direct | Only r0/read is granted; 1 divided by 4. | 1 | 0.25 |
| duplicate | Two grants both reach the same r0/read pair; union still contains one pair. | 1 | 0.25 |
| nested | alpha -> group0 -> group1 -> group2 -> allow -> r0/read; membership adds no escalation. | 1 | 0.25 |
| pim | Eligible binding can activate without approval; r0/read is reachable with one escalation. At k=0 reach is empty. | 1 | 0.25 |
| approval | Eligible binding additionally requires independent approval; the default attacker cannot traverse it. | 0 | 0 |
| device | Device-required binding cuts the only access path. | 0 | 0 |
| network | Default model permits network restriction, so r0/read remains; strict model yields zero. | 1 | 0.25 |
| time | Default model permits time window, so r0/read remains; strict model yields zero. | 1 | 0.25 |
| deny | The actor has both allow and deny for r0/read; subtraction leaves no reachable pairs. | 0 | 0 |
| cycle | alpha reads r0; assuming beta adds r1/write; beta -> alpha repeats known states. | 2 | 0.5 |
| secret | Alpha reads vault metadata and secrets (2); explicit acquisition of beta adds r1/write (1); total 3/4. k=0 is 2/4; k=1 is 3/4. | 3 | 0.75 |
| metadata | Alpha reads vault metadata only; read_secret prerequisite is false, so beta is not obtained. | 1 | 0.25 |
| zero-sensitivity | Same direct reach, but all sensitivity weights are zero; canonical 1/4, sensitivity variant undefined/null. | 1 | 0.25 |

Resource weights are 0.2 for r0 and 0.8 for r1. Sensitivity denominator = 2*0.2 + 2*0.8 = 2. Direct weighted radius = 0.2/2 = 0.1; cycle = (0.2+0.8)/2 = 0.5; secret = (0.2+0.2+0.8)/2 = 0.6. Default read/write action weights 1/3 give denominator 8 and direct radius 1/8. Secret case has metadata/secret/read/write weights 1/1/1/3, denominator 6; reached action weight 1+1+3=5, so 5/6.

The generator's small configurations also run a separate whole-edge set-iteration oracle that does not import the engine. It checks exact pair sets and independently computes weighted values. It is not a formal proof or authoritative platform validation.

## Classic Charter Reconstruction

The classic fixture declares 16000 storage-account resources, each with read/write/administer, for a total of 48000 pairs. Complete triples are granted in resource order; if a count is not divisible by three, the last resource has the remaining prefix of the action triple.

| Fictional Principal | Hand Calculation | Expected Canonical Radius |
| --- | --- | --- |
| Finance analyst | 413 complete triples + 1 read = 1240 pairs; 1240 / 48000 | 0.025833333333333333 |
| CI/CD service | 3200 complete triples = 9600 pairs; 9600 / 48000 | 0.2 |
| Legacy synchronisation | 10400 complete triples = 31200 pairs; 31200 / 48000 | 0.65 |
| Copilot agent | 4800 complete triples = 14400 pairs; 14400 / 48000 | 0.3 |

This reproduces canonical cardinalities, not the charter's absent underlying tenant or illustrative sensitivity profile. Sensitivities cycle through 0.2/0.5/0.8/1.0; actually computed weighted values are recorded in results/classic-benchmark.json. The finance credential is an explicitly assumed already-authorized synthetic token so the example does not incorrectly claim a stolen MFA-gated password alone passes a second factor. General token claims/scope evaluation is deferred.

