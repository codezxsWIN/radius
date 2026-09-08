# Offline Entra/Azure Adapter

```powershell
.venv/Scripts/blastradius.exe collect-entra-azure --exports connectors/entra_azure/fixtures/rich --out results/connector-tenant.json
.venv/Scripts/blastradius.exe analyze results/connector-tenant.json --out results/connector-result.json
.venv/Scripts/blastradius.exe report results/connector-result.json --format md --out results/connector-report.md
```

Each API collection is a fully materialized `{ "value": [...] }` export. `groupMembers.json` groups those envelopes by source group ID; it is a bundle convention, not a Graph endpoint response. Metadata in the explicitly separate `metadata.json` is not misrepresented as an API property. It provides fictional classification, credential metadata inventory and reviewed capability/constraint mappings. Incomplete pagination and credential-material fields fail ingestion.

UUID-shaped identifiers in the saved fixtures are deterministic fictional UUID5 values, not tenant identifiers. Names and organization are visibly fictional. Source response shapes follow the documented Graph and ARM models; no API response was collected from a tenant.

## Independent Expected Results

Basic: two resources each declare two actions, making four pairs. The fictional user's three-level group inheritance grants storage metadata read only, 1/4. The managed identity's vault access policy grants secret read only, 1/4. Sensitivities are storage 0.5 and vault 1.0, so denominator = 2*0.5 + 2*1 = 3; their weighted radii are 1/6 and 1/3.

Rich adds an application with read/write inventory, making six pairs. The default device constraint blocks the user's password authenticator, yielding 0/6. The agent has storage metadata read plus explicitly mapped API read, yielding 2/6. The managed identity can read the vault secret, obtain that specific agent credential, and inherit its two pairs, yielding 3/6. Under permissive constraints the user reaches 2/6, the agent activates approved API write to reach 3/6, and the managed identity reaches 4/6. Delegated consent itself adds no app-only grant.

The expected-graph files are generated adapter outputs for inspection; they are **not** the independent oracle. Independent expected cardinalities and weighted arithmetic are asserted in tests/test_connector.py and derived above. Run `pytest tests/test_connector.py tests/test_transport.py`.

Read [PERMISSIONS.md](PERMISSIONS.md) and [manifest.json](manifest.json) for the supported scope and all unverified references. Live transport is mock-tested only, disabled by default, and not a supported real-tenant analysis workflow.
