# Blast Radius

**Learn what a credential can reach, then test a change without touching a cloud account.**

Blast Radius combines an offline authorization lesson, an inspectable graph lab, and an optional local repository analyzer. A declared capability is not automatically a vulnerability. Least privilege means preserving required work while removing unnecessary access, not making every permission count zero.

## Start Here

Open [ui/index.html](ui/index.html) from a downloaded checkout. No installation, server, cloud credentials, or network connection is required. GitHub shows HTML source; the included file is meant to open locally in your browser.

The first lesson uses a five-node fictional graph and three predict-change-explain exercises:

1. Predict the credential's reach: one granted read among four possible resource-action pairs.
2. Remove the grant: reach becomes zero, but the required read no longer works.
3. Add write, then remove only write: the required read survives without the unnecessary action.

Fictional lesson answers/progress are stored locally and can be reset or exported. **Advanced graph lab** opens the existing metrics, models, and Playground. Playground model changes preserve the edited graph, including invalid text; reset is explicit. Synthetic result v0.1 imports and repository reports are different contracts and are not interchangeable.

The lesson is also included in the Python wheel: `python -I -m blastradius learn`. It is an educational model, not live-cloud verification. Actual newcomer comprehension still needs user testing.

## Optional Analyzer

Use repository review only when you want to inspect actual source declarations. It accepts a local checkout plus its GitHub slug, or an explicitly supported public GitHub URL. Target source is data: workflows, Terraform, hooks, and dependencies are never executed.

Requirements: Python **3.12 or newer**, pip, and the pinned dependencies in [pyproject.toml](pyproject.toml). From this project directory on Windows:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -I -m blastradius review
```

On macOS/Linux, use `python3` and `.venv/bin/python`. Skip environment creation when a working environment exists. If that environment has no pip, run its Python with `-m ensurepip` first, or use `uv pip install --python <environment-python> .`. Do not delete or overwrite an environment to repair it. Installation may need registry access; the offline lesson does not.

The app opens at <http://127.0.0.1:8765/>. Use `--port 8766` if occupied; no other process is stopped. [start-review.cmd](start-review.cmd) diagnoses a missing/incomplete environment and offers the offline lesson instead. The installed app serves the same lesson at `/learn`.

Reviews expose source evidence, declared paths, identities, coverage gaps, and modeled trust-removal comparisons. There is no blanket high-priority score or claim that removal is minimally disruptive. Known alternate routes are preserved; excluded alternatives remain visible as **remaining access unknown**, even when modeled reach is zero.

Analysis reports real stages, supports cooperative cancellation, and has a 120-second analysis deadline. Cancellation waits for a bounded read/checkpoint, never publishes a partial result, and is not forced thread termination. Bundled-example review state survives refresh. Real repository state is not written to browser storage; leaving warns about losing the visible session. Download reports explicitly before discarding a real review.

## Supported Inputs

| Input | Assessed | Not Assessed |
| --- | --- | --- |
| GitHub Actions | Exact branch OIDC, finite matrices, literal env/matrix context | Arbitrary expressions, local action behavior, environment subjects, secret values |
| CloudFormation JSON/YAML | Literal IAM role trust, finite Secrets Manager reads, same-template literal policy attachments | Intrinsic evaluation, unresolved restrictions, full policy composition |
| Terraform JSON | Literal IAM role and inline policy declarations in one module file | HCL, expressions, state/plans, cross-file IAM joins, provider execution |

Metadata-only Terraform JSON files do not erase otherwise supported evidence. Multiple relevant declarations or HCL in the same module remain incomplete; HCL counts are explicit. Do not restructure real infrastructure merely to fit this tool.

**Zero findings means no complete path was proven within this profile, not that the repository is safe.** Deployed permissions, required workload access, exploitability, and policy violations require additional evidence. Source reports can contain sensitive names/ARNs/paths; they are not anonymized. Read [SECURITY.md](SECURITY.md) before analyzing or sharing real source.

## Export and CI

```powershell
.venv/Scripts/python.exe -I -m blastradius analyze-repo C:/work/payments --repository-slug acme/payments --out C:/reports/payments.json
.venv/Scripts/python.exe -I -m blastradius render-repo C:/reports/payments.json --format html --out C:/reports/payments.html
```

Formats: JSON, Markdown, HTML and SARIF. Saved HTML works offline, including its recorded single-statement comparison. Arbitrary multi-control recomputation needs the local app. Result hashes check integrity, not authorship. Reports must be outside the analyzed checkout; replacing one requires `--force`. `--fail-on-findings` is an opt-in declaration gate, not a vulnerability verdict.

[Repository-review CI](.github/workflows/repository-review.yml) installs the analyzer from the immutable **trusted base revision** and treats the PR checkout only as data. Preserve `-I`, pinned actions, read-only permissions and the separate opt-in manual SARIF job. Never install or execute the target PR as the analyzer. This workflow is distinct from the project's ordinary unprivileged test workflow.

## Verify Changes

```powershell
.venv/Scripts/python.exe -m pip install -e ".[test]"
.venv/Scripts/python.exe -B tools/verify.py
node tools/build_ui.mjs --check
node tools/test_ui_contract.mjs
node tools/test_ui_browser.mjs
node tools/test_repository_review.mjs
```

Developer checks require Node 25+ and Chromium; set `BR_BROWSER` if it is not discovered, and `BR_PYTHON` to the project interpreter when needed. No JavaScript registry installation is needed. After UI source edits, run `node tools/build_ui.mjs`; never edit generated HTML directly. CI checks parity, installed lesson completion, model/edit continuity, browser failures and a bounded repository-shaped performance budget.

## Further Reading

- [Current architecture](ARCHITECTURE.md) and [direction](DIRECTION.md)
- [Contributing](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md), and [licensing](LICENSING.md)
- [Hand-computed fixtures](tests/fixtures/README.md) and [metric specification](spec/METRIC_SPECIFICATION_v1.0-draft.md)
- [Educational audit](reviews/2026-09-17-educational-audit.md) and [verification record](TEST_REPORT.md)
- [Historical handover](HANDOVER.md), [decisions](DECISIONS.md), and [research methodology](PRIVACY_ANALYSIS.md)

The package is `blastradius` in this nested Git repository. The surrounding workspace's older `blast_radius` package and the historical dashboard are not the current quickstart. This project is unrelated to the Blast-RADIUS RADIUS/UDP vulnerability. Code is Apache-2.0; specification/schema and data have separate terms in the licensing policy.
