# Spec: Safe Public GitHub URL Input

Module id: `public-github-input`

Status: **Approved for implementation by the user's continuing build direction**

Created: 2026-09-15

## Objective

Let a user run the existing repository attack-path analysis directly against a public `https://github.com/owner/repository` URL without installing Git, uploading source to Blast Radius, executing repository code, or granting an account token.

```powershell
blastradius analyze-github https://github.com/owner/repository --ref main
```

The tool resolves the requested ref to an immutable commit through GitHub's public REST API, downloads that commit's source ZIP through GitHub's archive endpoint, extracts it into a temporary local directory under strict limits, runs `analyze_repository`, attaches immutable source metadata, and deletes the temporary files.

## Supported Input

- HTTPS `github.com` repository URLs only.
- Exactly two path segments: owner and repository; an optional `.git` suffix and trailing slash are normalized away.
- No username/password, custom port, query, fragment or alternate host.
- Owner/repository must satisfy the existing bounded slug grammar.
- Optional non-empty `--ref`; omitted ref resolves `HEAD`.
- Public repositories only. No token, cookie, credential helper or ambient Git configuration is read.

## Network Boundary

- Resolve a commit using `GET /repos/{owner}/{repo}/commits/{ref}` on `api.github.com`.
- Validate the returned SHA-1 commit identifier.
- Request `GET /repos/{owner}/{repo}/zipball/{commit_sha}` on `api.github.com`.
- Accept one HTTPS redirect only when its target host is exactly `codeload.github.com`, with no credentials or custom port.
- Download no more than 25 MiB of compressed archive bytes.
- Use a fixed user agent, GitHub JSON media type and bounded timeout.
- Do not follow arbitrary redirects and do not contact any host derived from repository content.

GitHub documents that public commit lookup can be unauthenticated, archive downloads redirect, and commit-ID archives provide stable extracted contents even if branch/tag names later move.

## Archive Boundary

- ZIP only; reject malformed, encrypted, unsupported-compression and multi-root archives.
- Reject absolute paths, `..`, backslashes, drive/ADS colon syntax, NULs, Windows reserved names, trailing-dot/space segments, links and non-regular entries.
- Reject duplicate paths using case-insensitive keys for cross-platform determinism.
- Enforce the acquisition profile's path depth/length, 10,000-file, 5 MiB-per-file and 100 MiB-total uncompressed limits before and during extraction. As in local acquisition, files above the per-file limit are not decompressed or written and are reported as skipped; aggregate/count limit violations reject the archive.
- Stream each member and verify actual bytes match declared size; never call `extract`/`extractall`.
- Extract beneath a fixed `repository` directory inside an automatically cleaned temporary directory.

## Result Contract

Reuse `repository-attack-path-v0.1` and add `repository.input`:

- `kind: public-github-url`
- normalized URL
- requested ref (`HEAD` when omitted)
- resolved commit SHA
- downloaded archive SHA-256
- extraction counts and explicit oversized-file skips

Recompute `analysis_hash` after attaching input metadata. Repository findings, diagnostics, no-proof language and deployed-state limitations remain unchanged.

## Explicit Non-Goals

- Private repositories or authentication tokens.
- GitHub Enterprise Server/custom hosts.
- Pull request merge refs or Git object checkout.
- Git history, submodules, Git LFS, release assets or signature verification.
- Server-side repository upload/storage.
- Running Git, hooks, filters, package managers, workflows or source code.

## Acceptance Tests

1. Strict URL parsing accepts canonical public repository URLs and rejects host/credential/port/path/query confusion.
2. A fake GitHub transport proves commit pinning, one allowed redirect and bounded archive download.
3. A fixture archive produces the same supported finding flow and immutable source metadata.
4. Zip-slip, links, duplicate paths, excessive sizes and unapproved redirects fail closed.
5. Temporary extracted source is unavailable after analysis returns.
6. CLI emits deterministic JSON through stdout/protected output.
7. Existing local input and synthetic v0.1 tests remain green.

## References

- [GitHub REST API: get a commit](https://docs.github.com/en/rest/commits/commits#get-a-commit)
- [GitHub REST API: download a repository archive](https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-zip)
- [GitHub: downloading source code archives and commit-ID reproducibility](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)
