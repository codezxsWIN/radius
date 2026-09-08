# Blast Radius Metric Specification v1.0-draft

Status: candidate community specification, NOT an approved international standard. Date: 2026-09-09. Authors: Blast Radius contributors; coordinating editor Amit Damle. Licence: Creative Commons Attribution 4.0 International (CC BY 4.0). DOI: **NOT ASSIGNED; deposit placeholder, not a resolvable identifier**.

Suggested citation: Blast Radius contributors. *Blast Radius Metric Specification v1.0-draft*. 2026. Version and content hash MUST accompany a citation until a DOI is assigned. This draft builds on the inspected reference implementation; the requested v0.2 specification was not available, so no rule below falsely claims to reproduce an unseen ruling.

## 1. Conventions and Scope

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT and MAY express the normative requirement levels of BCP 14 (RFC 2119 and RFC 8174) when capitalized. Requirement identifiers BR-R01 through BR-R32 are permanent within this draft series. Conformance fixtures BR-001 through BR-040 and the requirement matrix are distributed with this document.

Blast Radius specifies authorization reach, not probability of compromise, expected financial loss, incident severity, vulnerability exploitability, or compliance. The artifacts are free specification/schema, free conformance tests/reference code, and eventually open aggregate data. No paid certificate, certification mark, proprietary test or tool-management service is part of this standard.

**BR-R01.** An implementation MUST identify the specification/profile version, graph-schema version, action inventory, sensitivity/weight profile, constraint model and its parameters. It MUST reject an unsupported required semantic extension rather than silently produce a conformant score. Fixtures BR-001, BR-033.

**BR-R02.** The core profile MUST accept only structurally valid input and resolve all node, edge, owner and constraint references. Duplicate identities and dangling references MUST be rejected. Credential nodes MUST contain metadata, never credential values. Fixtures BR-034, BR-037, BR-038.

The wire graph remains schema v0.1 with an additive `session_satisfied_constraints` credential field. The metric and conformance profile are independently versioned `1.0-draft`. This avoids relabeling an incompatible change as the same standard while preserving existing synthetic fixtures.

## 2. Graph and Resource Universe

Let $G=(N,E)$ be a finite directed labelled multigraph. Nodes are partitioned into principals $P$, credentials $C$, bindings $B$, resources $R$ and constraints $K$. Groups are a non-authenticating principal subtype. Provenance consists of connector, source API identifier, observation time and evidence reference; it is evidence metadata, never a traversable authorization edge.

**BR-R03.** Each resource MUST declare a finite set of supported action classes, including currently ungranted actions. The universe is $U=\{(r,a):r\in R,a\in A_r\}$. The denominator MUST NOT be derived from observed grants or reachable paths. BR-016.

**BR-R04.** A resource-action pair MUST be counted once regardless of how many paths or identities reach it. BR-002.

**BR-R05.** The empty universe MUST produce an explicit invalid/undefined result, not a radius of zero. An empty credential population over a nonempty universe is valid and has null population statistics. BR-031, BR-036.

**BR-R06.** Resource granularity MUST be declared before collection and held constant in comparisons. Potentially unbounded resources, such as objects in a storage service, MUST use a declared finite abstraction (for example an account/bucket action set) rather than assume complete object enumeration. Canonical scores with incompatible coverage/granularity MUST NOT be compared as tenant-wide risk estimates. BR-016, BR-032. Core fixtures use explicitly declared synthetic object units; provider-specific granularity is an extension-review responsibility.

## 3. Authorization Semantics

**BR-R07.** `authenticates_as` traverses from a credential to its declared non-group owner, subject to that authenticator's constraints. Metadata owner association alone MUST NOT bypass a blocked authentication edge. BR-006, BR-024.

**BR-R08.** `member_of` traverses toward a group and preserves the acting principal. Nested groups MUST be evaluated transitively, and membership cycles MUST terminate. BR-003, BR-010.

**BR-R09.** `assigned` links a principal/group to a binding; `grants` links a binding to a resource with a finite action subset of that resource's inventory. Ordinary active bindings and membership have zero escalation cost. BR-001, BR-015, BR-022.

**BR-R10.** Denies MUST be subtracted from the current actor's applicable capabilities across ALL allow paths, not skipped as if an alternate allow could override them. Resolved denies and their applicability MUST remain fixed when testing permission-only monotonicity. Denies MUST already be effective; conditions that would alter their applicability MUST be resolved by the normalizer, not evaluated as attacker capabilities. BR-009, BR-029.

