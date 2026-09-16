# Blast Radius Improvement Prompt: 520 Educational Goals

## Mission

You are improving the existing Blast Radius repository as educational software. Your primary success criterion is not the number of features, documents, dashboards, providers or passing tests. It is whether a newcomer can open a trustworthy example, understand an access path, predict a change, run the experiment and explain the result without cloud credentials or maintainer assistance.

Read [the evidence-backed criticism](2026-09-17-educational-audit.md) before changing anything. Reproduce its failures against the current checkout; do not assume they remain unfixed. Preserve existing user changes, deterministic engines, independently calculated fixtures, offline operation and source-execution boundaries. Improve the code already present instead of starting a replacement application.

This is a **520-goal acceptance backlog**, not a demand for 520 new features or a requirement to complete every goal before shipping. Several goals deliberately constrain scope, remove friction or verify existing behavior. Resolve overlapping work in the existing owning modules rather than creating a separate abstraction, document or test file per goal.

## Execution Order

First deliver a small corrective release: preserve edited graphs across model changes; handle the demonstrated attached-deny and action-case failures; qualify incomplete alternate-trust simulations; reconcile source and generated HTML; expose one offline lesson; make startup understandable; and automate those exact journeys. Do not broaden provider coverage while these failures remain.

Next improve lesson quality, recovery, accessibility and responsiveness. Only then consider additional lessons, instructor material or broader parser profiles. Stop after each working increment, run focused checks, record evidence, and select the next smallest useful change. Do not turn the backlog into a large speculative rewrite.

Targets below are proposed acceptance criteria, not claims of measured performance or existing completion. Agree any changed target explicitly and record the reason. Real novice studies, clean operating-system installs and hosted CI runs require actual access and evidence; missing access blocks those claims, not independent implementation work.

## Boundaries

Keep the core experience free, local and usable offline. No required accounts, cloud login, live tenant access, telemetry, AI chatbot, hosted database, paid dependency, authentication dashboard or additional provider is necessary for the first release. Never execute analyzed repositories, request credentials to resolve missing declarations, apply policies automatically, or relabel unknown access as safe. Do not use npm in this environment. Preserve the existing trusted-analyzer versus untrusted-source CI separation.

Use one existing task tracker for progress. For completed goals, record the implementation location, focused test or observation, result and remaining limitation. A screenshot proves appearance, not comprehension; a passing fixture proves a bounded behavior, not full IAM fidelity. Make the final first-run instructions shorter as the implementation improves.

## 01. Purpose and Scope

- [ ] G001: Define the primary learner and their prerequisite knowledge in one explicit sentence.
- [ ] G002: Define success as completing one correct access-path experiment within five minutes.
- [ ] G003: Distinguish learner needs from security-engineer investigation needs before choosing default navigation.
- [ ] G004: Identify the maintained application root without relying on the surrounding local workspace layout.
- [ ] G005: Declare one primary public entry point for the educational experience.
- [ ] G006: State that authorization reach is not breach probability or an automatic vulnerability classification.
- [ ] G007: Keep repository analysis as an advanced application of the concepts, not a prerequisite lesson.
- [ ] G008: Preserve the reference engine as the source of computed answers.
- [ ] G009: Define which historical artifacts remain supported, archived or illustrative.
- [ ] G010: Establish a small first-release scope before selecting further backlog goals.
- [ ] G011: Explicitly exclude accounts, billing, multitenancy and cloud provisioning from that release.
- [ ] G012: Record the difference between functional correctness and educational effectiveness.
- [ ] G013: Avoid measuring progress by page count or total implemented controls.
- [ ] G014: Separate experimental research claims from demonstrated teaching outcomes.
- [ ] G015: Give every proposed feature a specific learner problem it addresses.
- [ ] G016: Reject features that add prerequisite knowledge without improving the selected lesson.
- [ ] G017: Define how a learner graduates from examples to their own supported inputs.
- [ ] G018: Keep the first lesson independent of operating-system-specific file paths.
- [ ] G019: Preserve the project's free licensing and accurate attribution boundaries.
- [ ] G020: Reassess scope after novice feedback rather than assuming this backlog is immutable.

## 02. Setup and Launch

- [ ] G021: Make the first supported launch command discoverable before advanced configuration instructions.
- [ ] G022: Detect a missing Python interpreter and give one actionable installation direction.
- [ ] G023: Report an unsupported Python version before attempting dependency installation.
- [ ] G024: Explain which interpreter and environment the launcher will actually use.
- [ ] G025: Keep virtual-environment creation local to the chosen project or application directory.
- [ ] G026: Never recreate or clear a working environment during routine startup.
- [ ] G027: Provide a supported installation route that does not require prior knowledge of uv.
- [ ] G028: Retain uv as an optional fast path where it is already available.
- [ ] G029: Explain first-install network requirements separately from offline runtime behavior.
- [ ] G030: Detect missing runtime dependencies and identify them without exposing unrelated environment details.
- [ ] G031: Offer an explicit dependency-repair action rather than silently reinstalling on every launch.
- [ ] G032: Keep installation failures visible when a Windows launcher is opened directly.
- [ ] G033: Test launch commands from a directory other than the repository root.
- [ ] G034: Test installation and startup from a path containing spaces.
- [ ] G035: Handle an occupied port without terminating the unrelated process.
- [ ] G036: Print the actual bound local URL rather than assuming the default port succeeded.
- [ ] G037: Preserve headless startup for workshops and automated checks.
- [ ] G038: Make service shutdown understandable and verify that it releases the listening socket.
- [ ] G039: Separate application startup from development-only build and test requirements.
- [ ] G040: Record clean-install results separately from successful launches on a prepared machine.

