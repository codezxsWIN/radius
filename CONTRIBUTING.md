# Contributing

Use Python 3.12+. Install pinned test extras from pyproject.toml and run `pytest --cov=blastradius --cov-report=term-missing`. Add a hand-computed fixture before changing reachability semantics. Preserve deterministic serialization, action-sensitive escalation guards, fixed denominators and actor-scoped deny behavior.

Only invented tenant exports and credential metadata belong in fixtures. Do not contribute secrets or real tenant records. Proposed live collectors must use documented GET endpoints, least-privilege permissions, pagination, throttling and explicit coverage notes; never execute escalation actions.

Code is Apache-2.0. Contributions require authorization to license the material. Metric properties remain subject to independent research review.
