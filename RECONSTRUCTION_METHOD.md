# Public-Incident Reconstruction Protocol v1

This study is an auditable model-boundary exercise, not reconstruction of a real tenant graph. Its empirical inputs are publicly reported incident facts; its graph topology and unreported authorization details are explicitly synthetic assumptions. No tenant is contacted, no exploit is executed and no credential value is stored.

## Inclusion and Evidence Grades

1. Prefer an affected organization, incident-response investigator or official vulnerability record. Cite exact URLs, title, publication/update date when available and access date. Separate a source's assessment from a confirmed observation.
2. Grade A means an accessible primary incident account supports the stated credential-use segment; Grade B means a vulnerability capability or secondary report supports a scenario, not a complete named incident. Grade U means the asserted incident cannot be verified and MUST NOT enter incident-level conclusions.
3. Every requested case receives a dossier even if downgraded. Additional cases may be included only with independently verified public support and a stated reason. CircleCI 2023 is added because its first-party account documents a stolen 2FA-backed session and production-secret access; MLflow remains a vulnerability/post-acquisition scenario rather than being mislabeled a named victim incident.
4. Preserve contradictions and later updates. A 2026 CVE record can establish a vulnerability and known exploitation without identifying a victim, attached IAM permissions or exfiltrated cloud credentials. The MLflow advisory's original proof describes a local simulated secret service; it is not proof of a real AWS credential theft.

## Construction

Create the smallest graph for the supported credential-use segment, with obviously fictional names. In the main model, one granted resource/action unit represents a reported category (for example a database export collection); it is not the real count of tables, tenants, workers or files. Sensitivity=1 and action-class mapping are assumptions. A reported number of potentially exposed organizations is never used as a count of confirmed compromised principals or graph resources.

Modeling begins AFTER the credential acquisition assumed by the threat model. Software vulnerabilities, endpoint compromise, SSRF and arbitrary code execution are not authorization edges unless a separately defined extension explicitly models them. For Hugging Face the leaked-token write capability is in scope, while the reported zero-day path to worker compromise is outside the core. For MLflow, the initial unauthenticated SSRF is outside the core and no known attached cloud role is inferred.

For each case, save input.json, engine-output.json for all three named models, control-input.json and control-output.json for a specified hypothetical control, plus narrative.md and evidence.json. Every edge is tagged as a modeling assumption or supported abstract capability. Run the exact core conformance adapter in-process; no private signing key is required for a public reconstruction artifact. The deterministic output hash binds the actual modeled input and parameters.

## Ranking Protocol and Falsification

Top decile requires a defined population and preincident permissions. None of these public sources supplies the full credential population and inventory, so the primary result is **not identifiable**, not "yes" because a one-credential toy graph trivially ranks first. A one-credential graph is deliberately insufficient for a decile claim.

An identifiability stress test constructs and EXECUTES two explicitly assumed completions: both add the same one unreported resource and nine credentials, but those background credentials have zero reach in one completion and full two-pair reach in the other. The target retains1/2 reach under session-theft-aware in both, but changes from uniquely first to uniquely tenth out of ten. Thus the completed universe remains fixed while rank changes without contradicting the reported path. Graphs and exact outputs are saved; these are countermodels demonstrating missing information, not estimates of actual background populations or undocumented incident facts.

The study is falsified as a metric explanation if a supported authorization-only path cannot be represented without adding an unjustified capability, if an asserted control does not change the modeled reachable set as claimed, or if a source contradicts a modeled fact. Refusing to model an out-of-scope exploit is a boundary finding, not an engine accuracy failure. No hypothesis that radius predicts incident impact is tested without preincident denominators and a comparison sample.

## Control Interpretation

Controls are hypothetical classes, not claims that a specific product configuration would have prevented the historical event. Credential revocation removes its authentication transition; fresh device/approval gates are modeled only at the stage where required; least privilege removes the relevant grant. A default model that assumes network location is satisfiable cannot be used to claim network allowlisting necessarily cuts a path. A completed MFA claim on a stolen session does not satisfy a new production step-up control.

## Reviewer Challenge Procedure

A reviewer can challenge a case by citing conflicting public evidence, changing a labeled assumption, proposing a different finite resource unit, providing a supported comparison population, or supplying a graph/control variant. Re-run `python tools/build_reconstructions.py` and compare exact pair sets, absolute reach, ratios and manifest hashes. Source statements, assumption tables and selection/exclusion decisions are versioned; the maintainer must preserve counterexamples rather than remove inconvenient cases.

## Claims

The study can demonstrate that specified credential-use mechanisms are expressible under an explicit authorization model and that modeled controls change the computed reach. It can expose where public narratives require vulnerability/session extensions or leave the comparison population unidentified.

It cannot recover actual tenant-wide blast radii, verify undisclosed IAM policies, infer that all notified organizations were compromised, or establish preincident top-decile prediction. Minimal synthetic ratios are conditional on an investigator-chosen resource universe and are not historical breach-impact estimates.
