# Blast Radius Governance Charter v1.0-draft

Status: proposed public governance, not a claim that a steering group has been elected or an institution has accepted the project. This charter governs a free metric standard, conformance suite/reference implementations and planned aggregate dataset. It does not establish a product, certification business or commercial service.

## Five-Seat Steering Group

| Seat | Expertise and constituency | Current status |
| --- | --- | --- |
| 1 | Independent academic: formal methods or security measurement | Vacant; no person nominated without consent |
| 2 | Independent privacy/data-governance researcher | Vacant |
| 3 | Deploying practitioner from an end-user organization | Vacant |
| 4 | Open-source security-tool maintainer | Vacant |
| 5 | Cloud/identity platform practitioner | Founder Amit Damle proposed, not yet elected; Microsoft affiliation counted |

At most ONE seat may be held by people affiliated with the same vendor, including the founder's employer. Parent companies, controlled subsidiaries and materially dependent consulting arrangements count together; dual affiliations count against every relevant vendor cap. Changing employer requires immediate disclosure and, if necessary, resignation or recusal while a replacement election occurs. A nominally independent seat cannot be filled by a vendor's directed representative.

Terms are12 months, at most two consecutive terms. The proposed initial group must be publicly nominated for30 days and ratified with the neutral host's independent participation. Subsequent elections are by documented active contributors: at least three substantive reviewed contributions in the previous six months; no sponsor purchases votes and multiple accounts do not create votes. Election eligibility disputes are resolved by unconflicted members and an independent host observer. These are intended rules, not fabricated current election results.

## Decisions, Quorum and Conflicts

Routine technical decisions require at least three unconflicted members present and a majority of votes cast. Normative metric or privacy-release changes require at least three affirmative unconflicted votes, after the public review period. An abstention is not an affirmative vote. No chair/founder casting vote exists. If fewer than three unconflicted members remain, the proposal waits or an independent temporary reviewer is appointed under the neutral host; the threshold is not reduced to force a decision.

The founder MUST recuse from decisions uniquely affecting the founder's employer, its connector semantics, comparative ranking, sponsorship or proprietary disclosure. The same rule applies to every member and their affiliates. Conflicts, attendance, recusals and reasons for each decision are recorded publicly, with private sensitive information minimized. General cross-platform definitions are not automatically employer-specific, but their effects must be disclosed and an independent member decides disputed recusal questions.

A vendor-employed connector maintainer may contribute code and evidence but cannot solely approve that connector's semantic mapping. Every such change needs a second reviewer independent of the vendor/affiliate and its directing sponsor, plus reproducible conformance fixtures. If no independent reviewer is available, the change remains experimental and cannot gain a supported-normalizer claim. The same requirement applies to founder-maintained Microsoft-related mappings.

## Open Change Process

1. Submit a public proposal with problem, numbered affected requirements, counterexample, model/denominator impact, compatibility analysis, tests, migration and conflicts.
2. Hold at least30 calendar days of public comment for normative changes; accept criticism without requiring payment, membership or an agreement to use a vendor tool.
3. Publish dispositions of substantive objections. Unresolved objections remain linked in the decision record.
4. Obtain the required unconflicted vote. Record it with a semantic version/draft revision and archived suite digests.
5. Publish updated specification, registries, fixtures, reference results and migration note together. Stable fixture IDs cannot be silently reused for changed meaning.

Editorial corrections that do not change semantics may use two independent reviewers and a recorded rationale. A demonstrated security defect may trigger an emergency warning or release withdrawal, but not a secret redefinition of the standard. Prepublication synthetic implementation work is not claimed to have already passed the future30-day community process.

## Funding and No Influence

All code, specifications, schemas, conformance tests, reference reports and released aggregate data remain freely available. There are no paid tiers, paid certification, paywalled tests, exclusive data-access sponsors or license fees. Operators may incur their own infrastructure costs; "free artifacts" is not a promise of unlimited free hosting.