## 03. Offline Distribution

- [ ] G041: Identify the smallest existing lesson that can run from a standalone HTML artifact.
- [ ] G042: Include every required font, icon, script and example in the offline distribution.
- [ ] G043: Let learners open that lesson without starting a Python server.
- [ ] G044: Preserve a server-backed route only for capabilities that genuinely require it.
- [ ] G045: Make the relationship between offline lesson and local analyzer explicit.
- [ ] G046: Package the educational assets deliberately instead of leaving them available only in source checkouts.
- [ ] G047: Verify the installed package contains every advertised bundled example.
- [ ] G048: Verify the installed package can locate assets outside the source tree.
- [ ] G049: Test offline launch after the browser cache has been cleared.
- [ ] G050: Fail the offline test on unexpected HTTP or HTTPS asset requests.
- [ ] G051: Include third-party license notices with the assets they cover.
- [ ] G052: Keep the offline artifact size visible in release verification.
- [ ] G053: Exclude benchmark payloads, temporary environments and personal reports from release bundles.
- [ ] G054: Identify the artifact's version and source revision without displaying unnecessary hashes by default.
- [ ] G055: Provide checksums for distributable artifacts without calling them public signatures.
- [ ] G056: Document which report operations remain available without the local server.
- [ ] G057: Disable unavailable offline operations with a specific reason.
- [ ] G058: Test file-based opening in the browsers claimed as supported.
- [ ] G059: Provide a low-bandwidth workshop distribution that does not fetch dependencies during teaching.
- [ ] G060: Verify the distributed artifact rather than only the development source page.

## 04. Documentation Front Door

- [ ] G061: Put a concise educational quickstart above research history and detailed scope notes.
- [ ] G062: Explain the first visible result in ordinary language immediately after the launch instruction.
- [ ] G063: Provide expected output for the first command so success is recognizable.
- [ ] G064: Separate install, learn, review and contribute documentation paths.
- [ ] G065: Link the smallest interactive example directly from the maintained README.
- [ ] G066: Move conflicting historical quickstarts behind a clearly labeled archive link.
- [ ] G067: Update the architecture description to match current packages, dependencies and input types.
- [ ] G068: Resolve contradictory direction statements without deleting the historical decision record.
- [ ] G069: Explain the two surrounding Python package names where workspace confusion can occur.
- [ ] G070: Avoid presenting a pre-existing local virtual environment as part of a fresh clone.
- [ ] G071: Define credential, principal, binding, resource and action in a compact glossary.
- [ ] G072: Introduce OIDC and IAM only where the repository lesson needs them.
- [ ] G073: Distinguish a walkthrough for presenters from exercises intended for independent learners.
- [ ] G074: Link relevant hand-computed fixtures from the lesson that uses them.
- [ ] G075: Put exact parser limitations beside the supported-input instructions.
- [ ] G076: Document the difference between no finding, failed analysis and incomplete evidence.
- [ ] G077: Give one safe troubleshooting path for each common setup failure.
- [ ] G078: Check all quickstart commands against the installed package.
- [ ] G079: Validate relative documentation links in a freshly extracted distribution.
- [ ] G080: Keep a single authoritative current verification summary with dated historical receipts elsewhere.

## 05. First Learning Journey

- [ ] G081: Begin with a small concrete access question rather than a collection of summary metrics.
- [ ] G082: Make the single-path example the first suggested learner action.
- [ ] G083: Show the starting identity and target resource before advanced source evidence.
- [ ] G084: Present the initial result before requesting a real repository path.
- [ ] G085: Give the first exercise one clear learning objective.
- [ ] G086: Ask the learner to predict the result before revealing a counterfactual answer.
- [ ] G087: Allow a prediction without account creation or personal information.
- [ ] G088: Run the actual engine when the learner makes the supported change.
- [ ] G089: Explain which input changed and which inputs stayed fixed.
- [ ] G090: Compare the prediction with the computed answer without grading the learner's identity.
- [ ] G091: Reveal a short causal explanation rather than only a green or red outcome.
- [ ] G092: Offer an explicit reset to the original example.
- [ ] G093: Preserve the current experiment while the learner inspects supporting evidence.
- [ ] G094: Make the next lesson optional after the first objective is complete.
- [ ] G095: Keep the first lesson independent of JSON editing skills.
- [ ] G096: Offer raw JSON as an advanced inspection surface for the same example.
- [ ] G097: Avoid requiring p95, Gini or weighted metrics to understand direct access.
- [ ] G098: Make an incorrect prediction useful by identifying the relevant misconception.
- [ ] G099: Provide a short completion question that checks understanding rather than button clicking.
- [ ] G100: Measure first-lesson completion time with people who have not seen the project before.

## 06. Graph Fundamentals

- [ ] G101: Teach the distinction between a credential and the principal it authenticates as.
- [ ] G102: Show that a resource-action pair, not a resource alone, is the counted unit.
- [ ] G103: Use a four-pair example with an independently hand-computed denominator.
- [ ] G104: Demonstrate direct authorization before introducing escalation.
- [ ] G105: Show that two paths to the same pair do not double-count reach.
- [ ] G106: Demonstrate nested membership without treating every graph hop as escalation.
- [ ] G107: Show a terminating cycle and explain why it adds no infinite reach.
- [ ] G108: Distinguish a witness path from the full set of available paths.
- [ ] G109: Identify the assumptions required for an identity-assumption transition.
- [ ] G110: Contrast reading secret-store metadata with reading a represented credential.
- [ ] G111: Show why a metadata-only edge cannot authorize credential acquisition.
- [ ] G112: Introduce absolute reach before presenting normalized radius.
- [ ] G113: Demonstrate that adding an unreachable resource changes the denominator, not existing permissions.
- [ ] G114: Preserve the declared universe when comparing permission-removal scenarios.
- [ ] G115: Show sensitivity weights as explicit policy choices rather than objective probabilities.
- [ ] G116: Demonstrate an undefined zero-weight denominator without inventing a zero score.
- [ ] G117: Explain action weighting with a small independently calculated example.
- [ ] G118: Contrast bounded escalation reach with unbounded canonical reach.
- [ ] G119: Show why the same credential can have different weighted and unweighted rankings.
- [ ] G120: Link each foundational lesson to the specific invariant its regression protects.

