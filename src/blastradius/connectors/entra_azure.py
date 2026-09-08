"""Synthetic Graph/ARM export normalization. No live API calls occur here."""

from datetime import datetime
from fnmatch import fnmatchcase
from hashlib import sha256
import json
from pathlib import Path

from ..model import GraphError, normalized, validate
from ..synthetic import Builder

COLLECTIONS = (
    "users", "groups", "servicePrincipals", "appRoleAssignments", "oauth2PermissionGrants",
    "directoryRoleAssignments", "directoryRoleDefinitions", "roleEligibilityScheduleInstances",
    "conditionalAccessPolicies", "armRoleAssignments", "armRoleDefinitions", "armDenyAssignments", "resources", "vaults",
)
OPERATIONS = {
    "microsoft.storage/storageaccounts": (("Microsoft.Storage/storageAccounts/read", "read_metadata", "management"), ("Microsoft.Storage/storageAccounts/write", "write", "management")),
    "microsoft.keyvault/vaults": (("Microsoft.KeyVault/vaults/read", "read_metadata", "management"), ("Microsoft.KeyVault/vaults/secrets/getSecret/action", "read_secret", "data")),
}


def safe_id(prefix, value):
    return prefix + sha256(value.encode("utf-8")).hexdigest()[:24]


def reject_material(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"secrettext", "password", "access_token", "refresh_token", "client_secret", "privatekey", "authorization", "secretaccesskey", "accesskeyid", "sessiontoken", "token", "secret", "key"}:
                raise GraphError("Export contains unsupported credential material; values are not echoed.")
            reject_material(child)
    elif isinstance(value, list):
        for child in value: reject_material(child)


def read_exports(folder):
    folder = Path(folder)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("synthetic") is not True or not metadata.get("organization", "").startswith("Fictional "):
        raise GraphError("The export adapter accepts marked fictional fixtures only.")
    bundle = {"metadata": metadata}
    for name in COLLECTIONS:
        path = folder / f"{name}.json"
        if not path.exists():
            raise GraphError(f"Required export collection is missing: {name}.")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("value"), list) or value.get("@odata.nextLink") or value.get("nextLink"):
            raise GraphError(f"Export {name} must contain a fully materialized value collection, not an incomplete page.")
        bundle[name] = value["value"]
    bundle["groupMembers"] = json.loads((folder / "groupMembers.json").read_text(encoding="utf-8"))
    reject_material(bundle)
    return bundle


def _match(operation, permissions, plane):
    allow_key, exclude_key = ("actions", "notActions") if plane == "management" else ("dataActions", "notDataActions")
    return any(any(fnmatchcase(operation.lower(), pattern.lower()) for pattern in permission.get(allow_key, [])) and not any(fnmatchcase(operation.lower(), pattern.lower()) for pattern in permission.get(exclude_key, [])) for permission in permissions)


def _in_scope(identifier, scope, no_children=False):
    identifier, scope = identifier.rstrip("/").lower(), scope.rstrip("/").lower()
    return identifier == scope or (not no_children and identifier.startswith(scope + "/"))


def ingest(folder):
    return normalize_exports(read_exports(folder))


