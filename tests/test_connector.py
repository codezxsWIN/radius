from copy import deepcopy
import json
from pathlib import Path

import pytest

from blastradius.analysis import Analysis
from blastradius.connectors.entra_azure import normalize_exports, safe_id, _match, _in_scope
from blastradius.model import GraphError, canonical

SCOPE = "/subscriptions/11111111-1111-4111-8111-111111111111"
STORAGE = SCOPE + "/resourceGroups/fictional/providers/Microsoft.Storage/storageAccounts/fableledger"
VAULT = SCOPE + "/resourceGroups/fictional/providers/Microsoft.KeyVault/vaults/fablevault"


def exports():
    data = {name: [] for name in ("users", "groups", "servicePrincipals", "appRoleAssignments", "oauth2PermissionGrants", "directoryRoleAssignments", "directoryRoleDefinitions", "roleEligibilityScheduleInstances", "conditionalAccessPolicies", "armRoleAssignments", "armRoleDefinitions", "armDenyAssignments", "resources", "vaults")}
    data["metadata"] = {"synthetic": True, "organization": "Fictional Copper Meadow", "observed_at": "2026-09-09T00:00:00Z", "principal_types": {},
                         "credential_inventory": [{"id": "fictional-password-metadata", "principal_id": "fictional-user", "type": "password", "name": "Fictional Vera Glass credential metadata"}, {"id": "fictional-managed-metadata", "principal_id": "fictional-managed", "type": "federated_trust", "name": "Fictional managed metadata"}],
                         "sensitivity": {STORAGE: 0.5, VAULT: 1.0}, "application_resources": {}, "app_role_capabilities": {}, "directory_role_capabilities": {}, "pim_requirements": {}, "conditional_access_review": {}, "secret_links": []}
    data["users"] = [{"id": "fictional-user", "displayName": "Fictional Vera Glass", "createdDateTime": "2026-01-01T00:00:00Z"}]
    data["groups"] = [{"id": f"fictional-group-{index}", "displayName": f"Fictional Group {index}"} for index in range(3)]
    data["groupMembers"] = {"fictional-group-0": {"value": [{"id": "fictional-user", "@odata.type": "#microsoft.graph.user"}]}, "fictional-group-1": {"value": [{"id": "fictional-group-0", "@odata.type": "#microsoft.graph.group"}]}, "fictional-group-2": {"value": [{"id": "fictional-group-1", "@odata.type": "#microsoft.graph.group"}]}}
    data["servicePrincipals"] = [{"id": "fictional-managed", "displayName": "Fictional Quartz Identity", "servicePrincipalType": "ManagedIdentity", "appRoles": []}]
    data["resources"] = [{"id": STORAGE, "name": "fableledger", "type": "Microsoft.Storage/storageAccounts", "location": "fictional-region"}]
    data["vaults"] = [{"id": VAULT, "name": "fablevault", "type": "Microsoft.KeyVault/vaults", "location": "fictional-region", "properties": {"enableRbacAuthorization": False, "accessPolicies": [{"tenantId": "11111111-1111-4111-8111-111111111111", "objectId": "fictional-managed", "permissions": {"secrets": ["get"]}}]}}]
    definition = SCOPE + "/providers/Microsoft.Authorization/roleDefinitions/fictional-role"
    data["armRoleDefinitions"] = [{"id": definition, "properties": {"roleName": "Fictional Account Reader", "permissions": [{"actions": ["Microsoft.Storage/storageAccounts/read"], "notActions": [], "dataActions": [], "notDataActions": []}]}}]
    data["armRoleAssignments"] = [{"id": SCOPE + "/providers/Microsoft.Authorization/roleAssignments/fictional-assignment", "properties": {"principalId": "fictional-group-2", "roleDefinitionId": definition, "scope": SCOPE, "condition": None}}]
    return data


def test_offline_connector_hand_computed_reach():
    graph = normalize_exports(exports())
    result = Analysis(graph).run(False)
    records = {item["credential_id"]: item for item in result["credentials"]}
    assert result["universe_size"] == 4
    assert records["fictional-password-metadata"]["canonical_radius"] == 0.25
    assert records["fictional-password-metadata"]["sensitivity_weighted_radius"] == float(1/6)
    assert records["fictional-managed-metadata"]["canonical_radius"] == 0.25
    assert records["fictional-managed-metadata"]["sensitivity_weighted_radius"] == float(1/3)
    assert records["fictional-password-metadata"]["explanation"]["graph_hops"] == 6


