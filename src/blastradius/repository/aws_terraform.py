"""Bounded Terraform JSON IAM evidence extraction."""

from hashlib import sha256
from io import StringIO
import json
import re

from ..model import GraphError, canonical, read_json
from .aws_cloudformation import _github_trusts, _secret_grants
from .yaml_nodes import DocumentSyntaxError, compose_document, location, mapping, scalar


ROLE_NAME = re.compile(r"^[A-Za-z0-9+=,.@_-]{1,64}$")
ROLE_PATH = re.compile(r"^/(?:[A-Za-z0-9+=,.@_/-]+/)?$")


def _identifier(kind, *parts):
    digest = sha256(canonical([kind, *parts])).hexdigest()[:20]
    return f"{kind}-{digest}"


def _diagnostic(code, message, path, node, severity="warning"):
    return {"code": code, "severity": severity, "message": message, "location": location(path, node)}


def _policy_node(path, node, diagnostics):
    value = scalar(node)
    if value is None or "${" in value or "%{" in value:
        diagnostics.append(_diagnostic("DYNAMIC_TERRAFORM_POLICY", "Terraform IAM policy must be a literal JSON string; expressions are not evaluated.", path, node))
        return None
    try:
        if not isinstance(read_json(StringIO(value)), dict):
            raise ValueError
        document = compose_document(value.encode("utf-8"))
    except (DocumentSyntaxError, GraphError, json.JSONDecodeError, ValueError):
        diagnostics.append(_diagnostic("MALFORMED_TERRAFORM_POLICY", "Terraform IAM policy is not a supported literal JSON document.", path, node, "error"))
        return None
    if mapping(document) is None:
        diagnostics.append(_diagnostic("MALFORMED_TERRAFORM_POLICY", "Terraform IAM policy must decode to a JSON object.", path, node, "error"))
        return None
    return document


def _relocate(items, path, node, source_api):
    source = location(path, node)
    for item in items:
        item["location"] = source.copy()
        item["source_api"] = source_api