## 07. OIDC and Repository Lessons

- [ ] G121: Explain the workflow job as the modeled starting context in the repository example.
- [ ] G122: Separate assumed job compromise from evidence that a compromise occurred.
- [ ] G123: Identify the workflow declaration requesting an OIDC token.
- [ ] G124: Explain why token-request permission alone does not grant AWS resource access.
- [ ] G125: Show the requested role ARN and the declaration used to match it.
- [ ] G126: Explain the trust audience using the actual example value.
- [ ] G127: Explain the repository and branch components of the subject claim.
- [ ] G128: Demonstrate a mismatched branch without recommending broader trust to produce a finding.
- [ ] G129: Demonstrate a mismatched provider account as a broken correlation.
- [ ] G130: Demonstrate a role-path mismatch independently from a role-name mismatch.
- [ ] G131: Show the finite permission statement that reaches the example secret.
- [ ] G132: Separate source declarations from effective deployed authorization throughout the lesson.
- [ ] G133: Explain a missing IAM declaration without requesting credential values.
- [ ] G134: Show unresolved secret-reference names without collecting their values.
- [ ] G135: Teach that a local action's input is not proof of that action's authentication behavior.
- [ ] G136: Demonstrate one finite matrix expansion with separate job-variant identities.
- [ ] G137: Explain why variants must not pool permissions with one another.
- [ ] G138: Show environment-subject support as a profile boundary, not a silent branch substitution.
- [ ] G139: Distinguish the GitHub source slug from a claim about a deployed account.
- [ ] G140: Finish the lesson with a source-backed explanation the learner can reproduce.

## 08. Denies, Alternatives and Constraints

- [ ] G141: Demonstrate an explicit deny subtracting an otherwise allowed action.
- [ ] G142: Explain why deleting a deny can increase reach.
- [ ] G143: Show actor-scoped deny behavior without leaking one identity's restrictions into another.
- [ ] G144: Contrast an approval requirement with an already satisfied token property.
- [ ] G145: Demonstrate a device requirement under each supported attacker model.
- [ ] G146: Explain the difference between modeled network assumptions and verified network reachability.
- [ ] G147: Demonstrate the time-window assumption without implying that time is measured live.
- [ ] G148: Show two equivalent exact trust routes to the same target.
- [ ] G149: Demonstrate that removing one alternative leaves the target reachable.
- [ ] G150: Demonstrate that removing both modeled alternatives changes the result.
- [ ] G151: Introduce shared trust across jobs and show the complete affected job set.
- [ ] G152: Explain why independent what-if deltas cannot simply be added together.
- [ ] G153: Contrast a proved alternative route with a potentially relevant unsupported route.
- [ ] G154: Show an incomplete comparison without presenting a success verdict.
- [ ] G155: Explain that a permission boundary is not another ordinary allow statement.
- [ ] G156: Show unresolved policy composition as uncertainty, not as automatically effective access.
- [ ] G157: Include a least-privilege exercise with declared legitimate workload requirements.
- [ ] G158: Preserve required access in the successful answer to that least-privilege exercise.
- [ ] G159: Include an intentionally overbroad trust example with accurately qualified evidence.
- [ ] G160: Ask learners to explain why zero modeled reach may not mean zero deployed access.

## 09. Interactive Graph State

- [ ] G161: Maintain the edited graph independently from the preset and computed result.
- [ ] G162: Recompute the active edited graph when the learner switches constraint models.
- [ ] G163: Add the device-constraint, Default-to-Strict regression that currently produces a misleading increase.
- [ ] G164: Preserve added resources and edges when switching models.
- [ ] G165: Keep the active input hash distinct from the baseline input hash.
- [ ] G166: Make explicit reset the only ordinary action that discards a valid experiment.
- [ ] G167: Warn before replacing edited input with a different preset.
- [ ] G168: Preserve editor content while opening definitions or evidence dialogs.
- [ ] G169: Preserve editor content while toggling theme or display-only options.
- [ ] G170: Recompute or clearly invalidate results after any semantic input change.
- [ ] G171: Never display a previous valid score as the answer to invalid current input.
- [ ] G172: Separate parser errors from graph-semantic errors in editor feedback.
- [ ] G173: Identify the invalid field or declaration when the validator provides that information.
- [ ] G174: Support undo and redo for the existing bounded graph-edit operations.
- [ ] G175: Keep undo history separate from model-selection history.
- [ ] G176: Make added-node identifiers deterministic within a saved experiment.
- [ ] G177: Reject duplicate identifiers without partially mutating the valid baseline.
- [ ] G178: Preserve the same selected credential when it still exists after recomputation.
- [ ] G179: Explain selection changes when the previously selected credential was removed.
- [ ] G180: Offer explicit synthetic experiment export and import for continuing a lesson later.

## 10. Lesson Presets and Answers