def test_connector_deny_exclusions_and_scope():
    data = exports()
    data["armDenyAssignments"] = [{"id": "fictional-deny", "properties": {"scope": SCOPE, "principals": [{"id": "00000000-0000-0000-0000-000000000000", "type": "SystemDefined"}], "excludePrincipals": [{"id": "fictional-managed", "type": "ServicePrincipal"}], "doNotApplyToChildScopes": False, "permissions": [{"actions": ["Microsoft.Storage/storageAccounts/read"], "notActions": [], "dataActions": [], "notDataActions": []}]}}]
    records = {item["credential_id"]: item for item in Analysis(normalize_exports(data)).run(False)["credentials"]}
    assert records["fictional-password-metadata"]["absolute_reach"] == 0
    assert records["fictional-managed-metadata"]["absolute_reach"] == 1
    data["armDenyAssignments"][0]["properties"]["doNotApplyToChildScopes"] = True
    assert all(item["absolute_reach"] == 1 for item in Analysis(normalize_exports(data)).run(False)["credentials"])


def test_notactions_is_local_to_each_permission_block():
    permissions = [{"actions": ["*"], "notActions": ["Microsoft.Storage/*"], "dataActions": []}, {"actions": ["Microsoft.Storage/storageAccounts/read"], "notActions": []}]
    assert _match("Microsoft.Storage/storageAccounts/read", permissions, "management")
    assert not _match("Microsoft.Storage/storageAccounts/write", permissions, "management")
    assert _in_scope(STORAGE.upper(), SCOPE.lower())
    assert not _in_scope(SCOPE + "evil/resource", SCOPE)


@pytest.mark.parametrize("change", ["real", "material", "condition", "missing-role"])
def test_connector_refuses_unsupported_or_sensitive_data(change):
    data = exports()
    if change == "real": data["metadata"]["synthetic"] = False
    if change == "material": data["servicePrincipals"][0]["secretText"] = "REJECT-SENTINEL"
    if change == "condition": data["armRoleAssignments"][0]["properties"]["condition"] = "unsupported predicate"
    if change == "missing-role": data["armRoleDefinitions"] = []
    with pytest.raises(GraphError): normalize_exports(data)


