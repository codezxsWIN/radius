# Standards Session Release Record

Session began 2026-09-09 at 03:30:10 India time. This record follows verified implementation, source review and packaging; exact final save time and ZIP digest are in the generated OneDrive SAVE_RECEIPT.json. No cloud synchronization, remote repository publication, neutral-host admission or real-data release is claimed.

## Committed Artifacts

- `51cb0d1`: candidate specification, frozen conformance/reference report, synthetic privacy/NHI study, sourced reconstruction and governance/paper artifacts.
- `47c8df7`: JavaScript reference and report, bounded Kubernetes adapter, numeric/runner hardening, final-source review, executed rank countermodels and complete artifact including the unchanged demo.
- The current record is an evidence-only follow-up. The runtime code tested by the final wheel is the code in `47c8df7`; subsequent documentation does not imply a new code release.

Git identity came from the existing local configuration; no identity, coauthor or institutional approval was fabricated. No remote was configured. A temporary local clone passed all 42 release checks and all 120 JavaScript corpus cases. Hash-sensitive fixtures preserve LF; the two pre-data protocol documents retain their original CRLF bytes with explicit no-conversion rules.

## Actual Gates

| Gate | Result |
| --- | --- |
| Python integrated tests | 179 passed in 39.07 seconds |
| Python line coverage | 1641/1757 statements; 93.397837%; no branch/JavaScript coverage claim |
| Python public conformance | 120/120, two executions each |
| JavaScript public conformance | 120/120, two executions each |
| Clean installed wheel | 120/120 isolated Python cases outside source tree; Kubernetes normalization passed |
| Kubernetes bounded-profile tests | 17 passed; unbounded 4/6 and 3/6, zero-step 3/6 each |
| Public artifact audit | 42 checks, 38 required artifacts; clean clone also passed |
| Source archive | 315 members at final runtime build; required contents/exclusions passed |
| Reconstruction | 30 baseline/control/model outputs plus 10 executed rank countermodels |
| Synthetic privacy | 500/500 exact summaries unique; 161/500 rounded unique |
| Selected aggregate utility | epsilon ln2, k target10, noisy threshold20; mean count MAE1.014762, support retained96.8% across200 trials |
| NHI joint outcomes | null54/500; NHI-broader250/500; human-broader54/500; no real inference |

Public conformance revision2 digest: `9dc834236ba7cd22c9878705447117c3cc0625ffcb23d7327b57a9456403bfc4`.

Final tested wheel: `dist/blastradius_prototype-0.1.0-py3-none-any.whl`, SHA-256 `61d42e1a466a9e354a83de2146b0548578bbe0c0de226e1ff213493eb019e378`.

Source archive built with that wheel: `dist/blastradius_prototype-0.1.0.tar.gz`, SHA-256 `41079e0e0ecc37c1a3d2e33abebe1165fa9161daad220eeb9f41ebfeb80da6ca`. It contains the final runtime and main documents; this later receipt is included in the full checkpoint ZIP and Git rather than retroactively changing that tested distribution.

Preserved demo SHA-256: `3a73122a30a84d31732e33454ede34b65767f4ed2e1af4f18ba2fb979f869408`. Its original contents were neither regenerated nor edited in the standards session.

## Reproduction

From the project directory, run `python tools/verify.py`, `blastradius conformance run --tool 'python -B -m blastradius conformance adapter'`, `node reference-js/verify.mjs`, `python tools/build_reconstructions.py` and `python tools/run_research.py`. The research runner refuses changed protocol hashes. Use the project virtual environment or install the tested wheel; no npm, private HMAC key or cloud account is needed for public conformance.

`python tools/audit_release.py --zip PATH --sdist dist/blastradius_prototype-0.1.0.tar.gz` checks checkpoint bytes against the current required files and scans archive paths for excluded material. The final receipt additionally records SHA-256 and byte size. Local OneDrive writes are verified, not cloud upload status.

## Unmet External Requirements

No verified empirical tenant-parameter distributions were found, so generator ranges are openly investigator-designed. The planned real NHI primary test cannot be computed from the current histogram-only payload. No independently authorized red-team ground truth, independent formal/privacy review, elected steering group, private reporting channel, neutral institutional home, real dataset or public DOI exists.

EuroS&P 2027 and CCS 2027 paper deadlines were not published in the retrieved official pages; CCS conference dates were available, not submission dates. OpenSSF's default specification/data licensing differs from CC-BY/CC0, requiring explicit acceptance or a different neutral home. These are documented decisions for Amit and prerequisites for further work, not hidden completed goals.