- [ ] G181: Give each learner-facing preset a plain-language title alongside its conformance identifier.
- [ ] G182: State exactly one primary concept for each introductory preset.
- [ ] G183: Order presets by prerequisite concepts rather than internal fixture numbering alone.
- [ ] G184: Keep the first three examples small enough to inspect completely.
- [ ] G185: Record the expected starting pair set independently of the production engine.
- [ ] G186: Record the expected changed pair set for each exercise answer.
- [ ] G187: Keep the original derivation visibly tied to the unchanged preset.
- [ ] G188: Replace stale derivation text with an edited-experiment explanation after modifications.
- [ ] G189: Include one exercise where a plausible change has no effect.
- [ ] G190: Include one exercise where a decrease in percentage does not mean permissions were removed.
- [ ] G191: Include one exercise where removing the wrong control increases access.
- [ ] G192: Include one exercise where missing evidence prevents a conclusion.
- [ ] G193: Provide hints that reveal the next reasoning step rather than immediately giving the answer.
- [ ] G194: Make answer reveal explicit so learners can attempt the prediction first.
- [ ] G195: Let learners repeat exercises with restored original inputs.
- [ ] G196: Avoid using incident victim details as decorative scenario material.
- [ ] G197: Mark reconstructed incident assumptions separately from documented public facts.
- [ ] G198: Keep optional incident lessons separate from the foundational sequence.
- [ ] G199: Version lesson expectations whenever their meaning changes.
- [ ] G200: Test that every advertised lesson has a valid starting state and reachable completion state.

## 11. Repository Intake

- [ ] G201: Explain supported repository formats before asking the learner to acquire a repository.
- [ ] G202: Make the public URL and local directory modes visually unambiguous.
- [ ] G203: Preserve the entered source when validation fails so correction is inexpensive.
- [ ] G204: Explain why local analysis needs the repository slug for OIDC correlation.
- [ ] G205: Validate a malformed slug before starting expensive inventory work.
- [ ] G206: Identify a nonexistent local directory without replacing it with a generic parser error.
- [ ] G207: Reject network paths with an explicit local-only explanation.
- [ ] G208: Explain unsupported GitHub tree or file URLs and identify the required repository URL form.
- [ ] G209: Distinguish an invalid ref from an unsupported source profile where the transport permits it.
- [ ] G210: Show the resolved immutable commit for public inputs.
- [ ] G211: Explain public rate limiting without requesting an access token as a shortcut.
- [ ] G212: Provide a bundled example fallback after a network failure.
- [ ] G213: Keep scan activity independent from animation completion or tab visibility.
- [ ] G214: Show the current acquisition or analysis stage using actual progress events.
- [ ] G215: Provide cancellation without leaving a partial result labeled complete.
- [ ] G216: Prevent accidental overlapping analyses from mixing results or controls.
- [ ] G217: Keep the previous completed report explicitly available or deliberately cleared during a new run.
- [ ] G218: Explain large-file skips as coverage limits rather than successful parsing.
- [ ] G219: Display the public-source privacy boundary before a learner submits real repository details.
- [ ] G220: Keep analyzed files as data and never run their setup, hooks, actions or dependencies.

## 12. Coverage and Evidence Gaps

- [ ] G221: Separate inventoried, selected, parsed, partially understood and unparsed file counts.
- [ ] G222: Count unsupported Terraform HCL files explicitly when they are present.
- [ ] G223: Distinguish out-of-profile files from malformed supported documents.
- [ ] G224: Show when no supported infrastructure declarations were found.
- [ ] G225: Tie each diagnostic to its actual source location where available.
- [ ] G226: Give each unresolved identity a specific evidence-needed reason.
- [ ] G227: Separate a missing role declaration from a role declaration that cannot be interpreted safely.
- [ ] G228: Preserve warnings about restrictions even when an independent literal allow is found.
- [ ] G229: Surface gaps relevant to the selected finding beside that finding.
- [ ] G230: Surface potentially surviving alternatives beside a remediation comparison.
- [ ] G231: Avoid hiding critical scope qualifiers solely in collapsed advanced sections.
- [ ] G232: State the denominator behind any displayed coverage percentage.
- [ ] G233: Never equate parsing every selected file with understanding the entire repository.
- [ ] G234: Give zero-finding results a next step appropriate to their actual evidence gap.
- [ ] G235: Differentiate no identity requests from unresolved identity requests.
- [ ] G236: Explain matrix-expansion limits with observed variant counts and configured caps.
- [ ] G237: Preserve relevant skipped-file information in every exported report format.
- [ ] G238: Identify unsupported source constructs without dumping unrelated sensitive source content.
- [ ] G239: Keep coverage terms consistent across CLI, browser, Markdown and SARIF metadata.
- [ ] G240: Test coverage explanations on repositories that contain no positive findings.

## 13. Bounded AWS Correctness

- [ ] G241: Enumerate the exact CloudFormation IAM resource forms the parser recognizes.
- [ ] G242: Detect literal external policy attachments to roles already included in the analysis.
- [ ] G243: Treat relevant unresolved external attachments as a completeness blocker, not an absent policy.
- [ ] G244: Preserve role-name and role-path matching when joining supported declarations.
- [ ] G245: Retain provider-account matching independently from role-name matching.
- [ ] G246: Distinguish unknown restrictive policy composition from a known unrestricted allow.
- [ ] G247: Preserve the original IAM action spelling in evidence exports.
- [ ] G248: Normalize only case-insensitive action comparisons, not all policy strings.
- [ ] G249: Check trust-action capitalization using the same semantic discipline as permission actions.
- [ ] G250: Add equivalent inline-deny and AWS::IAM::Policy-attached-deny regression cases.
- [ ] G251: Add mixed-case GetSecretValue and AssumeRoleWithWebIdentity regression cases.
- [ ] G252: Record original condition operators and values rather than flattening distinct semantics.
- [ ] G253: Handle StringEquals wildcard-looking literals without treating them as StringLike patterns.
- [ ] G254: Preserve relevant broad trust statements when an exact trust also exists.
- [ ] G255: Prevent exact-trust removal from implying complete blocking while unsupported alternatives remain.
- [ ] G256: Keep permission boundaries outside complete-path claims until their supported semantics are established.
- [ ] G257: Diagnose unsupported managed-policy attachments at the affected role.
- [ ] G258: Preserve opaque CloudFormation intrinsic values without interpreting them as literal permissions.
- [ ] G259: Identify Terraform-derived grant provenance correctly instead of labeling every grant CloudFormation.
- [ ] G260: Document every accepted authorization rule with a counterexample and a bounded correctness test.

