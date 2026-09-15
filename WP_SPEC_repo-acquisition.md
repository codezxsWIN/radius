# Spec: Safe Local Repository Acquisition

Module id: `repo-acquisition`  
Status: **Proposed for review**  
Capability map: `WP_CAPABILITY_MAP.md`  
Created: 2026-09-15

## Objective

Build the first input boundary for repository-to-production analysis: safely inventory a user-supplied local Git working tree as untrusted data without executing repository code or following paths outside the selected root.

The initial user is a platform or security engineer who wants to analyze a checked-out repository. The module produces a deterministic snapshot manifest that downstream evidence parsers can consume without traversing the filesystem again.

This module does not parse GitHub Actions, infer permissions, build an authorization graph, run blast-radius analysis, clone remote repositories, or inspect private GitHub accounts. Those are downstream or deferred capabilities.

## User Story

As a platform/security engineer, I can point Blast Radius at a local repository and receive a safe, deterministic inventory of analyzable files, skipped files and coverage limitations so that later parsers operate on a bounded and auditable snapshot.

## Proposed Command

```powershell
blastradius inspect-repo C:\path\to\repository `
  --out results\repository-manifest.json
```

Overwrite remains explicit and consistent with the existing CLI:

```powershell
blastradius inspect-repo C:\path\to\repository `
  --out results\repository-manifest.json `
  --force
```

Development commands:

```powershell
pytest -q tests/test_repository_acquisition.py tests/test_cli.py
pytest -q
python -m blastradius inspect-repo tests/fixtures/repositories/aws-oidc-safe --out output.json
```

The final smoke command must use a temporary output path so repository artifacts are not polluted.

## Input Contract

The positional input is one existing local directory.

The root may be a Git working tree, but Git metadata is optional for the initial module. Repository contents are always treated as untrusted data.

The initial inventory includes regular files reachable beneath the root, subject to limits and exclusions. It never executes files, imports modules from the target, invokes build tools, runs Git hooks, resolves package dependencies, expands archives, or contacts a network service.

### Default exclusions

The initial profile excludes directory entries that are implementation metadata or generated dependency/cache trees:

- `.git`
- `.venv`
- `venv`
- `node_modules`
- `dist`
- `build`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`

Every excluded top-level or nested directory encountered is represented in diagnostics by its safe relative path and exclusion reason. Exclusions are deterministic and case-insensitive on Windows.

### Safety limits

Initial defaults:

- Maximum regular files inventoried: 10,000.
- Maximum size of one file: 5 MiB.
- Maximum cumulative inventoried bytes: 100 MiB.
- Maximum relative path length: 1,024 characters.
- Maximum directory nesting beneath the root: 40 segments.

Crossing a global file-count or byte limit fails the acquisition with a controlled error; it must not silently produce a complete-looking partial manifest. Individual oversized files are recorded as skipped with their size and reason, because later parsers need explicit coverage information.

These limits belong to a versioned acquisition profile and may become CLI-configurable only in a later specification.

### Path and link behavior

- Resolve the user-supplied root once and require it to be a directory.
- Emit only normalized forward-slash relative paths.
- Reject any path that cannot be represented relative to the resolved root.
- Do not follow directory symlinks, junctions or reparse points.
- Do not read file symlinks or reparse points; record them as skipped.
- Do not rely on filename extensions to decide whether a file is safe to inventory.
- Sort traversal and output by normalized relative path.
- Reject duplicate normalized paths, including case-folded collisions on a case-insensitive platform.

## Output Contract

The manifest is canonical JSON with this shape:

```json
{
  "format_version": "0.1",
  "profile": "safe-local-v0.1",
  "source": {
    "kind": "local-directory",
    "name": "aws-oidc-safe"
  },
  "limits": {
    "max_files": 10000,
    "max_file_bytes": 5242880,
    "max_total_bytes": 104857600,
    "max_path_characters": 1024,
    "max_depth": 40
  },
  "files": [
    {
      "path": ".github/workflows/deploy.yml",
      "size": 842,
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  ],
  "skipped": [
    {
      "path": "node_modules",
      "kind": "directory",
      "reason": "excluded-directory"
    }
  ],
  "summary": {
    "file_count": 1,
    "total_bytes": 842,
    "skipped_count": 1
  },
  "snapshot_hash": "<64 lowercase hexadecimal characters>"
}
```

The manifest intentionally omits the user's absolute root path to avoid leaking workstation details into reports. The source name is the final directory name after path resolution.

`snapshot_hash` is SHA-256 over canonical manifest bytes with the `snapshot_hash` field absent. File hashes are calculated over raw bytes. Repeating acquisition over byte-identical included files with the same relative paths, exclusions and profile produces byte-identical output.

