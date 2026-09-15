# Spec: Human Repository Attack-Path Report

Module id: `repository-report`

Status: **Approved for implementation by the user's continuing build direction**

Created: 2026-09-15

## Objective

Make `repository-attack-path-v0.1` useful to a developer or reviewer without requiring them to inspect canonical JSON. Add a deterministic Markdown renderer and `--format md` to both repository analysis commands while keeping JSON as the default machine contract.

## Required Report Order

1. Repository slug and immutable public commit metadata when present.
2. Finding count and declared reachable-secret count.
3. For each finding: priority/title, explicit assumed-compromise start, concrete provider action/resource ARN, ordered path, exact source locations and confidence.
4. Remediation description, applied/not-applied state, before/after absolute reach and path-broken result.
5. Coverage, skipped archive inputs, parser diagnostics and deployed-state limitation.
6. Analysis hash.

The zero-finding report must reproduce the no-proof/not-safe conclusion prominently.

## Safety and Determinism

- Treat every repository-derived string as untrusted display text.
- Replace control characters and prevent untrusted values from creating Markdown headings, links or list structure.
- Use no HTML, remote resources, scripts or embedded repository content.
- Preserve finding/path order from the deterministic JSON contract.
- Never hide unsupported diagnostics or change confidence language.
- Rendering does not mutate the result.

## CLI Contract

```powershell
blastradius analyze-github https://github.com/owner/repository --format md
blastradius analyze-repo C:\checkout --repository-slug owner/repository --format md
```

`--format json` remains the default for backward compatibility. `--out` and `--force` retain existing behavior.

## Acceptance Tests

1. A positive report contains the exact assumption, path kinds, source `path:line:column`, impact and before/after remediation result.
2. A zero-finding report states that no complete path was proven and this is not evidence of safety.
3. Control characters and Markdown metacharacters in untrusted fields cannot create new report structure.
4. Rendering is deterministic and non-mutating.
5. Both repository CLI commands support Markdown output; all existing JSON tests remain unchanged.