def rich_exports():
    data = exports()
    data["servicePrincipals"].extend([
        {"id": "fictional-agent", "displayName": "Fictional Amber Agent", "servicePrincipalType": "Application", "appId": "22222222-2222-4222-8222-222222222222", "appRoles": []},
        {"id": "fictional-api", "displayName": "Fictional Ledger API", "servicePrincipalType": "Application", "appId": "33333333-3333-4333-8333-333333333333", "appRoles": [{"id": "fictional-reader-role", "allowedMemberTypes": ["Application"], "displayName": "Fictional ledger reader", "value": "Fictional.Ledger.Read", "isEnabled": True}]},
    ])
    metadata = data["metadata"]
    metadata["principal_types"]["fictional-agent"] = "ai_agent"
    metadata["credential_inventory"].append({"id": "fictional-agent-metadata", "principal_id": "fictional-agent", "type": "federated_trust", "name": "Fictional agent metadata"})
    metadata["application_resources"]["fictional-api"] = {"name": "Fictional Ledger API", "actions": ["read", "write"], "sensitivity": 0.8}
    metadata["app_role_capabilities"]["fictional-api:fictional-reader-role"] = [{"resource_id": "fictional-api", "actions": ["read"]}]
    metadata["directory_role_capabilities"] = {"fictional-directory-reader": [{"resource_id": "fictional-api", "actions": ["read"]}], "fictional-directory-writer": [{"resource_id": "fictional-api", "actions": ["write"]}]}
    metadata["pim_requirements"]["fictional-eligibility"] = ["approval_required"]
    metadata["conditional_access_review"]["fictional-device-policy"] = {"credentials": ["fictional-password-metadata"], "constraints": ["device_required"]}
    metadata["secret_links"] = [{"principal_id": "fictional-managed", "vault_id": VAULT, "credential_id": "fictional-agent-metadata"}]
    data["groupMembers"]["fictional-group-0"]["value"].append({"id": "fictional-agent", "@odata.type": "#microsoft.graph.servicePrincipal"})
    data["appRoleAssignments"] = [{"id": "fictional-app-assignment", "principalId": "fictional-agent", "resourceId": "fictional-api", "appRoleId": "fictional-reader-role", "createdDateTime": "2026-08-01T00:00:00Z"}]
    data["oauth2PermissionGrants"] = [{"id": "fictional-delegated", "clientId": "fictional-agent", "consentType": "AllPrincipals", "principalId": None, "resourceId": "fictional-api", "scope": "Fictional.Ledger.Read"}]
    data["directoryRoleDefinitions"] = [{"id": "fictional-directory-reader", "displayName": "Fictional Reader", "isBuiltIn": False, "rolePermissions": []}, {"id": "fictional-directory-writer", "displayName": "Fictional Writer", "isBuiltIn": False, "rolePermissions": []}]
    data["directoryRoleAssignments"] = [{"id": "fictional-directory-assignment", "principalId": "fictional-user", "roleDefinitionId": "fictional-directory-reader", "directoryScopeId": "/", "appScopeId": None}]
    data["roleEligibilityScheduleInstances"] = [{"id": "fictional-eligibility", "principalId": "fictional-agent", "roleDefinitionId": "fictional-directory-writer", "directoryScopeId": "/", "startDateTime": "2026-08-01T00:00:00Z", "endDateTime": "2027-08-01T00:00:00Z", "memberType": "Direct", "roleEligibilityScheduleId": "fictional-schedule"}]
    data["conditionalAccessPolicies"] = [{"id": "fictional-device-policy", "displayName": "Fictional device gate", "state": "enabled", "conditions": {"users": {"includeUsers": ["fictional-user"], "excludeUsers": []}, "applications": {"includeApplications": ["All"]}, "clientAppTypes": ["all"]}, "grantControls": {"operator": "AND", "builtInControls": ["compliantDevice"]}}]
    return data


def test_rich_export_all_supported_types_and_reviewed_context():
    graph = normalize_exports(rich_exports())
    default = {item["credential_id"]: item for item in Analysis(graph).run(False)["credentials"]}
    assert default["fictional-password-metadata"]["absolute_reach"] == 0
    assert default["fictional-agent-metadata"]["absolute_reach"] == 2
    assert default["fictional-managed-metadata"]["absolute_reach"] == 3
    assert all(item["universe_size"] == 6 for item in default.values())
    permissive = {item["credential_id"]: item for item in Analysis(graph, "permissive").run(False)["credentials"]}
    assert permissive["fictional-password-metadata"]["absolute_reach"] == 2
    assert permissive["fictional-agent-metadata"]["absolute_reach"] == 3
    assert permissive["fictional-managed-metadata"]["absolute_reach"] == 4
    assert any("Delegated OAuth" in note for note in graph["coverage"])


def test_pim_and_conditional_access_review_cannot_be_assumed():
    for field in ("pim_requirements", "conditional_access_review"):
        data = rich_exports()
        data["metadata"][field] = {}
        with pytest.raises(GraphError): normalize_exports(data)


def test_vault_rbac_and_access_policy_modes_are_not_combined():
    data = exports()
    definition = data["armRoleDefinitions"][0]
    definition["properties"]["permissions"][0]["dataActions"] = ["Microsoft.KeyVault/vaults/secrets/getSecret/action"]
    default = {item["credential_id"]: item for item in Analysis(normalize_exports(data)).run(False)["credentials"]}
    assert default["fictional-password-metadata"]["absolute_reach"] == 1
    assert default["fictional-managed-metadata"]["absolute_reach"] == 1
    data["vaults"][0]["properties"]["enableRbacAuthorization"] = True
    rbac = {item["credential_id"]: item for item in Analysis(normalize_exports(data)).run(False)["credentials"]}
    assert rbac["fictional-password-metadata"]["absolute_reach"] == 2
    assert rbac["fictional-managed-metadata"]["absolute_reach"] == 0


