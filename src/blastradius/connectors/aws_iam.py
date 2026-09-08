"""Bounded synthetic IAM export adapter; no AWS SDK, authentication or API calls."""

import json
from pathlib import Path
import re
from urllib.parse import unquote

from ..model import GraphError, normalized, validate
from ..synthetic import Builder
from .entra_azure import reject_material, safe_id

REQUIRED_CONTEXT = {
    "account_scope": "single-fictional-account", "permissions_boundaries": "absent",
    "service_control_policies": "allow_all", "resource_control_policies": "allow_all",
    "session_policies": "absent", "resource_policies": "absent_except_role_trust",
    "kms_authorization": "not_required",
}


def sequence(value):
    return value if isinstance(value, list) else [value]


def pattern_matches(value, pattern, insensitive=False):
    if "${" in pattern:
        raise GraphError("IAM policy variables require contextual evaluation and are unsupported.")
    expression = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(expression, value, re.IGNORECASE if insensitive else 0) is not None


def statements(document, trust=False):
    if isinstance(document, str):
        document = json.loads(unquote(document))
    if document.get("Version", "2012-10-17") != "2012-10-17":
        raise GraphError("Only the explicitly supported IAM policy language version is accepted.")
    result = sequence(document.get("Statement", []))
    for statement in result:
        if statement.get("Condition") or "NotPrincipal" in statement or "Principal" in statement and not trust:
            raise GraphError("Conditional or unsupported principal policy semantics are not approximated.")
        if statement.get("Effect") not in {"Allow", "Deny"} or ("Action" in statement) == ("NotAction" in statement):
            raise GraphError("Each statement needs an effect and exactly one Action/NotAction selector.")
        if not trust and ("Resource" in statement) == ("NotResource" in statement):
            raise GraphError("Each identity statement needs exactly one Resource/NotResource selector.")
    return result


def matches(statement, action, resource, trust=False):
    field = "Action" if "Action" in statement else "NotAction"
    action_match = any(pattern_matches(action, value, True) for value in sequence(statement[field]))
    if field == "NotAction": action_match = not action_match
    if trust: return action_match
    field = "Resource" if "Resource" in statement else "NotResource"
    resource_match = any(pattern_matches(resource, value) for value in sequence(statement[field]))
    if field == "NotResource": resource_match = not resource_match
    return action_match and resource_match