## 14. Terraform Scope

- [ ] G261: Name the existing parser Terraform JSON support, not unrestricted Terraform support.
- [ ] G262: State explicitly that HCL, state, plans and expression execution are not required for lessons.
- [ ] G263: Detect a supported literal Terraform JSON example before enabling its analysis action.
- [ ] G264: Distinguish policy JSON syntax errors from unsupported Terraform references.
- [ ] G265: Preserve source coordinates for literal trust and permission declarations.
- [ ] G266: Keep role and inline-policy correlation within a documented ownership boundary.
- [ ] G267: Explain why a cross-file join is unresolved instead of suggesting that trust is absent.
- [ ] G268: Add the unrelated second-file regression from the review as a coverage-policy test.
- [ ] G269: Determine whether unrelated provider-only files can be safely excluded from join ambiguity.
- [ ] G270: Retain conservative rejection when another file can materially change the role's policies.
- [ ] G271: Identify which files create join uncertainty for each affected declaration.
- [ ] G272: Avoid advising users to restructure deployed infrastructure merely to satisfy the parser.
- [ ] G273: Provide a fictional supported Terraform JSON lesson separately from real-source guidance.
- [ ] G274: Test denied and ambiguous policies in that Terraform lesson.
- [ ] G275: Preserve the difference between unsupported input and malformed input in exported coverage.
- [ ] G276: Do not read Terraform state to recover secret values or runtime permissions.
- [ ] G277: Do not invoke Terraform initialization, providers or plan execution during repository review.
- [ ] G278: Keep any future HCL work behind a separately approved and tested parser profile.
- [ ] G279: Measure representative-source coverage before advertising a broader Terraform capability.
- [ ] G280: Keep Terraform feature expansion outside the launch-critical educational release.

## 15. Findings and Meaning

- [ ] G281: Distinguish declared access observations from findings requiring a security policy violation.
- [ ] G282: Explain the start-condition assumption on the main result, not only in hidden detail.
- [ ] G283: Define the unit counted by a finding when several requests share one job and secret.
- [ ] G284: Display distinct jobs, secrets and request-derived paths with separate labels.
- [ ] G285: Avoid promoting ordinary required access to high priority without additional justification.
- [ ] G286: Make prioritization criteria inspectable when a priority is assigned.
- [ ] G287: Distinguish confidence in source extraction from confidence in effective deployed access.
- [ ] G288: Preserve an explicit unknown state for unsupported authorization semantics.
- [ ] G289: Keep hypothetical compromise wording visible in portable reports.
- [ ] G290: Avoid using a green appearance alone to communicate a security conclusion.
- [ ] G291: State whether a result is baseline, modified model or saved comparison.
- [ ] G292: Remove the claim of smallest change unless the relevant minimization is actually computed.
- [ ] G293: Describe full trust-statement removal as removal, not an automatically safe restriction.
- [ ] G294: Separate target-path interruption from repository-wide permission reduction.
- [ ] G295: Preserve evidence limitations when sorting, filtering or selecting findings.
- [ ] G296: Replace blanket high-priority semantics with a documented educational observation and review taxonomy.
- [ ] G297: Keep zero findings distinct from successful completion of a comprehensive security assessment.
- [ ] G298: Explain when a stronger-looking result comes from a narrower modeled graph.
- [ ] G299: Carry the same interpretation into SARIF without inventing unsupported vulnerability severity.
- [ ] G300: Ask an uninvolved reviewer to explain the result before accepting its wording as clear.

## 16. Simulation and Required Access

- [ ] G301: Preserve all modeled alternatives when simulating a selected trust removal.
- [ ] G302: Keep the original graph immutable during every comparison.
- [ ] G303: Recompute the whole selected change set rather than adding independent deltas.
- [ ] G304: Show all affected jobs when a trust statement is shared.
- [ ] G305: Preserve the selected control set while filtering or inspecting findings.
- [ ] G306: Prevent stale comparison responses from overwriting newer selections.
- [ ] G307: Render unknown impact after a comparison failure instead of restoring a fabricated success.
- [ ] G308: Explain what the selected removal does to legitimate deployment access.
- [ ] G309: Attach unresolved-route warnings directly to apparently successful blocking comparisons.
- [ ] G310: Distinguish a selected target no longer being reachable from all secrets becoming unreachable.
- [ ] G311: Expose the fixed before-and-after counting units for every comparison.
- [ ] G312: Let a learner reset all staged controls in one explicit action.
- [ ] G313: Include baseline and comparison identities in saved change requests.
- [ ] G314: Mark change requests as review documents, not executable infrastructure patches.
- [ ] G315: Refuse controls that do not belong to the current baseline.
- [ ] G316: Test repeated and rapidly reversed control selections for deterministic final state.
- [ ] G317: Define required-access constraints for optional least-privilege optimization lessons.
- [ ] G318: Reject a supposedly successful exercise answer that breaks required access.
- [ ] G319: Report infeasible preservation requirements instead of recommending arbitrary access removal.
- [ ] G320: Keep platform mutation permanently outside the educational simulation controls.

