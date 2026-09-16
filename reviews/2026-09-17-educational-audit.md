# Blast Radius: Educational Readiness Review

Date: 2026-09-17. Review target: the current working tree, including the existing uncommitted repository-review and Terraform JSON changes. This is a first-time-user-oriented engineering review, not a production security certification.

## Verdict

**There is substantial working engineering here, but the repository is not yet a coherent, easy educational experience.** Its strongest asset is an inspectable, deterministic authorization model. Its weakest asset is the path from arriving at the repository to understanding that model correctly.

The project currently asks learners to navigate a research archive, multiple applications, two Python packages in the surrounding workspace, incompatible result formats, and security-specific vocabulary before it establishes a simple learning loop. The active interface emphasizes findings and removing access; the richer educational graph lab is separate, not included in the installed package, and has a state bug that can teach the opposite of the engine's actual behavior.

This is not a recommendation to add another dashboard, AI assistant, cloud integration, or framework. The next release should make one short lesson reliable, preserve the learner's work, correct the demonstrated parser and presentation failures, and make the existing strengths discoverable.

## Findings, Ordered by Priority

### 1. High: Changing Models Silently Replaces the Learner's Edited Graph

Reproduced in the shipped visual lab:

1. Open Playground, preset BR-001, Default model: 1/4, or 25%.
2. Add a device constraint: the edited graph has six nodes and correctly reports 0/4.
3. Click Strict: the graph silently returns to five nodes and the interface reports 1/4, or 25%.
4. Independently evaluate the six-node edited graph under Strict: the actual result remains 0/4.

This is not merely inconvenient data loss. A learner can infer that stricter controls increased access, when the application actually changed the input. No discard warning or reset explanation appears. Adding a resource and switching models similarly loses the added node.