**BR-R11.** Actor-restricted edges MUST apply only in their declared actor context. Group traversal MUST NOT merge unrelated actors' permissions. Assumption/acquisition changes identity context explicitly; a deny for the original actor does not automatically apply to an acquired identity. BR-010, BR-028.

**BR-R12.** `can_read_secret` MUST name both a specific obtainable credential and an actor-local `read_secret` prerequisite on an explicitly represented secret store. Metadata read alone MUST NOT satisfy this prerequisite. Any source-group membership that authorizes acquisition MUST itself be accessible under the model. BR-011, BR-012.

**BR-R13.** `can_assume` and `can_read_secret` each add one escalation step. The normalizer MUST justify assumption/acquisition rather than infer it from a role name. Resource containment, provenance, `constrained_by`, API naming and network adjacency MUST NOT independently grant reach. BR-010, BR-011, BR-032.

**BR-R14.** PIM eligibility denotes a potentially activatable binding; activation costs one escalation step. It MUST remain blocked by applicable approval/device requirements. An active assignment has zero activation cost even if another eligible assignment exists. Missing activation-policy context MUST be reported or rejected, not assumed approval-free. BR-004, BR-005, BR-019, BR-022.

## 4. Constraint-Model Registry

Model registrations include ID, version, attacker assumptions, predicate and incompatible comparisons. They are maintained by this project, not by IANA. The legacy `permissive` diagnostic model MAY remain available, but is not required for the v1.0-draft core claim.

| Model ID | Normative Rule | Interpretation |
| --- | --- | --- |
| default / 1 | Device and independent approval block; network/time do not; eligible activation is allowed unless otherwise blocked. | One compromised credential, no independently possessed device or second person's approval. |
| strict / 1 | Default blocks plus network/time restrictions block. | Lower reach bound under stronger explicitly assumed constraints, not measured attacker impossibility. |
| session-theft-aware / 1 | Default rules, except an authenticator for an issued token MAY reuse the specifically declared completed device factor. | Distinguishes an already authenticated stolen session from a fresh password; never waives new approval/access constraints. |

**BR-R15.** Default device/approval restrictions MUST cut their constrained transition. BR-005, BR-006.

**BR-R16.** Default network/time restrictions MUST remain satisfiable; strict MUST block them. BR-007, BR-008, BR-032.

**BR-R17.** The session model MUST require `subtype=token` and an explicit `session_satisfied_constraints` declaration to reuse a completed authentication device factor. The only registered reusable factor in this profile is `device_required`. A token label without the declaration is insufficient. BR-024, BR-025.

**BR-R18.** A reused session factor MUST apply only to its `authenticates_as` transition. It MUST NOT bypass a resource/binding gate or independent approval, and a password MUST NOT claim it. BR-026, BR-027, BR-038.

All declared constraints on an edge/binding are conjunctive. General token audience, replay binding, revocation/expiry, delegated session context, alternative/OR policy controls and authentication strengths require separate semantic extensions. A larger session-aware radius is a different attacker starting condition, not a violation of stronger-constraint monotonicity.

## 5. Fixed Point and Metric Family

The effective state is $(v,a,p)$: current node, action (empty off resource states), and acting principal. The model plus pre-resolved authorization defines a unary transition relation $T$. In particular, a secret-acquisition transition starts from its required `(secret_store,read_secret,actor)` state, with a fixed predicate checking that the edge's source belongs to the actor's constraint-qualified group closure. It does not combine a prerequisite reached by another actor or credential. Starting from credential $c$, $S_c^*=\mu S.(\{s_c\}\cup T(S))$. Reach is the projection of resource states onto unique pairs: $Q_c=\{(r,a)\in U:(r,a,p)\in S_c^*\}$.

**BR-R19.** Implementations MUST compute the least fixed point, including cycles and mutual escalation, rather than impose an undocumented hop cutoff. BR-010, BR-020.

**BR-R20.** Canonical radius is $|Q_c|/|U|$. Every published normalized value MUST be accompanied by absolute reach $|Q_c|$, universe size $|U|$, model and coverage. A normalized value alone is nonconformant publication. BR-001, BR-016.