## 17. Session State and Exports

- [ ] G321: Preserve synthetic lesson state across an ordinary browser refresh.
- [ ] G322: Keep real repository persistence opt-in and clearly separate from synthetic lesson persistence.
- [ ] G323: Provide a visible unsaved-change indication for edited experiments and staged reviews.
- [ ] G324: Explain what is lost when a live local session is stopped.
- [ ] G325: Restore the selected lesson and model when importing a saved synthetic experiment.
- [ ] G326: Validate imported experiment structure before replacing the active state.
- [ ] G327: Reject incompatible repository reports in the graph viewer with format-specific guidance.
- [ ] G328: Distinguish baseline export from change-request export in button labels.
- [ ] G329: Preserve selected evidence and coverage in offline repository reports.
- [ ] G330: Explain that saved single-control comparisons cannot recompute arbitrary offline combinations.
- [ ] G331: Include the relevant model and input identity in exported educational answers.
- [ ] G332: Keep export content independent of which rows happen to be visible after filtering.
- [ ] G333: Verify that JSON, Markdown, HTML and SARIF describe the same baseline.
- [ ] G334: Check content integrity during report import without claiming source authentication.
- [ ] G335: Expose an explicit clear-data operation for the current local session.
- [ ] G336: Verify that clearing data also clears retained comparison context.
- [ ] G337: Warn about sensitive infrastructure names before sharing real-source exports.
- [ ] G338: Generate useful filenames containing report type and an unambiguous snapshot identifier.
- [ ] G339: Handle unavailable clipboard access with a usable, non-destructive fallback.
- [ ] G340: Test exported file contents rather than treating a button click as proof of download correctness.

## 18. Interface and Accessibility

- [ ] G341: Preserve the established visual language instead of adding a separate decorative dashboard.
- [ ] G342: Keep the current question, inputs and result visible before secondary metrics.
- [ ] G343: Use the visual access path as instructional content rather than hiding all causality by default.
- [ ] G344: Keep advanced evidence expandable without making core assumptions undiscoverable.
- [ ] G345: Use stable dimensions so changing values cannot shift primary controls.
- [ ] G346: Ensure all controls have meaningful accessible names and visible focus states.
- [ ] G347: Support the complete first lesson using keyboard input alone.
- [ ] G348: Preserve focus after recomputation, filtering and dialog closure.
- [ ] G349: Associate form errors with the fields that need correction.
- [ ] G350: Announce computation completion and uncertainty without flooding assistive technology with updates.
- [ ] G351: Keep diagrams understandable without relying only on color.
- [ ] G352: Provide a readable textual equivalent for each instructional graph.
- [ ] G353: Verify mobile layouts at 320 and 390 CSS pixels without horizontal page overflow.
- [ ] G354: Check zoomed text and long repository names for clipping.
- [ ] G355: Preserve touch targets and avoid tightly packed controls in the first lesson.
- [ ] G356: Honor reduced-motion preferences without suppressing the computed result.
- [ ] G357: Keep state transitions functional when the browser tab is backgrounded.
- [ ] G358: Avoid adding marketing copy or empty sections to the working interface.
- [ ] G359: Test contrast and semantic structure in both supported themes.
- [ ] G360: Treat automated accessibility audits as a baseline, not a substitute for manual assistive-technology checks.

## 19. Performance and Work Limits

- [ ] G361: Establish a measured responsiveness budget for the bundled first lesson on a named machine.
- [ ] G362: Track installation, startup, analysis, rendering and export times separately.
- [ ] G363: Reproduce the 8-job/8-secret and 32-job/16-secret workloads before optimizing.
- [ ] G364: Retain exact expected finding counts in every performance fixture.
- [ ] G365: Profile the owning computation before selecting an optimization.
- [ ] G366: Avoid repeating equivalent graph-removal work for every finding using the same control.
- [ ] G367: Validate each distinct modified graph at a justified boundary rather than blindly repeating full validation.
- [ ] G368: Reuse immutable indexes where that preserves actor and action isolation.
- [ ] G369: Keep reachability results deterministic after caching or reuse.
- [ ] G370: Bound input expansion before allocating large variant collections.
- [ ] G371: Bound comparison work explicitly and explain refusals without silent sampling.
- [ ] G372: Add cancellation checks at safe points in long-running analysis.
- [ ] G373: Keep canceled operations from installing partial results in the session.
- [ ] G374: Measure output amplification when small source files produce many findings.
- [ ] G375: Avoid unnecessarily duplicating evidence in memory while preserving portable report meaning.
- [ ] G376: Measure large-table rendering separately from Python analysis time.
- [ ] G377: Paginate or virtualize only where observed data sizes justify the complexity.
- [ ] G378: Ensure progress reporting is based on completed work, not a fake timer.
- [ ] G379: Record hardware, interpreter, data shape and measurement exclusions with performance receipts.
- [ ] G380: Require semantic parity tests before accepting any speed improvement.

## 20. Core and Parser Regression Coverage

