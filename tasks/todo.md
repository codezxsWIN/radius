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
