"""Conservative mapping from repository evidence to authorization graph v0.2."""

from copy import deepcopy
from hashlib import sha256

from ..model import GraphError, canonical, validate
from .evidence import PROFILE as EVIDENCE_PROFILE


def _identifier(kind, *parts):
    digest = sha256(canonical([kind, *parts])).hexdigest()[:24]
    return f"{kind}-{digest}"


def _name(value, prefix=""):
    text = prefix + str(value)
    if len(text) <= 160:
        return text
    return text[:77] + "..." + text[-80:]


def _provenance(source_api, snapshot_hash, evidence_ref):
    return {
        "connector": "repository",
        "source_api": source_api,
        "snapshot_hash": snapshot_hash,
        "evidence_ref": evidence_ref,
    }


def _fact_map(evidence, collection):
    facts = evidence.get("facts", {}).get(collection)
    if not isinstance(facts, list):
        raise GraphError("Repository evidence contains an invalid fact collection.")
    result = {}
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("id"), str) or fact["id"] in result:
            raise GraphError("Repository evidence contains invalid or duplicate fact identifiers.")
        result[fact["id"]] = fact
    return result


def build_repository_graph(evidence: dict) -> tuple[dict | None, dict]:
    """Return a validated graph only for exact, finite repository evidence paths."""
    if not isinstance(evidence, dict) or evidence.get("profile") != EVIDENCE_PROFILE:
        raise GraphError("Repository evidence is invalid or unsupported.")
    repository = evidence.get("repository")
    if not isinstance(repository, dict):
        raise GraphError("Repository evidence has no repository identity.")
    slug, snapshot_hash = repository.get("slug"), repository.get("snapshot_hash")
    if (not isinstance(slug, str) or not isinstance(snapshot_hash, str)
            or len(snapshot_hash) != 64
            or any(character not in "0123456789abcdef" for character in snapshot_hash)):
        raise GraphError("Repository evidence has an invalid repository identity.")

    workflows = _fact_map(evidence, "workflows")
    requests = _fact_map(evidence, "oidc_role_requests")
    roles = _fact_map(evidence, "aws_roles")
    trusts = _fact_map(evidence, "aws_trusts")
    grants = _fact_map(evidence, "aws_secret_grants")
    grants_by_role = {}
    for grant in grants.values():
        if grant.get("action") == "read_secret" and grant.get("provider_action") == "secretsmanager:GetSecretValue" and isinstance(grant.get("resource_arn"), str):
            grants_by_role.setdefault(grant.get("role_id"), []).append(grant)

    complete = []
    for request in sorted(requests.values(), key=lambda item: item["id"]):
        if request.get("trust_match") != "exact-declared-configuration":
            continue
        workflow = workflows.get(request.get("workflow_id"))
        if workflow is None:
            continue
        for role_id in sorted(request.get("matching_role_ids", [])):
            role = roles.get(role_id)
            if role is None:
                continue
            for trust_id in sorted(request.get("matching_trust_ids", [])):
                trust = trusts.get(trust_id)
                if trust is None or trust.get("role_id") != role_id or trust.get("broad") is not False:
                    continue
                for grant in sorted(grants_by_role.get(role_id, []), key=lambda item: item["id"]):
                    complete.append((workflow, request, role, trust, grant))

    if not complete:
        return None, {}

    evidence_index = {}
    resource_support = {}
    for _, _, _, _, grant in complete:
        resource_support.setdefault(grant["resource_arn"], {})[grant["id"]] = grant
    resource_references = {}
    for resource_arn, supporting_grants in sorted(resource_support.items()):
        grant_ids = sorted(supporting_grants)
        reference = _identifier("evidence-secret-resource", resource_arn, *grant_ids)
        first = supporting_grants[grant_ids[0]]
        evidence_index[reference] = {
            "id": reference,
            "kind": "finite-secret-resource-declaration",
            "resource_arn": resource_arn,
            "grant_ids": grant_ids,
            "confidence": "declared-configuration",
            "location": deepcopy(first["location"]),
        }
        resource_references[resource_arn] = reference
    nodes, edges = {}, {}

    def keep_fact(fact):
        evidence_index[fact["id"]] = deepcopy(fact)

    def keep_node(node):
        existing = nodes.get(node["id"])
        if existing is not None and existing != node:
            raise GraphError("Repository evidence maps one graph identifier to conflicting nodes.")
        nodes[node["id"]] = node

    def keep_edge(edge):
        existing = edges.get(edge["id"])
        if existing is not None and existing != edge:
            raise GraphError("Repository evidence maps one graph identifier to conflicting edges.")
        edges[edge["id"]] = edge

    for workflow, request, role, trust, grant in complete:
        for fact in (workflow, request, role, trust, grant):
            keep_fact(fact)

        workflow_id = _identifier("principal-workflow", workflow["id"])
        credential_id = _identifier("credential-oidc", request["id"])
        role_id = _identifier("principal-aws-role", role["id"])
        binding_id = _identifier("binding-secret-read", grant["id"])
        resource_id = _identifier("resource-secret", grant["resource_arn"])
        correlation_id = _identifier("evidence-correlation", request["id"], trust["id"], role["id"])
        evidence_index[correlation_id] = {
            "id": correlation_id,
            "kind": "exact-github-oidc-role-correlation",
            "request_id": request["id"],
            "trust_id": trust["id"],
            "role_id": role["id"],
            "confidence": "declared-configuration",
            "location": deepcopy(request["location"]),
            "supporting_locations": [
                {"fact_id": request["id"], **deepcopy(request["location"])},
                {"fact_id": trust["id"], **deepcopy(trust["location"])},
            ],
        }

        keep_node({
            "id": workflow_id,
            "kind": "principal",
            "subtype": "workload_identity",
            "name": _name(workflow.get("name", workflow["path"]), "GitHub Actions workflow: "),
            "provenance": _provenance("github-actions", snapshot_hash, workflow["id"]),
        })
        keep_node({
            "id": credential_id,
            "kind": "credential",
            "subtype": "federated_trust",
            "name": _name(f"OIDC request in job {request.get('job_id', 'unknown')}"),
            "principal_id": workflow_id,
            "provenance": _provenance("github-actions", snapshot_hash, request["id"]),
        })
        keep_node({
            "id": role_id,
            "kind": "principal",
            "subtype": "service_principal",
            "name": _name(role.get("role_name", role["id"]), "AWS IAM role: "),
            "provenance": _provenance("cloudformation", snapshot_hash, role["id"]),
        })
        keep_node({
            "id": binding_id,
            "kind": "binding",
            "subtype": "policy_attachment",
            "name": _name("Declared Secrets Manager read grant"),
            "effect": "allow",
            "constraints": [],
            "eligible": False,
            "provenance": _provenance("cloudformation", snapshot_hash, grant["id"]),
        })
        keep_node({
            "id": resource_id,
            "kind": "resource",
            "subtype": "secret_store",
            "name": _name(grant["resource_arn"], "AWS secret: "),
            "actions": ["read_secret"],
            "sensitivity": 1.0,
            "provenance": _provenance("cloudformation", snapshot_hash, resource_references[grant["resource_arn"]]),
        })

        keep_edge({
            "id": _identifier("edge-authenticates", request["id"]),
            "source": credential_id,
            "target": workflow_id,
            "kind": "authenticates_as",
            "provenance": _provenance("github-actions", snapshot_hash, request["id"]),
        })
        keep_edge({
            "id": _identifier("edge-can-assume", request["id"], trust["id"], role["id"]),
            "source": workflow_id,
            "target": role_id,
            "kind": "can_assume",
            "provenance": _provenance("repository-correlation", snapshot_hash, correlation_id),
        })
        keep_edge({
            "id": _identifier("edge-assigned", role["id"], grant["id"]),
            "source": role_id,
            "target": binding_id,
            "kind": "assigned",
            "provenance": _provenance("cloudformation", snapshot_hash, grant["id"]),
        })
        keep_edge({
            "id": _identifier("edge-grants", grant["id"]),
            "source": binding_id,
            "target": resource_id,
            "kind": "grants",
            "actions": ["read_secret"],
            "provenance": _provenance("cloudformation", snapshot_hash, grant["id"]),
        })

    graph = {
        "schema_version": "0.2",
        "synthetic": False,
        "source_kind": "repository-declared-configuration",
        "organization": slug,
        "observed_at": None,
        "action_weights": {"read_secret": 1},
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(edges.values(), key=lambda item: item["id"]),
        "coverage": [
            "GitHub Actions and literal AWS CloudFormation declarations only.",
            "Deployed AWS state, runtime conditions and effective permissions were not verified.",
        ],
    }
    return validate(graph), dict(sorted(evidence_index.items()))
