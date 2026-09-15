"""Bounded CloudFormation IAM evidence extraction."""

from hashlib import sha256
import re

from ..model import canonical
from .yaml_nodes import location, mapping, scalar, scalar_list, sequence


SECRET_ARN = re.compile(r"^arn:aws:secretsmanager:[a-z0-9-]+:[0-9]{12}:secret:[A-Za-z0-9/_+=.@-]+$")


def _identifier(kind, *parts):
    digest = sha256(canonical([kind, *parts])).hexdigest()[:20]
    return f"{kind}-{digest}"


def _diagnostic(code, message, path, node, severity="warning"):
    return {"code": code, "severity": severity, "message": message, "location": location(path, node)}


def _statements(policy):
    document = mapping(policy)
    if document is None or "Statement" not in document:
        return None
    values = sequence(document["Statement"])
    if values is not None:
        return values
    return [document["Statement"]] if mapping(document["Statement"]) is not None else None


def _github_trusts(path, role_id, policy):
    facts, diagnostics = [], []
    statements = _statements(policy)
    if statements is None:
        diagnostics.append(_diagnostic("UNSUPPORTED_TRUST_POLICY", "Role trust policy has no supported literal statements.", path, policy))
        return facts, diagnostics
    for index, statement_node in enumerate(statements):
        statement = mapping(statement_node)
        if statement is None:
            continue
        effect = scalar(statement.get("Effect")) if "Effect" in statement else None
        principal = mapping(statement.get("Principal")) if "Principal" in statement else None
        federated = scalar_list(principal.get("Federated")) if principal and "Federated" in principal else None
        actions = scalar_list(statement.get("Action")) if "Action" in statement else None
        if effect != "Allow" or not federated or not actions:
            continue
        if not any(value.endswith(":oidc-provider/token.actions.githubusercontent.com") for value in federated):
            continue
        if "sts:AssumeRoleWithWebIdentity" not in actions:
            continue
        condition = mapping(statement.get("Condition")) if "Condition" in statement else None
        if condition is None:
            diagnostics.append(_diagnostic("GITHUB_TRUST_CONDITION_MISSING", "GitHub OIDC trust lacks a supported literal condition.", path, statement_node, "error"))
            continue
        unsupported = set(condition) - {"StringEquals", "StringLike"}
        if unsupported:
            diagnostics.append(_diagnostic("UNSUPPORTED_TRUST_CONDITION", "GitHub OIDC trust uses an unsupported condition operator.", path, statement["Condition"]))
            continue
        equals = mapping(condition.get("StringEquals")) if "StringEquals" in condition else {}
        like = mapping(condition.get("StringLike")) if "StringLike" in condition else {}
        if equals is None or like is None:
            diagnostics.append(_diagnostic("UNSUPPORTED_TRUST_CONDITION", "GitHub OIDC trust condition must be a literal mapping.", path, statement["Condition"]))
            continue
        audience = scalar_list(equals.get("token.actions.githubusercontent.com:aud")) if "token.actions.githubusercontent.com:aud" in equals else None
        if audience != ["sts.amazonaws.com"]:
            diagnostics.append(_diagnostic("GITHUB_TRUST_AUDIENCE_UNSUPPORTED", "GitHub OIDC trust does not require the supported sts.amazonaws.com audience.", path, statement["Condition"], "error"))
            continue
        subject_node = equals.get("token.actions.githubusercontent.com:sub") or like.get("token.actions.githubusercontent.com:sub")
        subjects = scalar_list(subject_node) if subject_node is not None else None
        if not subjects:
            diagnostics.append(_diagnostic("GITHUB_TRUST_SUBJECT_MISSING", "GitHub OIDC trust has no supported subject condition.", path, statement["Condition"], "error"))
            continue
        broad = any("*" in value or "?" in value for value in subjects)
        confidence = "potential" if broad else "declared-configuration"
        fact = {
            "id": _identifier("aws-trust", path, role_id, index, subjects),
            "role_id": role_id,
            "subjects": sorted(set(subjects)),
            "audience": audience,
            "operator": "StringEquals" if subject_node is equals.get("token.actions.githubusercontent.com:sub") else "StringLike",
            "broad": broad,
            "confidence": confidence,
            "location": location(path, statement_node),
        }
        facts.append(fact)
        if broad:
            diagnostics.append(_diagnostic("BROAD_GITHUB_TRUST", "GitHub OIDC subject trust contains a wildcard and is only a potential repository match.", path, subject_node, "error"))
    return facts, diagnostics


