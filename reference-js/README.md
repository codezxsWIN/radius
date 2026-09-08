# JavaScript Reference Experiment

Apache-2.0. A second-language implementation of the same exact public contract, written in this session by the same contributor; this is implementation diversity, NOT independent authorship or external validation. It does not invoke Python or load expected fixture values when calculating a response.

Requires Node with JSON.parse source-context support (tested with25.8.1). No package manager, npm dependency, network access or build step is needed. It uses BigInt rational arithmetic and whole-edge state relaxation, a distinct implementation from the optimized Python priority queue. Input validation implements the specific keyword subset used by the bundled schema, not a general JSON Schema library. Future schema keywords require explicit validation support and review.

```powershell
node reference-js/verify.mjs
.venv/Scripts/blastradius.exe conformance run --tool 'node reference-js/reference.mjs' --out conformance/reports/javascript
```

The legacy graph hash distinguishes integer1 and float1.0. The adapter therefore retains numeric source tokens and reproduces the explicitly specified v0.1 finite-float serialization. Decimal tokens that lose value in binary64 are rejected rather than silently rounded; integer source tokens are preserved using BigInt. Native parsing validates syntax first, then a token-scope pass rejects repeated decoded property names, including escaped aliases. This compatibility profile should be reviewed before a final standard. The conformance suite, not this README, records actual pass/fail status; passing its finite corpus does not certify complete parser equivalence or every schema edge case.
