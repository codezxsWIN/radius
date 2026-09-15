# Blast Radius Visual Vocabulary v0.1

Normative candidate annex to Metric Specification v1.0-draft. Original specification text CC-BY-4.0; original implementation Apache-2.0. This annex is a draft visual contract, not a ratified international standard, certification mark or claim of vendor adoption.

## Required Encodings

**VV-01 Area.** A blast disc's AREA MUST be proportional to canonical radius B=absolute reach/universe size. For a declared full-universe reference radius R, the disc radius MUST be R*sqrt(B). B=0 MUST produce zero filled area, not a minimum-size dot that could imply reach. A reference outline and absolute numerator/denominator MUST accompany the disc. Radius length is not itself the metric.

**VV-02 Steps.** Ring k MUST denote minimum escalation cost k, not graph hops, time, severity or likelihood. Resource-action marks MUST be placed according to their first reachable step; a resource with actions first reached at different steps may appear in multiple rings and MUST retain its action labels. Animation MAY reveal one step at a time; timing is presentational and MUST NOT imply real attack duration. Pause, single-step and scrub MUST expose the same data without animation.

**VV-03 Certainty.** Explicitly approximated/assumed transitions MUST be dashed or hatched and described in a visible ledger. Missing certainty evidence MUST be labeled unknown, not converted to zero uncertainty. A share attributed to approximations MUST specify its denominator and method; this instrument uses pairs lost after removing declared assumed ALLOW transitions divided by baseline reachable pairs. Alternative exact routes therefore prevent a pair from being counted as dependent on approximation. A synthetic teaching annotation MUST NOT be represented as an empirical confidence estimate.

**VV-04 Sensitivity.** Sensitivity MUST use the shared, fixed, sequential five-bin scale from ui/tokens.json: [0,.2),[.2,.4),[.4,.6),[.6,.8),[.8,1]. Exact weights MUST remain available in text. Per-view auto-rescaled color ranges are forbidden. Principal types use the separate named categorical palette, with text and icons in addition to color; categorical colors MUST NOT imply a risk ordering.

**VV-05 Stamp.** Every view and exported figure MUST include snapshot hash, engine version, graph schema version, constraint model, metric parameters and snapshot generation time. Visual-vocabulary version, redaction state and illustrative status MUST also appear. The source result's manifest hash MUST be available in the surrounding evidence record. A stamp is provenance, not proof of truth or verification of a private HMAC signature.

## Additional Rules

**VV-06 Populations.** Treemap area MUST encode absolute credential reach, not number of paths. Zero-area credentials MUST remain in the text alternative. A p95 outline means canonical radius at or above the declared population's nearest-rank p95, not the top5% by arbitrary tie breaking. A filtered subset MUST retain or explicitly replace its population definition; it MUST NOT silently change denominators.

**VV-07 Distributions.** Lorenz/Gini displays MUST label summed credential-pair exposure, which can count the same pair across credentials repeatedly. They MUST NOT describe that sum as unique tenant surface. Histograms MUST disclose bin endpoints and any logarithmic transform. Grouped log(1+count) bars are used instead of misleading log-stacked segments.

**VV-08 Counterfactuals.** Before/after marks MUST share scales, resource universe and named metric. Deleting a deny may increase reach; such an increase MUST NOT be styled as an improvement. A single-binding ranking MUST state the number of candidates evaluated and MUST NOT be called a globally optimal change plan. Gini changes alone are not risk-reduction claims.

**VV-09 Accessibility.** Every visual MUST expose a text description and data table. Keyboard and pointer users MUST reach equivalent evidence. Color alone MUST NOT identify principal type, approximation or direction of change. Reduced motion MUST preserve every state. Color-vision simulation and automated audits are evidence, not a substitute for user testing or a blanket WCAG claim.

**VV-10 Reproduction.** The same result, view options, tokens and embedded fonts MUST produce identical SVG bytes. Layouts MUST be deterministic and must not use ambient time or unseeded random placement. Physical export dimensions and any aggregation MUST be disclosed. Different view parameters can legitimately produce different figures but MUST be recoverable from their source/caption record.

## Visual Catalog Compatibility

The engine result v0.1 and its manifest remain unchanged. The UI consumes those results through a separately versioned visual catalog v0.1 that lists local result filenames/digests, fixture/source context and OPTIONAL explicit approximation annotations. This catalog does not redefine engine authorization or add certainty fields to old results. Unknown annotations do not confer authority. File input accepts synthetic result v0.1; local edits are evaluated with the existing JavaScript reference and stamped with that engine identity.

## Free Conformance Claim

Any tool may say it follows Visual Vocabulary v0.1 if it publishes its token version, deterministic examples and completed checklist, including disclosed deviations. There is no fee, certification authority, exclusive mark or endorsement. Claims MUST distinguish automated checks from manual review and unsupported view types.

Checklist: area ratio; fixed denominator; step/hop distinction; fixed sensitivity bins; categorical redundancy; explicit uncertainty ledger; common before/after scales; zero/undefined states; full stamp; text alternatives; keyboard access; reduced-motion equivalence; byte-identical SVG; embedded font/export dimensions; no unsupported historical or empirical claims.