**BR-R21.** Sensitivity radius is $\sum_{(r,a)\in Q_c}s_r / \sum_{(r,a)\in U}s_r$, with finite $s_r\in[0,1]$. Zero total sensitivity MUST produce null/undefined, not zero. Missing classifications MUST be distinguished from explicit zero weight. BR-013, BR-017, BR-035.

**BR-R22.** Action radius uses the same universe, weighting each pair by the declared positive action weight. Defaults are read=1, write=3, administer=5, metadata-read=1 and secret-read=1. A different profile MAY be used only when supplied and reported explicitly. BR-018.

**BR-R23.** For nonnegative integer $k$, step-bounded radius counts pairs reachable with total escalation cost <=k, divided by the SAME full universe. Ordinary graph hops MUST NOT be substituted for escalation count. Unbounded and bounded values MUST be separate. BR-019, BR-020, BR-021, BR-022.

**BR-R24.** Arithmetic comparisons and canonical conformance output MUST retain exact rational values. Decimal JSON weights are interpreted as their exact decimal fractions; a conformance ratio is serialized as a reduced fraction string, including integers `0` and `1`. Presentation decimals MAY be rounded but MUST NOT control rankings. BR-017, BR-018.

**BR-R25.** Tenant maximum and nearest-rank p95 MUST use the declared credential population. For sorted $x_1..x_n$, p95=$x_{\lceil0.95n\rceil}$; Gini=$\sum_i(2i-n-1)x_i/(n\sum_i x_i)$, with zero for an all-zero nonempty population. Share above threshold uses strict >, default 1/4. Empty population statistics MUST be null. BR-023, BR-031.

**BR-R26.** An explanatory witness MUST name the highest-sensitivity reachable resource; ties minimize escalation steps, graph hops, lexicographic edge-ID sequence, then pair ID. Its provenance MUST identify the transitions used. Absence of a reachable pair MUST produce no invented witness. BR-001, BR-010, BR-014.

**BR-R27.** Canonical graph bytes sort object keys, node/edge IDs and unordered action/constraint lists; observation time belongs to the input. Analysis MUST NOT insert ambient time, random IDs or probabilistic scores into deterministic output. SHA-256 input hash MUST be identical under permitted input-order permutations. The contract manifest hash is over canonical result bytes excluding the hash field itself. BR-030.

HMAC/Ed25519 signatures MAY envelope a result separately; signatures attest a signing key's possession, not the truth/completeness of source data. Core conformance MUST NOT depend on a reference implementation's private key.

## 6. Numbered Theorems and Revised Claims

### Theorem 1: Normalization and Bounds

For finite nonempty $U$ and nonnegative weights with positive total, $0\le B(c)\le1$ for canonical and each weighted variant. Proof: $Q_c\subseteq U$; summing nonnegative terms over a subset lies between zero and the sum over $U$. The zero-total sensitivity case is undefined by BR-R21 and is not covered by the ratio theorem.

### Theorem 2: Effective-Allow Monotonicity

With fixed states, $U$, weights, credential population, resolved denies and constraint predicates, adding effective allow transitions cannot decrease any individual radius; removing them cannot increase one. Proof: transition inclusion gives $T\subseteq T'$. Induction on closure iteration gives $S_n\subseteq S'_n$ for every n, hence least-fixed-point and reach inclusion; nonnegative weighted sums preserve the order.

Counterexample to the unqualified claim: adding membership in a deny-bearing group may remove an already allowed action; deleting a deny may increase reach. Revised claim excludes changes to resolved deny applicability, universe, weights, identity context or model. Max/p95 inherit the order for a fixed population; Gini does NOT: changing radii (1,1) to (0,1) decreases individual reach but increases Gini from 0 to 1/2.

### Theorem 3: Independent-Source Composability

For fixed unary transition relation T, closure from two initial states equals the union of their separate closures, so principal independent-credential reach is $Q_{c_1}\cup Q_{c_2}$. Proof: every state in a multi-source traversal has a path beginning at one source; conversely each single-source path is available in the multi-source traversal. Therefore max of the separate radii <= union radius <= min(1,sum of radii).

Counterexample to unrestricted collaboration: capability X requires both a role from credential A and a distinct approval capability from credential B; neither independent reach contains X but collaboration does. Revised claim is independent use under unary transitions, NOT a bound for conjunctive multi-credential authorization. BR-R28: implementations MUST label this scope and MUST reject unsupported conjunctive rules rather than silently reduce them to OR. BR-023, BR-028.