def normalize_exports(bundle):
    reject_material(bundle)
    metadata = bundle["metadata"]
    if metadata.get("synthetic") is not True:
        raise GraphError("Only synthetic exports are accepted.")
    builder = Builder(metadata["organization"])
    builder.graph["observed_at"] = metadata["observed_at"]
    builder.graph["coverage"] = [
        "Offline synthetic Graph/ARM normalization; endpoints were documented, not called against a tenant.",
        "Resource granularity is storage account / vault / explicitly mapped application object, never per blob.",
        "Operation vocabulary is deliberately finite. Unknown resource types and operations are reported, not assumed to grant canonical actions.",
        "Credential inventory, resource sensitivities, AI/workload classification, app/directory-role semantics and PIM approval context are explicit synthetic sidecar inputs, not invented API fields.",
        "Graph v1.0 direct group-members API has a documented service-principal omission; live completeness requires a reviewed workaround and pagination.",
    ]
    subject_ids, resource_ids, resource_objects = {}, {}, {}

    def provenance(collection, identifier):
        return {"connector": "entra-azure-offline-v0.1", "source_api": collection, "observed_at": metadata["observed_at"], "evidence_ref": identifier}

    def add_node(identifier, kind, subtype, name, collection, **attributes):
        builder.node(identifier, kind, subtype, name, **attributes)
        builder.graph["nodes"][-1]["provenance"] = provenance(collection, identifier)

    def add_binding(identifier, subject, grants, collection, eligible=False, constraints=(), effect="allow"):
        builder.binding(identifier, subject, grants, constraints, eligible, effect)
        for node in builder.graph["nodes"]:
            if node["id"] == identifier: node["provenance"] = provenance(collection, identifier)
        for edge in builder.graph["edges"]:
            if identifier in (edge["source"], edge["target"]): edge["provenance"] = provenance(collection, edge["id"])

    for collection, subtype in (("users", "human_user"), ("groups", "group"), ("servicePrincipals", "service_principal")):
        for record in bundle[collection]:
            identifier = safe_id("principal-", record["id"])
            if record["id"] in subject_ids:
                raise GraphError("Duplicate exported principal ID.")
            subject_ids[record["id"]] = identifier
            actual_type = "managed_identity" if record.get("servicePrincipalType") == "ManagedIdentity" else subtype
            actual_type = metadata.get("principal_types", {}).get(record["id"], actual_type)
            add_node(identifier, "principal", actual_type, record["displayName"], collection, provisioned_at=record.get("createdDateTime"))
    for inventory in metadata["credential_inventory"]:
        subject = subject_ids.get(inventory["principal_id"])
        if subject is None: raise GraphError("Synthetic credential inventory has an unknown principal.")
        add_node(inventory["id"], "credential", inventory["type"], inventory["name"], "synthetic-sidecar:credential_inventory", principal_id=subject)
        builder.edge("auth-" + inventory["id"], "authenticates_as", inventory["id"], subject)
    memberships = []
    for group_id, page in bundle["groupMembers"].items():
        if group_id not in subject_ids or page.get("@odata.nextLink"):
            raise GraphError("Group membership export is incomplete or refers to an unknown group.")
        for member in page["value"]:
            if member["id"] not in subject_ids: raise GraphError("Group member is outside the exported principal inventory.")
            memberships.append((member["id"], group_id))
            builder.edge(safe_id("member-", member["id"] + ":" + group_id), "member_of", subject_ids[member["id"]], subject_ids[group_id])

    def member_actors(identifier):
        found = {identifier}
        while True:
            expanded = found | {member for member, group in memberships if group in found}
            if expanded == found: break
            found = expanded
        groups = {item["id"] for item in bundle["groups"]}
        return found - groups

    for kind in ("device_required", "approval_required", "network_restriction", "time_window", "pim_eligible"):
        add_node(kind, "constraint", kind, "Fictional " + kind, "synthetic-sidecar:constraint-model")
    all_resources = {item["id"]: item for item in bundle["resources"]}
    all_resources.update({item["id"]: item for item in bundle["vaults"]})
    for external, record in sorted(all_resources.items()):
        operations = OPERATIONS.get(record["type"].lower())
        if operations is None:
            builder.graph["coverage"].append(f"Unsupported resource type omitted from modeled universe: {record['type']}.")
            continue
        sensitivity = metadata.get("sensitivity", {}).get(external)
        if sensitivity is None: raise GraphError("Every modeled resource requires an explicit synthetic sensitivity classification.")
        identifier = safe_id("resource-", external)
        resource_ids[external], resource_objects[external] = identifier, record
        add_node(identifier, "resource", "secret_store" if record["type"].lower() == "microsoft.keyvault/vaults" else "storage_account", "Fictional " + record["name"], "ARM/resources", actions=sorted({entry[1] for entry in operations}), sensitivity=sensitivity)
    for external, specification in metadata.get("application_resources", {}).items():
        identifier = safe_id("resource-", external)
        resource_ids[external] = identifier
        add_node(identifier, "resource", "application", specification["name"], "synthetic-sidecar:application_resources", actions=specification["actions"], sensitivity=specification["sensitivity"])

    def operation_grants(scope, permissions, no_children=False):
        grants = []
        for external, record in resource_objects.items():
            if _in_scope(external, scope, no_children):
                actions = {
                    canonical for operation, canonical, plane in OPERATIONS[record["type"].lower()]
                    if not (plane == "data" and record["type"].lower() == "microsoft.keyvault/vaults" and not record.get("properties", {}).get("enableRbacAuthorization", False))
                    and _match(operation, permissions, plane)
                }
                if actions: grants.append((resource_ids[external], sorted(actions)))
        return grants

    definitions = {item["id"].lower(): item["properties"] for item in bundle["armRoleDefinitions"]}
    for assignment in bundle["armRoleAssignments"]:
        properties = assignment["properties"]
        if properties.get("condition"): raise GraphError("Conditional ARM role assignments require reviewed predicate semantics; not normalized as unconditional allows.")
        definition = definitions.get(properties["roleDefinitionId"].lower())
        subject = subject_ids.get(properties["principalId"])
        if definition is None or subject is None: raise GraphError("ARM assignment has missing definition or principal.")
        add_binding(safe_id("arm-", assignment["id"]), subject, operation_grants(properties["scope"], definition["permissions"]), "ARM/roleAssignments")
    all_actors = set(subject_ids) - {item["id"] for item in bundle["groups"]}
    for deny in bundle["armDenyAssignments"]:
        properties = deny["properties"]
        included = set()
        for item in properties["principals"]:
            if item["id"] == "00000000-0000-0000-0000-000000000000": included |= all_actors
            elif item["id"] in subject_ids: included |= member_actors(item["id"])
            else: raise GraphError("Deny principal is absent from export inventory.")
        for item in properties.get("excludePrincipals", []):
            if item["id"] not in subject_ids: raise GraphError("Deny exclusion principal is absent from export inventory.")
            included -= member_actors(item["id"])
        for actor in sorted(included):
            add_binding(safe_id("deny-", deny["id"] + actor), subject_ids[actor], operation_grants(properties["scope"], properties["permissions"], properties.get("doNotApplyToChildScopes", False)), "ARM/denyAssignments", effect="deny")
    for vault in bundle["vaults"]:
        if vault["id"] not in resource_ids: continue
        if vault["properties"].get("enableRbacAuthorization", False): continue
        for index, policy in enumerate(vault["properties"].get("accessPolicies", [])):
            if policy["objectId"] not in subject_ids: raise GraphError("Vault policy principal is outside the export inventory.")
            actions = {"read_secret" for permission in policy.get("permissions", {}).get("secrets", []) if permission == "get"}
            if "list" in policy.get("permissions", {}).get("secrets", []): actions.add("read_metadata")
            if actions: add_binding(safe_id("vault-policy-", vault["id"] + str(index)), subject_ids[policy["objectId"]], [(resource_ids[vault["id"]], sorted(actions))], "ARM/vaults/accessPolicies")

    def mapped_capabilities(key, mapping_name):
        mapping = metadata.get(mapping_name, {}).get(key)
        if mapping is None:
            builder.graph["coverage"].append(f"Unmapped {mapping_name} object: {key}; no permission inferred from its name.")
            return []
        return [(resource_ids[item["resource_id"]], item["actions"]) for item in mapping]

    for assignment in bundle["appRoleAssignments"]:
        subject = subject_ids.get(assignment["principalId"])
        if subject is None: raise GraphError("App role assignment principal is missing.")
        mapping_key = assignment["resourceId"] + ":" + assignment["appRoleId"]
        add_binding(safe_id("app-role-", assignment["id"]), subject, mapped_capabilities(mapping_key, "app_role_capabilities"), "Graph/servicePrincipals/appRoleAssignments")
    for assignment in bundle["directoryRoleAssignments"]:
        if assignment.get("directoryScopeId") != "/" or assignment.get("appScopeId"):
            raise GraphError("Scoped directory assignments are not supported by the fixture capability mapping.")
        add_binding(safe_id("directory-role-", assignment["id"]), subject_ids[assignment["principalId"]], mapped_capabilities(assignment["roleDefinitionId"], "directory_role_capabilities"), "Graph/roleManagement/directory/roleAssignments")
    now = datetime.fromisoformat(metadata["observed_at"])
    for eligibility in bundle["roleEligibilityScheduleInstances"]:
        if eligibility.get("startDateTime") and datetime.fromisoformat(eligibility["startDateTime"]) > now: continue
        if eligibility.get("endDateTime") and datetime.fromisoformat(eligibility["endDateTime"]) <= now: continue
        requirements = metadata.get("pim_requirements", {}).get(eligibility["id"])
        if requirements is None: raise GraphError("PIM eligibility requires explicit reviewed activation constraints; approval is not implied absent.")
        add_binding(safe_id("pim-", eligibility["id"]), subject_ids[eligibility["principalId"]], mapped_capabilities(eligibility["roleDefinitionId"], "directory_role_capabilities"), "Graph/roleEligibilityScheduleInstances", eligible=True, constraints=["pim_eligible", *requirements])
    for grant in bundle["oauth2PermissionGrants"]:
        builder.graph["coverage"].append(f"Delegated OAuth grant {grant['id']} inventoried only: consent alone does not confer app-only capabilities without a signed-in user/session context.")
    for policy in bundle["conditionalAccessPolicies"]:
        if policy.get("state") != "enabled": continue
        mapping = metadata.get("conditional_access_review", {}).get(policy["id"])
        if mapping is None: raise GraphError("Enabled Conditional Access policy needs explicit fixture-stage applicability review.")
        for credential_id in mapping["credentials"]:
            auth = next((edge for edge in builder.graph["edges"] if edge["kind"] == "authenticates_as" and edge["source"] == credential_id), None)
            if auth is None: raise GraphError("Reviewed Conditional Access gate references an unknown authenticator.")
            auth["constraints"] = sorted(set(auth.get("constraints", [])) | set(mapping["constraints"]))
        builder.graph["coverage"].append(f"Conditional Access policy {policy['id']} uses explicit synthetic review; general policy predicate/OR/session/claims evaluation is deferred.")
    for link in metadata.get("secret_links", []):
        builder.edge(safe_id("secret-link-", json.dumps(link, sort_keys=True)), "can_read_secret", subject_ids[link["principal_id"]], link["credential_id"], requires={"resource_id": resource_ids[link["vault_id"]], "action": "read_secret"})
    return validate(normalized(builder.graph))