def extract_terraform_json(path, root):
    """Extract literal IAM role, OIDC trust and inline policy facts from *.tf.json."""
    root_map = mapping(root)
    resources = mapping(root_map.get("resource")) if root_map and "resource" in root_map else None
    if resources is None:
        return [], [], [], [_diagnostic("UNSUPPORTED_TERRAFORM_JSON", "Terraform JSON must contain a literal resource mapping.", path, root)]

    role_blocks = mapping(resources.get("aws_iam_role")) if "aws_iam_role" in resources else {}
    policy_blocks = mapping(resources.get("aws_iam_role_policy")) if "aws_iam_role_policy" in resources else {}
    if role_blocks is None or policy_blocks is None:
        return [], [], [], [_diagnostic("UNSUPPORTED_TERRAFORM_JSON", "Terraform IAM resources must use literal named mappings.", path, root)]

    roles, trusts, grants, diagnostics = [], [], [], []
    roles_by_name = {}
    blocked_roles = set()
    unresolved_policy_target = False
    unsupported_attachments = set(resources) & {
        "aws_iam_policy_attachment", "aws_iam_role_policy_attachment",
    }
    if unsupported_attachments:
        diagnostics.append(_diagnostic("UNRESOLVED_ROLE_RESTRICTION", "Terraform managed-policy attachments are not evaluated; no complete Terraform role path is claimed.", path, root))
    for logical_id, resource_node in sorted(role_blocks.items()):
        resource = mapping(resource_node)
        name_node = resource.get("name") if resource else None
        role_name = scalar(name_node) if name_node is not None else None
        if not role_name or not ROLE_NAME.fullmatch(role_name):
            diagnostics.append(_diagnostic("DYNAMIC_ROLE_NAME", "Terraform IAM role has no supported literal name.", path, name_node or resource_node))
            continue
        path_node = resource.get("path") if resource and "path" in resource else None
        role_path = scalar(path_node) if path_node is not None else "/"
        if not role_path or not ROLE_PATH.fullmatch(role_path):
            diagnostics.append(_diagnostic("DYNAMIC_ROLE_PATH", "Terraform IAM role path must be a supported literal path.", path, path_node or resource_node))
            continue
        role_id = _identifier("aws-role", path, logical_id, role_name)
        role = {
            "id": role_id,
            "logical_id": logical_id,
            "role_name": role_name,
            "role_path": role_path,
            "confidence": "declared-configuration",
            "source_api": "terraform-json",
            "location": location(path, resource_node),
        }
        roles.append(role)
        roles_by_name.setdefault(role_name, []).append(role)
        if unsupported_attachments or set(resource) & {"permissions_boundary", "managed_policy_arns", "inline_policy", "count", "for_each", "provider"}:
            blocked_roles.add(role_id)
            diagnostics.append(_diagnostic("UNRESOLVED_ROLE_RESTRICTION", "A Terraform permission boundary or managed policy has not been evaluated; no complete path is claimed for this role.", path, resource_node))
            continue
        trust_node = resource.get("assume_role_policy")
        if trust_node is None:
            diagnostics.append(_diagnostic("UNSUPPORTED_TRUST_POLICY", "Terraform IAM role has no supported literal assume-role policy.", path, resource_node))
            continue
        trust_policy = _policy_node(path, trust_node, diagnostics)
        if trust_policy is not None:
            found, issues = _github_trusts(path, role_id, trust_policy)
            _relocate(found, path, trust_node, "terraform-json")
            _relocate(issues, path, trust_node, "terraform-json")
            trusts.extend(found)
            diagnostics.extend(issues)

    policy_nodes_by_role = {}
    for logical_id, resource_node in sorted(policy_blocks.items()):
        resource = mapping(resource_node)
        role_node = resource.get("role") if resource else None
        role_name = scalar(role_node) if role_node is not None else None
        if not role_name or not ROLE_NAME.fullmatch(role_name):
            diagnostics.append(_diagnostic("DYNAMIC_TERRAFORM_ROLE_REFERENCE", "Terraform IAM role policy must name a literal role; references are not evaluated.", path, role_node or resource_node))
            unresolved_policy_target = True
            continue
        matching_roles = roles_by_name.get(role_name, [])
        if len(matching_roles) != 1:
            diagnostics.append(_diagnostic("TERRAFORM_ROLE_REFERENCE_NOT_MATCHED", "Terraform IAM role policy does not match exactly one literal role in this file.", path, role_node))
            continue
        policy_node = resource.get("policy")
        if set(resource) & {"count", "for_each", "provider"}:
            blocked_roles.add(matching_roles[0]["id"])
            diagnostics.append(_diagnostic("UNRESOLVED_ROLE_RESTRICTION", "Terraform policy instance or provider selection is unresolved.", path, resource_node))
            continue
        if policy_node is None:
            blocked_roles.add(matching_roles[0]["id"])
            diagnostics.append(_diagnostic("UNSUPPORTED_PERMISSION_POLICY", "Terraform IAM role policy has no supported literal policy document.", path, resource_node))
            continue
        policy = _policy_node(path, policy_node, diagnostics)
        if policy is None:
            blocked_roles.add(matching_roles[0]["id"])
            continue
        policy_nodes_by_role.setdefault(matching_roles[0]["id"], []).append(policy_node)
    for role_id, policy_nodes in sorted(policy_nodes_by_role.items()):
        if unresolved_policy_target or role_id in blocked_roles:
            continue
        combined = [{"PolicyDocument": json.loads(scalar(node))} for node in policy_nodes]
        combined_node = compose_document(json.dumps(combined, separators=(",", ":")).encode("utf-8"))
        combined_facts, combined_issues = _secret_grants(path, role_id, combined_node)
        if not combined_facts:
            _relocate(combined_issues, path, policy_nodes[0], "terraform-json")
            diagnostics.extend(combined_issues)
            continue
        for policy_node in policy_nodes:
            policies = compose_document(("[{\"PolicyDocument\":" + scalar(policy_node) + "}]").encode("utf-8"))
            found, issues = _secret_grants(path, role_id, policies)
            _relocate(found, path, policy_node, "terraform-json")
            _relocate(issues, path, policy_node, "terraform-json")
            grants.extend(found)
            diagnostics.extend(issues)
    return roles, trusts, grants, diagnostics