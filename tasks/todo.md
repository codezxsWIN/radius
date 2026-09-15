# WP_ Task List: Safe Local Repository Acquisition

## `WP_001`: Deterministic acquisition core

Description: Add the repository package and the smallest working acquisition path for regular files.

Acceptance criteria:

- [x] Manifest contains profile/source metadata, sorted file records, raw-byte SHA-256 values, summary and stable snapshot hash.
- [x] Empty directories and Unicode/space-containing relative paths are handled deterministically.
- [x] Output does not contain the supplied absolute repository root.

Verification:

- [x] `pytest -q tests/test_repository_acquisition.py -k "basic or deterministic or empty or unicode"`

Dependencies: none.

Files likely touched:

- `src/blastradius/repository/__init__.py`
- `src/blastradius/repository/acquisition.py`
- `tests/test_repository_acquisition.py`

Estimated scope: medium, three files.

## `WP_002`: Fail-closed safety profile

Description: Enforce exclusions, file/path/tree limits and non-followed links while preserving explicit coverage diagnostics.

Acceptance criteria:

- [x] Fixed excluded directories are not traversed and are reported.
- [x] Oversized files are skipped and reported; global count/byte overflow fails closed.
- [x] Links/reparse points are not followed or read, and depth/path/collision failures are controlled.

Verification:

- [x] `pytest -q tests/test_repository_acquisition.py`

Dependencies: `WP_001`.

Files likely touched:

- `src/blastradius/repository/acquisition.py`
- `tests/test_repository_acquisition.py`

Estimated scope: small, two files.

## Checkpoint: Acquisition boundary

- [x] Focused acquisition tests pass.
- [x] Repeated acquisition output is byte-identical.
- [x] Security assertions cover content, absolute-path and link-target non-disclosure.

## `WP_003`: CLI vertical slice

Description: Wire acquisition to an overwrite-safe `inspect-repo` command and verify stdout, file output and controlled errors.

Acceptance criteria:

- [x] `blastradius inspect-repo <directory>` emits canonical JSON to stdout or `--out`.
- [x] Existing-output protection and `--force` match current CLI behavior.
- [x] A manifest output path inside the analyzed repository is rejected to preserve repeatability.
- [x] Invalid input returns code 2 without echoing an absolute user path.

Verification:

- [x] `pytest -q tests/test_repository_acquisition.py tests/test_cli.py`

Dependencies: `WP_002`.

Files likely touched:

- `src/blastradius/cli.py`
- `tests/test_cli.py`

Estimated scope: small, two files.

## Checkpoint: User flow

- [x] CLI inventories a fixture repository end to end.
- [x] No network access or target execution occurs.
- [x] Existing CLI round trip still passes.

## `WP_004`: Documentation and release verification

Description: Record behavior, limits, decisions and verified state, then run the full regression gate.

Acceptance criteria:

- [x] README explains the safe local input workflow and explicitly states that parsing/analysis is not yet included.
- [x] Continuity and decision records distinguish completed acquisition from proposed downstream features.
- [x] Full tests and diff checks pass before push.

Verification:

- [x] `pytest -q` — 189 passed, 1 skipped in 21.35s.
- [x] `git diff --check`

Dependencies: `WP_003`.

Files likely touched:

- `README.md`
- `DECISIONS.md`
- `WP_PROJECT_CONTINUATION_PROMPT.md`
- `tasks/todo.md`

Estimated scope: medium, four files.

## Checkpoint: Complete

- [x] Every success criterion in `WP_SPEC_repo-acquisition.md` is met.
- [x] Branch is committed and pushed to `origin/WP_repository-input` (`daa4ede`).

---

# WP_ Task List: Repository Evidence

## `WP_005`: Verified reads and restricted marked nodes

Acceptance criteria:

- [x] Selected bytes are reread beneath the root and must match manifest size/hash.
- [x] Mapping keys, source locations, duplicate keys, aliases, merge keys, custom tags, node count and depth are handled deterministically and safely.
- [x] No YAML object construction, subprocess or network access occurs.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py -k "snapshot or yaml or location"`

Dependencies: completed `repo-acquisition` module.

## `WP_006`: GitHub Actions evidence

Acceptance criteria:

- [x] Workflow/job permissions and literal configure-credentials role requests are extracted with source locations.
- [x] Exact push branches are retained for subject matching.
- [x] Missing token permission and dynamic/unsupported constructs produce diagnostics rather than verified role requests.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py -k "workflow or oidc"`

Dependencies: `WP_005`.

## `WP_007`: CloudFormation IAM evidence

Acceptance criteria:

- [x] Literal role, exact GitHub trust and finite Secrets Manager grant facts are extracted.
- [x] Role/subject correlation is deterministic and confidence never exceeds declared configuration.
- [x] Wildcards, denies, intrinsic functions and unsupported conditions do not create allow facts.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py -k "cloudformation or trust or grant"`

Dependencies: `WP_006`.

## `WP_008`: Evidence command and checkpoint

Acceptance criteria:

- [x] Intermediate CLI emits canonical deterministic evidence and protects output paths.
- [x] Coverage says deployed AWS state is unverified.
- [x] Docs, decisions and continuity state match completed behavior.

Verification:

- [x] `pytest -q tests/test_repository_evidence.py tests/test_cli.py` — 19 passed.
- [x] `pytest -q` — 203 passed, 1 skipped.
- [x] `git diff --check`

Dependencies: `WP_007`.