### Theorem 4: Constraint Sensitivity

If model M2 permits a subset of M1's transitions while initial credential capabilities and resolved denies are fixed, reach under M2 is a subset of reach under M1. Proof: apply the closure-inclusion induction of Theorem 2. An expired/revoked session or a newly satisfied factor changes the initial context and is outside this comparison. BR-005 through BR-008, BR-024 through BR-027.

### Theorem 5: Bounded-Reach Ordering

For k<=l, $Q_{c,\le k}\subseteq Q_{c,\le l}\subseteq Q_c$. Proof: any path with cost at most k also has cost at most l, and any bounded path is an unbounded path. Nonnegative costs are required. BR-019 through BR-022.

### Theorem 6: Termination

The finite graph induces finitely many `(node,action,actor)` states. Set-closure iteration only adds states, so it terminates after at most that many strict additions. A priority-queue implementation using nonnegative escalation cost and increasing hop count cannot improve a state's optimal label infinitely; cycles cannot create a better repeated label. Witness tie-breaks MUST be total and deterministic. BR-010, BR-020.

### Theorem 7: Platform Invariance

A label-preserving isomorphism of effective state graphs and pair inventories, preserving weights and model predicates, preserves all per-credential metric values. Proof: the isomorphism maps paths bijectively and preserves their costs and weighted pair sums. This is NOT proof that real Azure/AWS/Kubernetes collectors are semantically equivalent: that is a separate normalization-conformance claim. Provenance/platform names alone MUST NOT affect arithmetic. BR-R29; BR-030.

### Theorem 8: Determinism

Fixed normalized snapshot, parameters, exact arithmetic and total witness ordering produce identical results and manifest hashes. Proof: closure is unique, each selected witness is a unique minimum under the total order, metric/statistic functions are pure, and the specified serialization is deterministic. A signature from a different key is not required to match. BR-R27, BR-030.

These are mathematical arguments over the stated model. Finite conformance tests do not prove the normalizer complete, observations truthful, authorization predicates correct, privacy sound or hypotheses true. No external review or mechanized proof is claimed.

## 7. Registries and Extensions

**BR-R30.** Principal registry values are human_user, service_principal, managed_identity, workload_identity, ai_agent and group. The last is non-authenticating. Action registry values are read, write, administer, read_metadata and read_secret. Constraint registry values are device_required, approval_required, network_restriction, time_window and pim_eligible. Unknown required values MUST fail the core profile. BR-033, BR-039, BR-040. The machine registry is registries.json.

Registrations require a unique lowercase identifier, semantic definition, owner-neutral contact, action/resource granularity, required evidence, conflict/precedence rules, tests, version, and public rationale. New platform normalizers MAY emit the existing core vocabulary without changing scores merely because provenance names a new platform. An extension requiring new states/actions/constraints MUST declare a separately versioned profile and capability negotiation contract; a core-only implementation MUST reject it. Experimental names use `x-<proposer>-<name>` and MUST NOT claim core conformance for affected results.

**BR-R31.** A conformance claim MUST name the exact suite digest, profile version, tool version and published report. It MUST pass every required fixture/model case with no skipped failures and MUST NOT imply trademark certification or a fee-based approval. Fixtures BR-001 through BR-040; report-schema tests also enforce runner behavior.

**BR-R32.** Normative changes require an issue, impact/counterexample analysis, new/updated stable tests, at least 30 days of public comment, a recorded unconflicted steering vote, and a new semantic version or draft revision. Existing fixture IDs MUST NOT be reused for different semantics; amended expectations require a revision and archived prior digest. Editorial corrections preserve meaning and are recorded. Unknown/incomplete v0.2 history MUST remain an explicit gap, not backfilled fictional authority.

## 8. Licensing, Neutrality and Non-Goals

This specification and its schema/registries are [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reference code and the runner are Apache-2.0. Aggregate datasets are CC0 only after publication gates and licensing review. No actual real-world submission is included in the current synthetic artifact.

No vendor-specific exception may alter the metric. Governance is defined in GOVERNANCE.md and requires a neutral institutional home before the first real-data aggregate. SIEM/ticketing connectors, SSO, multi-tenant consoles, compliance packs and executive dashboards beyond the single demo are permanently out of scope.