Skipped records must not include file contents, link targets, environment variables or exception text containing absolute paths.

## Project Structure

Proposed files:

```text
src/blastradius/repository/
    __init__.py          public acquisition types/functions
    acquisition.py       bounded traversal, hashing and manifest creation

tests/
    test_repository_acquisition.py
    fixtures/repositories/
        acquisition-basic/
        acquisition-limits/
        acquisition-links/

src/blastradius/cli.py   inspect-repo command wiring only
```

The target repository is data. It must never be added to `sys.path` or imported.

## Public Python Boundary

The initial internal/public boundary is deliberately small:

```python
from pathlib import Path


def acquire_repository(root: Path) -> dict:
    """Return a deterministic safe-local-v0.1 repository manifest."""
```

Expected input failures raise the existing `GraphError` until a broader domain-error hierarchy is justified. Error messages describe the category without echoing unsafe input values or absolute paths.

## Code Style

Follow the existing package style: standard library first, deterministic ordering, explicit validation, small pure helpers and controlled `GraphError` failures.

```python
def file_record(root, path):
    relative = normalized_relative(root, path)
    payload = path.read_bytes()
    return {
        "path": relative,
        "size": len(payload),
        "sha256": sha256(payload).hexdigest(),
    }
```

The implementation must not use the simplified example unchanged for large files; production code should stream file hashing and enforce byte limits before reading full content.

## Testing Strategy

Use pytest and the existing `tests/` conventions.

Unit tests must cover:

- Deterministic sorted output.
- Raw-byte SHA-256 correctness.
- Stable snapshot hash.
- Empty repository behavior.
- Unicode and spaces in filenames.
- Default directory exclusions.
- Oversized-file skipped diagnostics.
- File-count and cumulative-byte hard failures.
- Maximum depth and path-length handling.
- File symlink/reparse-point skipping.
- Directory symlink/junction non-traversal.
- No absolute paths in successful manifests or controlled errors.
- Repeated acquisition byte identity.
- Case-folded path-collision handling where the platform permits constructing the fixture.

CLI tests must cover:

- Successful stdout output when `--out` is omitted.
- Successful file output.
- Existing-output protection and `--force` behavior.
- Missing or non-directory input.
- Generic controlled errors without unsafe value echoing.

Regression verification:

- All existing 179 tests continue to pass.
- No existing conformance fixture or graph result changes.

## Boundaries

### Always do

- Treat target files and names as untrusted data.
- Keep traversal beneath the resolved root.
- Produce deterministic sorted output.
- Hash raw bytes without interpreting content.
- Report exclusions and skipped content as coverage diagnostics.
- Use controlled errors for invalid input and global-limit failures.
- Run targeted and full tests before declaring completion.

### Ask before changing

- Adding a runtime dependency.
- Invoking the Git executable or another subprocess.
- Making network requests or cloning URLs.
- Adding configurable limits or ignore rules.
- Including absolute paths in any persisted artifact.
- Changing the existing graph schema or conformance behavior.

### Never do

- Execute code, hooks, workflows, package managers, IaC tools or build scripts from the target repository.
- Follow symlinks, junctions or reparse points outside or inside the target tree.
- Read `.git` object contents as repository source.
- Print or persist file contents in the acquisition manifest.
- Claim the manifest represents deployed cloud state.
- Silently truncate after a global safety limit.

## Success Criteria

The module is complete when:

1. `blastradius inspect-repo <local-directory>` emits a deterministic canonical manifest.
2. Every included regular file has a normalized relative path, exact byte size and SHA-256.
3. Default generated/dependency directories are not traversed and are reported as excluded.
4. Links and reparse points are not followed or read and are reported as skipped.
5. Global safety-limit overflow fails closed with a controlled error.
6. Individual oversized files are explicitly reported without being read or hashed.
7. No output field exposes the supplied absolute root path.
8. The target repository is never executed and no network call occurs.
9. Targeted acquisition/CLI tests pass.
10. The complete pre-existing test suite passes unchanged.

## Open Questions for Review

1. Should ignored-but-present files be included initially, or should a future Git-aware profile honor `.gitignore`? This spec inventories the filesystem except explicit safe-profile exclusions.
2. Should an empty repository produce a valid zero-file manifest? This spec says yes because acquisition itself is defined even though downstream analysis will have no evidence.
3. Should oversized files be skipped or fail the entire acquisition? This spec skips and reports them, while global count/byte overflow fails closed.
4. Should the manifest include optional Git revision and dirty-state metadata in v0.1? This spec defers it to avoid invoking Git and to keep acquisition dependency-free.

## Approval Gate

Review and approve this input/output contract, safety behavior and four open-question defaults before implementation. Any changed decision must update this specification before code is written.