- [ ] G381: Preserve the existing Python and JavaScript conformance corpora unchanged unless semantics intentionally change.
- [ ] G382: Maintain independently hand-computed expectations for introductory lessons.
- [ ] G383: Keep duplicate-path invariance covered independently of presentation tests.
- [ ] G384: Keep cycle termination and deterministic witness selection covered.
- [ ] G385: Test actor-scoped denies across acquired identities.
- [ ] G386: Test metadata-only secret-store reads against credential-acquisition guards.
- [ ] G387: Test fixed denominators across permission removals.
- [ ] G388: Test zero sensitivity denominators as undefined rather than zero.
- [ ] G389: Test exact arithmetic without accepting lossy numeric coercion.
- [ ] G390: Cover alternative trust statements under both individual and combined removals.
- [ ] G391: Cover attached restrictive policies in the same and separate selected source files.
- [ ] G392: Cover supported IAM action case variants without changing resource-case behavior.
- [ ] G393: Cover mixed exact and unsupported broad trust alternatives.
- [ ] G394: Cover unsupported constructs that coexist with otherwise literal declarations.
- [ ] G395: Cover ambiguity across identically named roles and different role paths.
- [ ] G396: Cover matrix types, include/exclude behavior and variant permission isolation.
- [ ] G397: Cover malformed, duplicate-key, aliased and tagged YAML inputs according to the documented profile.
- [ ] G398: Cover source files changing between acquisition and extraction.
- [ ] G399: Preserve evidence that analyzed repositories are never imported or executed.
- [ ] G400: Classify skipped tests honestly and avoid counting them as exercised safeguards.

## 21. Browser Journey Tests

- [ ] G401: Automate the exact first lesson from a fresh page through its completion question.
- [ ] G402: Test launch into the smallest example without prior session state.
- [ ] G403: Test prediction, change, recomputation, explanation and reset as one connected journey.
- [ ] G404: Test edit-then-model-switch without resetting the graph between actions.
- [ ] G405: Test edit-then-theme-toggle and edit-then-evidence-inspection continuity.
- [ ] G406: Test selecting another preset with unsaved edits.
- [ ] G407: Test refresh recovery for synthetic experiments.
- [ ] G408: Test exact metric captions against the same data used for the displayed percentages.
- [ ] G409: Test a comparison with an unresolved alternative and require qualified wording.
- [ ] G410: Test source-validation failures followed by successful correction.
- [ ] G411: Test local-service loss without showing a successful comparison.
- [ ] G412: Test keyboard navigation across examples, model controls, diagrams and dialogs.
- [ ] G413: Test the first lesson with reduced motion enabled.
- [ ] G414: Test hidden-tab computation completion without relying on animation frames.
- [ ] G415: Test all supported export formats for meaningful content and expected extensions.
- [ ] G416: Test offline reopening without network requests.
- [ ] G417: Assert that accessibility violations fail the relevant browser test command.
- [ ] G418: Assert that unexpected page errors fail the relevant browser test command.
- [ ] G419: Separate within-run screenshot repeatability from historical visual-regression protection.
- [ ] G420: Retain focused screenshots showing the learner's decision points at desktop and mobile sizes.

## 22. Build and Continuous Integration

- [ ] G421: Reconcile the maintained UI source with the currently shipped corrected HTML.
- [ ] G422: Regenerate educational HTML using one documented build command.
- [ ] G423: Verify source-to-generated artifact equality in a clean checkout.
- [ ] G424: Fail CI when a required generated artifact is stale.
- [ ] G425: Run the first-lesson browser journey in the normal verification workflow.
- [ ] G426: Run repository-review browser checks when their owning code or assets change.
- [ ] G427: Include interaction contracts in the documented visual-test command.
- [ ] G428: Test the installed wheel from outside the source tree.
- [ ] G429: Check that release packages include the advertised educational assets.
- [ ] G430: Test supported Python versions rather than only one prepared interpreter.
- [ ] G431: Add an explicit supported-OS test matrix when those environments are available.
- [ ] G432: Use supported runtime versions for CI tools and document the compatibility basis.
- [ ] G433: Pin security-sensitive workflow actions to reviewed immutable revisions.
- [ ] G434: Keep target repository code out of trusted analyzer installation steps.
- [ ] G435: Preserve isolated Python execution for untrusted-source review.
- [ ] G436: Keep pull-request analysis credentials read-only and separate from optional publishing permissions.
- [ ] G437: Set meaningful job time limits and retain actionable failure artifacts.
- [ ] G438: Prevent synthetic test artifacts from accidentally including real local reports.
- [ ] G439: Require an actual hosted run before claiming hosted CI success.
- [ ] G440: Document how to reproduce each required CI gate locally without unnecessary tool installation.

## 23. Privacy and Safety

- [ ] G441: Keep bundled lessons fictional and visibly labeled synthetic.
- [ ] G442: Avoid including credential values in fixtures, screenshots or reports.
- [ ] G443: Preserve token-free public repository acquisition.
- [ ] G444: Keep local analysis independent of any third-party analysis service.
- [ ] G445: Preserve explicit host, origin and session checks on the loopback service.
- [ ] G446: Keep the service bound to loopback by default and reject unsupported exposure modes.
- [ ] G447: Preserve request-size, file-size, archive-size and expansion limits.
- [ ] G448: Reject unsafe archive paths, links and unsupported entry types.
- [ ] G449: Ensure parser errors do not expose unrelated file contents or secrets.
- [ ] G450: Retain raw source text only where required and disclose its storage lifetime.
- [ ] G451: Make synthetic lesson persistence independent of real-source retention permission.
- [ ] G452: Never claim that hashed or pseudonymized infrastructure identifiers are anonymous.
- [ ] G453: Explain that HMAC integrity is not public-key attestation or proof of complete input.
- [ ] G454: Keep private signing material outside distributable artifacts and model-visible logs.
- [ ] G455: Prevent untrusted source strings from becoming executable HTML or scripts.
- [ ] G456: Preserve safe escaping in Markdown and source-location exports.
- [ ] G457: Make external evidence links explicit user actions rather than automatic network fetches.
- [ ] G458: Keep real-cloud mutation outside every lesson and repository-review endpoint.
- [ ] G459: State the trusted-workstation threat boundary without implying hostile-local-process isolation.
- [ ] G460: Review privacy implications before adding telemetry, hosted lessons or shared classroom state.

