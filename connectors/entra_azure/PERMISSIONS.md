# Entra ID and Azure Read-Only Contract

**No real tenant was contacted.** The CLI supports only synthetic offline ingestion. The separately implemented library transport is disabled by default, accepts only documented GET collection routes, refuses redirects, validates pagination origin/path, caps pages and response sizes, and retries only transient failures. Its tests use generated ephemeral dummy authentication objects and fake HTTP responses, never real credentials.

## Endpoint and Application Permission Inventory

Microsoft Learn was searched and the principal API reference pages were fetched during this session. Exact paths, verification labels, references and mapping dispositions are in [manifest.json](manifest.json). Graph base is `https://graph.microsoft.com/v1.0`; ARM base is `https://management.azure.com`. No client secret or token is accepted as a CLI argument.

| Collection | Least Documented Application Read Permission / Read Profile | Verification |
| --- | --- | --- |
| Users | `User.Read.All` | Verified in fetched List users reference |
| Groups | `GroupMember.Read.All` is a documented supported read-only option | Exact minimum is not asserted: current documentation lists several granular options; never request a read-write permission merely because a table lists it first |
| Direct group members | `GroupMember.ReadBasic.All`; `Member.Read.Hidden` additionally for hidden memberships | Verified in fetched List group members reference; object detail needs its respective read permission |
| Service principals and their appRoleAssignments | `Application.Read.All` | Verified in search and fetched app-role reference |
| oauth2PermissionGrants | `Directory.Read.All` | Verified; this broader permission is only needed if delegated-grant inventory is collected |
| Directory roleAssignments | `RoleManagement.Read.Directory` | Verified; read-only alternatives are listed in the reference |
| Directory roleDefinitions | `RoleManagement.Read.Directory` | Unverified endpoint/permission pair in this session; candidate documented in manifest, not live-tested |
| roleEligibilityScheduleInstances | `RoleEligibilitySchedule.Read.Directory` | Verified |
| Conditional Access policies | `Policy.Read.All` | Verified |
| ARM roleAssignments / roleDefinitions | `Microsoft.Authorization/roleAssignments/read`, `Microsoft.Authorization/roleDefinitions/read` | Endpoints verified; exact minimal custom-role bundle unverified in-session |
| ARM denyAssignments | `Microsoft.Authorization/denyAssignments/read` | Verified in the fetched deny documentation |
| ARM resources | Read-only `Reader` at the authorized scope | Resource-list endpoint/version verified; exact minimal custom-role bundle unverified in-session |
| ARM vault inventory / access policy metadata | `Microsoft.KeyVault/vaults/read`, included in management-plane Reader | List-by-subscription endpoint verified at API version 2024-11-01; no data-plane secret permission requested |

Application permissions need administrator consent in an authorized lab. Do not blindly grant the union: omit optional collections to reduce privileges and review the actual minimal profile. Graph permissions do not grant Azure Resource Manager RBAC, and ARM Reader does not grant Key Vault data-plane secret access. No roles or permissions are assigned by this prototype.

## Important API Limits

- Microsoft Learn explicitly documents a v1.0 `/groups/{id}/members` issue that omits service principals. The documented alternatives are beta or a group `$expand=members` query; neither workaround is silently enabled. The live collector therefore reports incomplete membership coverage. Transitive membership is computed locally from complete exported direct membership; group nesting depth is preserved.
- Hidden memberships need additional read permission. Limited member objects may provide only ID and type. An incomplete export is rejected, not scored as a complete tenant.
- App-role IDs are not universally meaningful actions. A role named Reader does not prove a particular API operation. The synthetic sidecar explicitly maps app-role and directory-role IDs to capability pairs; those mappings are fixture semantics, not guessed Microsoft semantics.
- A delegated OAuth consent record is not an application permission. It is inventoried in coverage notes without inventing a signed-in-user or token context.
- PIM eligibility does not reveal all activation controls. Validity windows are checked; a reviewed sidecar constraint list is mandatory, and missing approval context fails ingestion. General role-management-policy evaluation remains deferred.
- Enabled Conditional Access policies require explicit fixture review of authentication-stage applicability. `mfa` alone is not treated as proof of possession of a second device. General policies, OR controls, authentication strengths, sessions, claims and application-specific predicates are not evaluated.
- ARM actions and dataActions are kept separate. NotActions/notDataActions subtract only within their permission block, not globally. Denies subtract across grants for the affected actor and respect exclusions and inheritance. Conditional role assignments are rejected.
- Vault access policies are ignored in RBAC mode, and RBAC secret data grants are not applied in access-policy mode. Metadata read never acquires a secret. Secret-to-credential links are invented and explicit; no secret-store contents are fetched.

## Live Transport Contract

`blastradius.connectors.transport.ReadOnlyTransport` accepts a caller-supplied object with a `get_token(scope)` method, compatible with a reviewed Azure Identity credential provider. Hosted use should prefer managed identity; a lab may use an approved interactive/workload identity provider. No SDK version is silently installed and no provider is constructed or invoked against a tenant in this session.

Its implemented `collect(subscription_id)` reads the allowlisted Graph collections, per-group memberships, per-service-principal app roles and subscription ARM collections. It returns an in-memory bundle explicitly marked `synthetic: false`, which the prototype normalizer refuses. There is no live CLI flag and no live-result persistence. This deliberate boundary must not be bypassed by relabeling data.

This is an implemented, mock-tested transport code path, **not** a fully validated live connector. Production authentication setup, encrypted persistence, real group completeness, policy evaluation, error bounds and tenant conformance are deferred. All endpoint existence claims are documentation-based only. Read-only does not mean the collected identity graph is nonsensitive.

## References

- [Graph users](https://learn.microsoft.com/graph/api/user-list?view=graph-rest-1.0)
- [Graph group members and known issue](https://learn.microsoft.com/graph/api/group-list-members?view=graph-rest-1.0)
- [Service principal app roles](https://learn.microsoft.com/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0)
- [OAuth delegated grants](https://learn.microsoft.com/graph/api/oauth2permissiongrant-list?view=graph-rest-1.0)
- [Directory role assignments](https://learn.microsoft.com/graph/api/rbacapplication-list-roleassignments?view=graph-rest-1.0)
- [PIM eligibility instances](https://learn.microsoft.com/graph/api/rbacapplication-list-roleeligibilityscheduleinstances?view=graph-rest-1.0)
- [Conditional Access policies](https://learn.microsoft.com/graph/api/conditionalaccessroot-list-policies?view=graph-rest-1.0)
- [ARM role assignments](https://learn.microsoft.com/azure/role-based-access-control/role-assignments-list-rest)
- [ARM role definitions](https://learn.microsoft.com/azure/role-based-access-control/role-definitions-list)
- [Azure denies](https://learn.microsoft.com/azure/role-based-access-control/deny-assignments)
- [ARM resource inventory](https://learn.microsoft.com/rest/api/resources/resources/list?view=rest-resources-2021-04-01)
- [Key Vault management inventory](https://learn.microsoft.com/rest/api/keyvault/keyvault/vaults/list-by-subscription?view=rest-keyvault-keyvault-2024-11-01)
- [Key Vault data operations, including readMetadata versus getSecret](https://learn.microsoft.com/azure/role-based-access-control/permissions/security#microsoftkeyvault)