def _secret_grants(path, role_id, policies):
    facts, diagnostics = [], []
    policy_nodes = sequence(policies)
    if policy_nodes is None:
        return facts, [_diagnostic("UNSUPPORTED_ROLE_POLICIES", "Role policies must be a literal list.", path, policies)]
    for policy_index, policy_node in enumerate(policy_nodes):
        policy = mapping(policy_node)
        document = policy.get("PolicyDocument") if policy else None
        statements = _statements(document) if document is not None else None
        if statements is None:
            diagnostics.append(_diagnostic("UNSUPPORTED_PERMISSION_POLICY", "Inline role policy has no supported literal statements.", path, policy_node))
            continue
        for statement_index, statement_node in enumerate(statements):
            statement = mapping(statement_node)
            if statement is None:
                continue
            effect = scalar(statement.get("Effect")) if "Effect" in statement else None
            if effect == "Deny":
                diagnostics.append(_diagnostic("EXPLICIT_DENY_UNSUPPORTED", "Explicit deny is retained as unsupported evidence and never converted into an allow fact.", path, statement_node))
                continue
            if effect != "Allow":
                continue
            if set(statement) & {"Condition", "NotAction", "NotResource", "Principal", "NotPrincipal"}:
                diagnostics.append(_diagnostic("UNSUPPORTED_PERMISSION_STATEMENT", "Permission statement uses elements outside the finite allow profile.", path, statement_node))
                continue
            actions = scalar_list(statement.get("Action")) if "Action" in statement else None
            if not actions or "secretsmanager:GetSecretValue" not in actions:
                continue
            resources = scalar_list(statement.get("Resource")) if "Resource" in statement else None
            if not resources:
                diagnostics.append(_diagnostic("NONFINITE_SECRET_RESOURCE", "Secret read permission has no finite literal Secrets Manager resource.", path, statement_node, "error"))
                continue
            for resource_index, resource in enumerate(resources):
                if "*" in resource or "?" in resource or not SECRET_ARN.fullmatch(resource):
                    diagnostics.append(_diagnostic("NONFINITE_SECRET_RESOURCE", "Secret read permission resource is wildcarded or outside the finite ARN profile.", path, statement["Resource"], "error"))
                    continue
                facts.append({
                    "id": _identifier("aws-secret-grant", path, role_id, policy_index, statement_index, resource_index, resource),
                    "role_id": role_id,
                    "provider_action": "secretsmanager:GetSecretValue",
                    "action": "read_secret",
                    "resource_arn": resource,
                    "confidence": "declared-configuration",
                    "location": location(path, statement_node),
                })
    return facts, diagnostics


def extract_cloudformation(path, root):
    root_map = mapping(root)
    resources = mapping(root_map.get("Resources")) if root_map and "Resources" in root_map else None
    if resources is None:
        return [], [], [], [_diagnostic("UNSUPPORTED_CLOUDFORMATION", "CloudFormation document must contain a literal Resources mapping.", path, root)]
    roles, trusts, grants, diagnostics = [], [], [], []
    for logical_id, resource_node in sorted(resources.items()):
        resource = mapping(resource_node)
        if resource is None or scalar(resource.get("Type")) != "AWS::IAM::Role":
            continue
        properties = mapping(resource.get("Properties")) if "Properties" in resource else None
        role_name_node = properties.get("RoleName") if properties else None
        role_name = scalar(role_name_node) if role_name_node is not None else None
        if not role_name or "${" in role_name or "*" in role_name or "/" in role_name:
            diagnostics.append(_diagnostic("DYNAMIC_ROLE_NAME", "IAM role has no supported literal RoleName.", path, role_name_node or resource_node))
            continue
        role_id = _identifier("aws-role", path, logical_id, role_name)
        roles.append({
            "id": role_id,
            "logical_id": logical_id,
            "role_name": role_name,
            "confidence": "declared-configuration",
            "location": location(path, resource_node),
        })
        trust_policy = properties.get("AssumeRolePolicyDocument") if properties else None
        if trust_policy is not None:
            found, issues = _github_trusts(path, role_id, trust_policy)
            trusts.extend(found)
            diagnostics.extend(issues)
        policies = properties.get("Policies") if properties else None
        if policies is not None:
            found, issues = _secret_grants(path, role_id, policies)
            grants.extend(found)
            diagnostics.extend(issues)
    return roles, trusts, grants, diagnostics