## 24. Contributor Experience

- [ ] G461: Provide a small contribution path for fixing a lesson or adding one bounded regression.
- [ ] G462: Explain the ownership boundary between parser facts, graph construction, analysis and presentation.
- [ ] G463: Explain how the synthetic graph contract differs from the repository report contract.
- [ ] G464: Keep public APIs stable unless a demonstrated requirement justifies a change.
- [ ] G465: Name the maintained source files for each generated application artifact.
- [ ] G466: Document the commands required after editing templates, styles or browser logic.
- [ ] G467: Reuse existing fixture builders and test helpers before creating new ones.
- [ ] G468: Keep test data minimal enough for a reviewer to verify expected reach manually.
- [ ] G469: Require a counterexample when extending authorization semantics.
- [ ] G470: Require a scope explanation when declining unsupported source constructs.
- [ ] G471: Avoid introducing abstractions solely to organize this long backlog.
- [ ] G472: Keep source comments focused on non-obvious invariants rather than narrating syntax.
- [ ] G473: Separate formatting cleanup from behavior changes when reviewing regressions.
- [ ] G474: Explain how to preserve existing dirty worktrees during contributor verification.
- [ ] G475: Keep generated files and source changes together when a release artifact depends on both.
- [ ] G476: Give contributors a targeted test command for each major ownership area.
- [ ] G477: Preserve failing examples when a semantic discrepancy is discovered.
- [ ] G478: Record deprecations and result-format changes in one maintained location.
- [ ] G479: Document which governance requirements apply to standards changes versus educational presentation changes.
- [ ] G480: Make the smallest useful contribution possible without cloud access or a large development environment.

## 25. Teaching and Evaluation

- [ ] G481: Recruit actual first-time users before claiming that the revised onboarding is easy.
- [ ] G482: Record participant prerequisites without collecting unnecessary identifying information.
- [ ] G483: Measure time from opening the README to the first valid example result.
- [ ] G484: Measure time from the first example to a correctly explained counterfactual.
- [ ] G485: Count requests for maintainer assistance separately from successful independent completion.
- [ ] G486: Ask learners to distinguish reachability from exploitability after the lesson.
- [ ] G487: Ask learners to distinguish graph hops from escalation cost.
- [ ] G488: Ask learners to explain why duplicate paths do not increase absolute reach.
- [ ] G489: Ask learners to explain why a missing finding is not a safety verdict.
- [ ] G490: Ask learners to identify legitimate access broken by a proposed removal.
- [ ] G491: Record misleading interface interpretations as defects even when the engine output is correct.
- [ ] G492: Test the lesson on a machine without the maintainer's existing environment.
- [ ] G493: Observe mobile and keyboard-only use rather than inferring usability from responsive CSS.
- [ ] G494: Provide an optional presenter guide aligned with the exact current learner interface.
- [ ] G495: Provide a short workshop setup checklist that avoids live dependency downloads.
- [ ] G496: Provide independently checked instructor answers for the introductory exercises.
- [ ] G497: Keep assessment questions focused on reasoning rather than memorizing internal field names.
- [ ] G498: Disclose sample size and selection limitations for any educational outcome report.
- [ ] G499: Use observed confusion to revise lesson order before adding more examples.
- [ ] G500: Do not describe a finite usability study as proof that every audience understands the tool.

## 26. Release Evidence and Handoff

- [ ] G501: Select the smallest completed goal set that fulfills the agreed first-release promise.
- [ ] G502: List unresolved launch-critical defects separately from optional backlog items.
- [ ] G503: Keep the release README shorter than the internal improvement backlog.
- [ ] G504: Include one tested install command and one tested offline-open route in the release instructions.
- [ ] G505: Record exact test commands, counts, skips and relevant limitations for the release candidate.
- [ ] G506: Require the reproduced model-switch and attached-deny failures to be resolved or explicitly block the affected claim.
- [ ] G507: Require source and generated educational artifacts to agree before distributing them.
- [ ] G508: Record the selected lesson's measured startup and interaction timings.
- [ ] G509: Record the modest repository workload timing after any performance changes.
- [ ] G510: Verify saved reports identify the correct baseline and comparison state.
- [ ] G511: Verify that offline lessons work without a previously populated browser cache.
- [ ] G512: Verify release bundles contain no private keys, real tenant data or audit scratch files.
- [ ] G513: Record which operating systems and browsers were actually tested.
- [ ] G514: Label unexecuted clean-install, accessibility and hosted-CI checks as unverified.
- [ ] G515: Preserve a rollback artifact before replacing a previously distributed educational build.
- [ ] G516: Provide a concise upgrade note for users with saved experiments or reports.
- [ ] G517: Hand off remaining work as prioritized outcomes rather than another unbounded feature list.
- [ ] G518: Keep implementation completion separate from empirical validation and user acceptance.
- [ ] G519: Obtain explicit authorization before committing, pushing, deploying or publishing the release.
- [ ] G520: Close with a demonstrated learner journey and honest remaining limits, not a claim that every goal is finished.

## Required Delivery Response

For each implementation increment, summarize the learner-visible improvement, changed ownership areas, exact verification performed, and unresolved limitations. Include the shortest working launch instructions. Do not claim all 520 goals are complete because a subset of tests passed. Do not leave the user with another long setup process as the only way to experience the result.