The model-change handler clears `state.preview`; the subsequent render reconstructs the editor from the preset. See [ui/app.js](../ui/app.js#L133) and [ui/app.js](../ui/app.js#L69).

**Required outcome:** model changes recompute the same edited graph. Input hash, active model and unsaved state must remain distinguishable. Add an edit-then-model-switch regression, not just separate edit and model-switch tests.

### 2. High: A Separately Attached Deny Is Silently Ignored

An independent disposable fixture added a literal `AWS::IAM::Policy` resource with `Roles: ["github-production"]` and an explicit deny of `secretsmanager:GetSecretValue` on `*`.

The same deny embedded under the role's `Policies` produces zero findings and `EXPLICIT_DENY_UNSUPPORTED`. Expressed as the separately attached policy, it produces one high-priority finding, one proposed removal, and **zero diagnostics or evidence gaps**.

[AWS documents](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-iam-policy.html) that this resource attaches an inline policy to the named role. The extractor skips every resource except `AWS::IAM::Role`, so the restriction never reaches its conservative deny handling. See [aws_cloudformation.py](../src/blastradius/repository/aws_cloudformation.py#L172).

The issue is not that the tool must implement all IAM. The issue is that a relevant restrictive declaration in the same parsed source disappears while the result is presented as a complete source-backed path.

**Required outcome:** resolve the bounded literal attachment or explicitly mark the affected role/path incomplete. Unsupported restrictive evidence must not silently become absent evidence.

### 3. High: Rebuilding the Educational Lab Removes Working Corrections

Ran the documented UI build in a disposable copy of the current source. The shipped HTML is 4,074,372 bytes; the rebuilt HTML is 4,067,670 bytes. They remain different after newline normalization.

The shipped artifact contains the corrected weighted-ratio captions, figure-selection control and narrative-copy helper. The rebuilt artifact lacks those markers. More importantly, the current source's metric renderer puts the same `absolute_reach / universe_size` caption under every metric, including bounded and weighted metrics. For the initial lab dataset, the correct bounded caption is 25/71, not the unbounded 45/71.

See [ui/app.js](../ui/app.js#L52), [ui/index.template.html](../ui/index.template.html#L15), and [tools/build_ui.mjs](../tools/build_ui.mjs). Both the shipped and regenerated artifacts pass the existing 14 interaction contracts, demonstrating the missing test coverage.

**Required outcome:** maintain one authoritative source, regenerate the HTML from it, and fail CI when rebuilding changes the checked-in artifact unexpectedly. Test metric captions against exact values, not only the large displayed percentage.

### 4. High: A Successful Simulation Can Hide an Unmodeled Alternative

Another independent fixture contains both the original exact branch trust and a wildcard alternative matching the same repository. Analysis emits `BROAD_GITHUB_TRUST`, but the graph contains only the exact trust. Removing that exact trust reports `after_absolute_reach: 0` and `path_broken: true`.

That is a valid statement about the deliberately reduced graph, not proof that the declared wildcard alternative stopped authorizing access. The current prominent "Simulate fix" and "path is blocked" presentation is stronger than the actionable evidence, particularly with scope and evidence collapsed.

The reduction happens in [evidence.py](../src/blastradius/repository/evidence.py#L136) and [graph.py](../src/blastradius/repository/graph.py#L65). The report semantics are visible in [findings.py](../src/blastradius/repository/findings.py#L93) and [review.html](../src/blastradius/assets/review.html).

**Required outcome:** keep known and unresolved alternative routes visible in the comparison. Use "blocked among modeled routes; remaining access unknown" where appropriate. Never remove the existing diagnostic to make the UI appear simpler.

### 5. Medium: Valid IAM Action Capitalization Silently Changes the Result

Changing only `secretsmanager:GetSecretValue` to `SecretsManager:GetSecretValue` changes the baseline from one finding to zero, without any diagnostic. AWS explicitly states that action prefixes and names are case-insensitive in its [Action documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_action.html).

The exact case-sensitive membership check is in [aws_cloudformation.py](../src/blastradius/repository/aws_cloudformation.py#L142); a similar exact check exists for the trust action.

**Required outcome:** compare action semantics case-insensitively while preserving the original source spelling and coordinates. Do not indiscriminately lowercase resource identifiers, subjects or other case-sensitive fields.

### 6. Medium: Ordinary Authorized Access Is Always Labeled High Priority

Every complete supported path is assigned `"priority": "high"` in [findings.py](../src/blastradius/repository/findings.py#L106). The bundled example has a finite grant and an exact repository/branch trust. The start condition assumes the deployment job is already compromised. The analyzer does not establish that the access is unnecessary or that compromise is possible.

For education, this distinction is essential: "this credential can read this secret" is an authorization fact; "this is excessive access" requires intended workload requirements; "this is exploitable" requires additional evidence.

The proposed action removes the whole trust statement. Calling it "Smallest modeled change" or "Simulate fix" does not establish that it is minimally disruptive or preserves the deployment's required access. The existing per-job impact calculations are valuable, but they do not define business necessity.

**Required outcome:** separate declared capability, suspicious configuration, unresolved evidence and confirmed policy violation. Teach least privilege using an explicit required-access set, not a universal goal of zero permissions.

### 7. Medium: Modest Repository Inputs Become Slow, Without Cancellation

Measured using the independently installed package and generated, supported fixtures with two source files:

| Expanded Jobs | Secrets | Findings | Input Bytes | Analysis Time | Result Bytes |
| --- | --- | --- | --- | --- | --- |
| 8 | 8 | 64 | 1,749 | 1.388 s | 354,201 |
| 32 | 16 | 512 | 2,457 | 28.476 s | 2,794,492 |

These are local Windows measurements, not universal performance promises. Analysis timing covers acquisition through result construction/hash; interpreter startup and the final separately timed serialization are outside the measured call. Final serialization took 0.005 s and 0.042 s respectively.

A separate profiled 64-finding run called full graph validation 65 times. Validation consumed 3.592 of 3.962 profiled analysis seconds, approximately 91%. The code rebuilds and validates a changed graph inside the finding loop: [findings.py](../src/blastradius/repository/findings.py#L93).

The interface disables reset while busy and has no cancel action, progress stages or client analysis deadline: [review.js](../src/blastradius/assets/review.js#L55). The server serializes operations with one shared lock.

**Required outcome:** reuse equivalent control-removal computations, retain validation at the correct boundaries, measure repository-shaped workloads, and provide honest progress/cancellation. Do not optimize by weakening the model or silently sampling findings.

### 8. Medium: The Friendly Launcher Is Not a Fresh-Install Launcher

The current environment launches successfully. A separate installation from copied source also succeeds in approximately 14 seconds using the existing local dependency cache.

However, launching a fresh copied checkout without its own virtual environment exits 1 with: "The project environment is not installed. Follow the setup in README.md." See [start-review.cmd](../start-review.cmd#L3). Python 3.12+ and `uv` are assumed in the new-install instructions, without a first-run diagnostic or a non-`uv` route.

The package itself is not fundamentally broken. The distinction is that one-click startup works only after someone has already completed the installation. No fresh OS or uncached network installation was tested, so the 14-second result is not a newcomer setup-time claim.

**Required outcome:** offer an immediately usable offline lesson and one clearly documented installation route for the optional analyzer. Detect prerequisites, explain failures and avoid destroying working environments.

### 9. Medium: The Educational Material Is Fragmented Across Separate Experiences

The outer workspace README and `blast_radius` package run a working legacy synthetic CLI. The nested Git repository publishes a different package, `blastradius`, whose default app is repository review. The visual lab and the legacy generated dashboard are separate HTML applications.

The outer workspace ambiguity is local layout friction, not a claim that the outer README is the nested repository's public GitHub homepage.

The installed package contains the review UI and two example workflows, but not the visual lab. The lab accepts synthetic engine result v0.1 inputs; repository reports are a different contract. There is no integrated route explaining which tool a learner should use or how their outputs relate.

There is a useful [five-minute presenter script](../demo/DEMO_SCRIPT.md) and excellent [hand-computed fixture explanations](../tests/fixtures/README.md). Those are real assets, not missing work. They are not the current app's onboarding, and a presenter talk track is not a learner's predict-change-explain exercise sequence.

**Required outcome:** one front door with a short learning path; advanced repository review and standards/research material stay available but are not prerequisites.

### 10. Medium: Terraform Coverage Is Easy to Misread

A working literal Terraform JSON fixture produces one finding. Adding a second file containing only a Terraform version requirement makes every Terraform file unsupported for joining and produces zero findings. This is the explicitly conservative global rule in [evidence.py](../src/blastradius/repository/evidence.py#L205), not an undocumented engine failure.

The usability problem is that one unrelated file invalidates otherwise independent evidence. Normal HCL is outside scope entirely, despite "Terraform" being a broad category to most learners. The user should discover that before attempting a scan, not after interpreting zero findings.

**Required outcome:** identify unsupported formats during intake, show HCL/out-of-profile counts explicitly, and scope cross-file uncertainty to relevant declarations when soundly possible. Do not suggest rewriting real infrastructure to satisfy a teaching tool.

### 11. Medium: Refresh Discards the Visible Review and Change Set

After loading the single example and staging a removal, browser reload returns to "Repository review / No source selected," hides the result, and shows zero selected changes. The server retains its last result in memory, but the browser cannot restore the visible investigation from a fresh page.

Privacy is a legitimate reason not to persist real repository data to browser storage automatically. It is not a reason for silent loss of educational or explicitly saved work.

**Required outcome:** restore synthetic lesson state safely, offer explicit review-save/import, or warn before losing a staged change set. Keep real-source retention opt-in.

### 12. Medium: Verification Does Not Protect the Most Important User Journeys

The current Python suite passes, and the browser checks are useful. However, [the normal CI workflow](../.github/workflows/verify.yml) runs Python and language-reference checks, not the repository-review or educational browser suites. [The Makefile](../Makefile#L9) runs the visual browser test but omits the interaction contract script. The visual browser script records accessibility/regression totals without asserting that all those totals are zero; the repository-review suite does enforce its accessibility checks.

There is no automatic first-lesson completion check, edit/model continuity test, source/artifact equality gate, or required repository responsiveness budget in that workflow. Recorded historical test counts cannot substitute for those gates.

**Required outcome:** protect the first successful user journey in CI. Test combinations of actions and the installed artifact, not just functions and individual buttons.

### 13. Medium: Current Documentation Gives Incompatible Maps

[ARCHITECTURE.md](../ARCHITECTURE.md#L3) still describes a synthetic-only prototype with one direct runtime dependency. The current package accepts repository declarations and depends on both JSON Schema and YAML libraries. [DIRECTION.md](../DIRECTION.md) still presents the standards-only direction as controlling, while the current README explains a later repository-first direction.

The README labels its historical section, which is helpful, but still contains several quickstarts and historical numerical milestones. A newcomer must decide which instructions and claims are current. Contributor guidance emphasizes standards governance without an equally clear small educational contribution path.

**Required outcome:** one current architecture and quickstart, with historical decisions linked from an archive rather than mixed into the first-run route.

## What Actually Worked

- Current nested Python suite: **306 passed, 1 skipped in 53.05 seconds**. The skip is the Windows symlink-privilege case, not an executed security test.
- Repository-review browser suite: **15 accessibility audits with zero violations**, four baseline export formats, two change-request formats, no page errors and zero offline HTTP requests.
- Real alternate/shared-trust behavior: **5 -> 5** after one alternative removal; **5 -> 1** after both production alternatives are removed.
- Educational UI contracts: **14 passed**, both before and after rebuilding the disposable copy. This does not cover the independent regressions above.
- JavaScript reference: **120/120 conformance cases**. Clean installed Python reference: **120/120**, with the runner executing each case twice.
- The outer README's first demo command also works and computes the documented 2/4 and 1/4 synthetic reaches.
- The analyzer preserves source, exports offline reports, handles uncertainty deliberately in many places, and has substantial local-host/origin/token protection and bounded archive acquisition.
- The repository-review CI design separates trusted analyzer code from untrusted target source. Preserve that boundary; do not simplify it by executing or installing PR code.

Passing tests are evidence of real implementation, not proof of provider completeness, independent authorship, educational effectiveness or production safety.

## Real-Repository Checks

| Repository | Resolved Commit | Observed Result |
| --- | --- | --- |
| aws-actions/configure-aws-credentials | ec8e608231b771e3614fc6ea4edadab8703331a5 | 57 inventoried files; 13 workflows parsed; 33 expanded job variants; 36 unresolved identity requests; zero complete paths |
| terraform-aws-modules/terraform-aws-iam | ba3fd6ded6911e0454092147fe3704171cc05e00 | 138 inventoried files; 5 workflows parsed; 133 files outside profile; zero selected Terraform files; zero complete paths |

The first case exposes 17 unresolved role locations, 12 local-action sites and four unsupported credential/session-option sites. The second case's only diagnostic category is an unsupported matrix; its actual HCL infrastructure is not assessed.

Both acquisitions succeeded without credentials or source execution. These two repositories are illustrative compatibility checks, not a representative accuracy benchmark. Zero complete paths is not a clean security verdict.

## Recommended Next Release

Make the next release demonstrate one promise: **a learner can open the project, understand one access path, predict a change, run it, and explain the result without cloud credentials or maintainer assistance.**

1. Correct the demonstrated state, parser, uncertainty and build failures first.
2. Make the smallest existing graph the primary offline lesson; expose the richer lab deliberately.
3. Establish a five-minute predict-change-explain sequence with independently checked answers.
4. Preserve edits across model changes and make reset explicit.
5. Make setup, unsupported inputs and real-source retention decisions unambiguous.
6. Put that exact installed/offline journey, build parity and modest performance budgets in CI.
7. Test the experience with actual newcomers before expanding providers or visual features.

Do not make all 520 improvement goals launch requirements. The requested [520-goal improvement prompt](2026-09-17-improvement-prompt.md) is an ordered acceptance backlog, with a deliberately small first release.

## Review Boundaries

The session began at 02:37:28 +05:30 on 2026-09-17. Evidence gathering, independent experiments and synthesis occupied the requested half-hour review window; document preparation continued afterward. Previous session receipts were not treated as current verification.

Application code and existing generated artifacts were not edited. Installation, browser-test output, independent fixture mutations, profiling and UI regeneration were confined to a disposable directory under the system temporary folder. Only these review deliverables were added to the project. Existing uncommitted work was preserved; nothing was committed or pushed.

Not verified: fresh Windows/macOS/Linux installations without cached packages, hosted CI execution, Firefox/Safari, manual assistive-technology testing, representative real-repository accuracy, or actual novice comprehension. No cloud authorization changes, secret reads or deployed-access verification were performed.

One profiler attempt failed because a truncating shell pipeline closed its output; it was rerun successfully to a profile file. The integrated browser refused a temporary HTML path outside trusted folders; editor trust was not changed. The standalone repository browser harness had already exercised the disposable files successfully. Neither incident is an application defect.
