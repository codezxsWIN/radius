# Security

This build permits synthetic data only. Fictional markers are a use contract, not proof that a relabeled input is harmless. No live tenant is contacted during this session; credential nodes carry metadata, never credential values.

Local synthetic results are plaintext. HMAC-SHA256 signing uses an OS-random local key stored outside the project and excluded from checkpoints. Verifiers holding that key can also forge results: this is local tamper detection, not public attestation or protection against a compromised host. Production signing-key custody, encrypted tenant persistence and private disclosure channels require review before any real tenant workflow.

Keep generated keys private. Never store keys in fixtures, repositories, demo HTML, OneDrive artifacts or report bodies. Signed reports disclose synthetic graph structure intentionally. Real tenant input is not supported. The future read-only transport is testable offline and is not a production collection claim.

No dedicated vulnerability-reporting address has been established. Use a previously verified private maintainer channel for sensitive reports; do not post secrets in issues or chats.

Public conformance executes an operator-supplied command with the operator's privileges; it is not a sandbox. Fixture hashes, contained paths, timeouts and output checks protect evaluation integrity, not a host from malicious local programs. Run third-party adapters only in an appropriate isolated environment. The captured-output limit is checked after process execution, not a hard streaming memory cap.

Structural summaries are explicitly not anonymous. The discrete-noise aggregate experiment is synthetic-only, and its public seed provides no privacy for real input. A production release requires independent review, durable contribution/budget enforcement, secret randomness and neutral custody. No real upload endpoint or management service is implemented.