def normalize_exports(details, metadata):
    reject_material(details)
    reject_material(metadata)
    if metadata.get("synthetic") is not True or metadata.get("policy_context") != REQUIRED_CONTEXT:
        raise GraphError("AWS adapter requires the complete explicit synthetic policy context; real or restrictive boundary/SCP/session contexts are unsupported.")
    if details.get("IsTruncated", True):
        raise GraphError("GetAccountAuthorizationDetails export is incomplete; materialize every Marker page first.")
    builder = Builder(metadata["organization"])
    builder.graph["observed_at"] = metadata["observed_at"]
    builder.graph["coverage"] = [
        "Experimental offline synthetic IAM subset only; no AWS account contacted.",
        "Explicit fixture assumptions: single account, no permissions boundaries or session policies, allow-all SCP/RCP, no resource policies except account-root role trust, no additional KMS authorization.",
        "Only declared resource-operation catalog entries are measured. Storage is a bucket-level unit, not per-object inventory. General IAM conditions, policy variables, cross-account access and federation are rejected or outside this profile.",
        "AssumeRole and secret acquisition are graph edges only; no STS or secret-value request is executed.",
    ]
    entities, identifiers, groups, managed = {}, {}, {}, {}
    for policy in details.get("Policies", []):
        versions = [version for version in policy["PolicyVersionList"] if version.get("IsDefaultVersion")]
        if len(versions) != 1: raise GraphError("Managed policy requires exactly one default version.")
        managed[policy["Arn"]] = statements(versions[0]["Document"])
    for collection, name_field, subtype in (("UserDetailList", "UserName", "human_user"), ("RoleDetailList", "RoleName", "workload_identity"), ("GroupDetailList", "GroupName", "group")):
        for entity in details.get(collection, []):
            if entity.get("PermissionsBoundary"): raise GraphError("Permissions boundaries are unsupported in this explicit fixture profile.")
            arn = entity["Arn"]
            if arn in entities: raise GraphError("Duplicate IAM entity ARN.")
            if arn.split(":")[4] != metadata["account_id"]: raise GraphError("Cross-account entities are outside this profile.")
            entities[arn], identifiers[arn] = entity, safe_id("aws-principal-", arn)
            builder.node(identifiers[arn], "principal", metadata.get("principal_types", {}).get(arn, subtype), "Fictional " + entity[name_field])
            if subtype == "group": groups[entity[name_field]] = arn
    for user in details.get("UserDetailList", []):
        for name in user.get("GroupList", []):
            if name not in groups: raise GraphError("IAM group policy inventory is incomplete.")
            builder.edge(safe_id("aws-member-", user["Arn"] + name), "member_of", identifiers[user["Arn"]], identifiers[groups[name]])
    for credential in metadata["credential_inventory"]:
        builder.node(credential["id"], "credential", credential["type"], credential["name"], principal_id=identifiers[credential["principal_arn"]])
        builder.edge("auth-" + credential["id"], "authenticates_as", credential["id"], identifiers[credential["principal_arn"]])
    resources = {}
    for resource in metadata["resource_inventory"]:
        identifier = safe_id("aws-resource-", resource["arn"])
        resources[resource["arn"]] = (identifier, resource)
        builder.node(identifier, "resource", resource["subtype"], resource["name"], sensitivity=resource["sensitivity"], actions=sorted({operation["canonical_action"] for operation in resource["operations"]}))

    def policies(entity):
        result = []
        for field in ("UserPolicyList", "RolePolicyList", "GroupPolicyList"):
            for policy in entity.get(field, []): result.extend(statements(policy["PolicyDocument"]))
        for attachment in entity.get("AttachedManagedPolicies", []):
            if attachment["PolicyArn"] not in managed: raise GraphError("Attached managed policy is absent from the export.")
            result.extend(managed[attachment["PolicyArn"]])
        return result

    entity_policies = {arn: policies(entity) for arn, entity in entities.items()}
    for arn, policy_list in entity_policies.items():
        for index, statement in enumerate(policy_list):
            grants = []
            for resource_id, resource in resources.values():
                actions = {operation["canonical_action"] for operation in resource["operations"] if matches(statement, operation["action"], operation["resource_arn"])}
                if actions: grants.append((resource_id, sorted(actions)))
            builder.binding(safe_id("aws-policy-", arn + str(index)), identifiers[arn], grants, effect=statement["Effect"].lower())

    def actor_policies(arn):
        result = list(entity_policies[arn])
        for group_name in entities[arn].get("GroupList", []): result.extend(entity_policies[groups[group_name]])
        return result

    account_root = f"arn:aws:iam::{metadata['account_id']}:root"
    for role in details.get("RoleDetailList", []):
        trust = statements(role["AssumeRolePolicyDocument"], trust=True)
        for statement in trust:
            if statement.get("Principal") != {"AWS": account_root}:
                raise GraphError("Only account-root trust is supported; direct same-account grants and service/federated trust need their separate authorization semantics.")
        trust_allows = any(statement["Effect"] == "Allow" and matches(statement, "sts:AssumeRole", role["Arn"], True) for statement in trust)
        trust_denies = any(statement["Effect"] == "Deny" and matches(statement, "sts:AssumeRole", role["Arn"], True) for statement in trust)
        for arn in sorted(entities):
            if arn in groups.values(): continue
            applicable = [statement for statement in actor_policies(arn) if matches(statement, "sts:AssumeRole", role["Arn"])]
            if trust_allows and not trust_denies and any(statement["Effect"] == "Allow" for statement in applicable) and not any(statement["Effect"] == "Deny" for statement in applicable):
                builder.edge(safe_id("aws-assume-", arn + role["Arn"]), "can_assume", identifiers[arn], identifiers[role["Arn"]])
    for link in metadata.get("secret_links", []):
        builder.edge(safe_id("aws-secret-", json.dumps(link, sort_keys=True)), "can_read_secret", identifiers[link["principal_arn"]], link["credential_id"], requires={"resource_id": resources[link["resource_arn"]][0], "action": "read_secret"})
    for item in builder.graph["nodes"] + builder.graph["edges"]:
        item["provenance"] = {"connector": "aws-iam-offline-v0.1", "source_api": "GetAccountAuthorizationDetails + explicit synthetic sidecar", "observed_at": metadata["observed_at"], "evidence_ref": item["id"]}
    return validate(normalized(builder.graph))


def ingest(folder):
    folder = Path(folder)
    details = json.loads((folder / "authorization-details.json").read_text(encoding="utf-8"))
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    return normalize_exports(details, metadata)
