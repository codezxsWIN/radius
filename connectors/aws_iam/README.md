# Bounded AWS IAM Offline Adapter

This stretch deliverable is **not a full AWS IAM or Organizations evaluator** and is not equal in coverage to a production connector. It ingests synthetic, SDK-shaped GetAccountAuthorizationDetails JSON plus an explicitly separate fixture sidecar. There is no AWS SDK dependency, live mode, authentication or account request.

```powershell
.venv/Scripts/blastradius.exe collect-aws-iam --exports connectors/aws_iam/fixtures/basic --out results/aws-tenant.json
.venv/Scripts/blastradius.exe analyze results/aws-tenant.json --out results/aws-result.json
```

The sidecar must state the full supported context: one fictional account, absent boundaries/session policies, allow-all SCP/RCP, no resource policies except account-root role trust, and no additional KMS authorization. The adapter refuses other contexts. It also rejects policy conditions, policy variables, incomplete pages and non-account-root trust. The AWS documentation permits direct same-account user trust without an additional identity allow; this adapter **rejects that distinct case** rather than applying its account-root rule incorrectly.

Supported mappings include users, direct IAM groups, roles, inline policies, default managed-policy versions, explicit denies, account-root trust plus identity permission, and explicit secret-to-credential graph links. Policy JSON may be an object or RFC3986 URL-encoded text. IAM wildcards are `*` and `?`; brackets are literal, unlike shell glob character classes.

Resource-operation catalog entries are explicit synthetic inputs, not discovered AWS assets. The fixture represents one S3 bucket with ListBucket/GetObject/PutObject outcomes and one invented Secrets Manager object with GetSecretValue. No key or secret value is present. The action strings are standard API operation names; the fixture's complete least-privilege production permission profile was not independently installed or tested. Prefix-limited/object-policy/KMS semantics outside the declared catalog are not a completeness claim.

## Hand-Computed Fixture

The universe has four pairs: bucket metadata, bucket read, bucket write, secret read. The user inherits metadata/read through a group managed policy and is denied bucket write in the user's actor context. The role has write and secret read. Account-root role trust plus a group-granted sts:AssumeRole permission lets the user assume the role in one escalation, so the user reaches all 4/4. The acquired role's write is not incorrectly removed by the user's deny. A compromised role credential alone reaches 2/4. At zero escalation steps the user reaches 2/4.

Tests separately remove identity AssumeRole permission and add a trust deny: user reach falls to 2/4. These expectations are hand-computed, not read from the adapter's generated graph. The saved expected-graph is an inspection artifact, not an independent oracle.

Official source references and every verification limitation are recorded in [manifest.json](manifest.json). General IAM policy evaluation must be completed and independently reviewed before this is used for any real account or cross-cloud comparison.