No sponsor or affiliated group may supply more than25% of accepted cash plus fairly valued restricted/unrestricted in-kind infrastructure and paid staff support in a rolling12-month period. Values and the valuation method are disclosed quarterly. Volunteer personal time is reported separately; employer-paid assigned work is an in-kind sponsorship contribution. With only one prospective sponsor, funds are refused or held unaccepted until diversification satisfies the cap; the founder cannot invoke a bootstrap exception. Unrestricted personal volunteer work cannot buy votes.

Sponsors receive no right to edit metric definitions, suppress negative findings, preapprove aggregate results, choose comparison cohorts, delay release or obtain private raw summaries. A funding agreement attempting this is rejected. Sponsorship review excludes beneficiary employees. Paid consulting by contributors must be clearly external and cannot be sold as project certification or privileged access to normative deliberations.

## Data Custody and Neutral Home

Before the first real-tenant aggregate, an independent institutional home must accept governance, intellectual-property and data stewardship responsibilities in writing. A founder-controlled repository or a neutrality statement alone is not a neutral home. The steering group and host must approve consent, lawful contribution authority, raw-summary retention/deletion, deduplication, independent privacy review, release budget and incident response. No real data intake is enabled before those gates.

Code uses Apache-2.0; specification/schema use CC-BY-4.0; released aggregate data use CC0-1.0. Contributions require an explicit declaration of authority to license, and a signed-off contribution/DCO-style record or host-approved equivalent. Public source citations are not relicensed or copied wholesale. Neutral-host license compatibility is an open issue described below, not permission to silently change the founder's specified licences.

## OpenSSF Sandbox Checklist

The following is grounded in the [OpenSSF TAC project lifecycle process](https://github.com/ossf/tac/blob/main/process/project-lifecycle.md), retrieved2026-09-09. Stage admission is not guaranteed and the project MUST NOT use an OpenSSF membership/project logo before approval.

| Requirement or step | Status / next evidence |
| --- | --- |
| Security-relevant scope and open-development artifacts | Draft standard and executable suite prepared; independent community review pending |
| At least one maintainer; two encouraged at Sandbox | Founder present; independent maintainer recruitment pending |
| Identify a Working Group sponsor or ask TAC for routing | No sponsor approached or agreed |
| Complete lifecycle proposal using official Sandbox template | Prepare proposal from this charter; no PR submitted |
| TAC discussion and approval | Not requested or obtained |
| Repository under OpenSSF GitHub Enterprise as agreed | Local repository only; no transfer performed |
| Linux Foundation IP/licensing due diligence for existing work | Not performed; contributor/employer rights review required |
| Baseline security/community practices and periodic updates | Policy/test artifacts available; external checks and biannual reporting not yet established |
| Multi-organization maintainer growth | Goal, not an assertion of adoption; later lifecycle stages have stricter requirements |

Important compatibility issue: the retrieved OpenSSF process defaults to Apache/MIT code, Community Specification License1.0 for specifications, CDLA for data and CC-BY-4.0 for documentation. The requested CC-BY specification and CC0 data terms do not automatically satisfy those defaults. Seek explicit legal/Governing Board acceptance or choose another neutral home; do not misstate the project as eligible/admitted or substitute new licences without a public decision and Amit's ruling.

Official proposal template: [Sandbox stage template](https://github.com/ossf/tac/blob/main/process/templates/PROJECT_NAME_sandbox_stage.md). The current project is a candidate only. OpenSSF affiliation is a possible path, not a marketing claim.

## Enforcement and Amendment

Violations can lead to a correction, review restriction, removal from a decision, or seat removal by three unconflicted votes with an appeal to the neutral host. The Code of Conduct provides independent reporting and appeal requirements. Founding vacancies do not authorize one-person approval of real data or vendor-specific normative claims. Until the independent group exists, the founder may maintain clearly labeled synthetic drafts and preserve counterexamples, but cannot declare community ratification.
