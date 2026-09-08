"""Closed structural-summary contract; removing identifiers does not anonymize it."""

from collections import Counter
from fractions import Fraction

from jsonschema import Draft202012Validator

from .model import GraphError

NODE_KINDS = ("principal", "credential", "binding", "resource", "constraint")
PRINCIPAL_TYPES = ("human_user", "service_principal", "managed_identity", "workload_identity", "ai_agent", "group")
CREDENTIAL_TYPES = ("password", "key", "certificate", "token", "passkey", "federated_trust")
EDGE_KINDS = ("authenticates_as", "member_of", "assigned", "grants", "can_assume", "can_read_secret", "constrained_by")
STRUCTURE_FIELDS = ("shared_binding_count", "eligible_binding_count", "constrained_item_count")


def closed_object(properties):
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def summary_schema():
    count = {"type": "integer", "minimum": 0, "maximum": 1000000000}
    properties = {key: {"const": value} for key, value in {
        "summary_version": "1.0-draft", "synthetic": True, "submission_enabled": False,
        "privacy_reviewed": False, "anonymous": False, "schema_version": "0.1",
        "metric_profile": "1.0-draft", "normalizer_profile": "unasserted",
    }.items()}
    properties["constraint_model"] = {"enum": ["default", "strict", "session-theft-aware"]}
    properties["action_profile"] = {"enum": ["core-1-3-5", "custom-not-comparable"]}
    for key, fields in (("node_counts", NODE_KINDS), ("principal_counts", PRINCIPAL_TYPES), ("credential_counts", CREDENTIAL_TYPES), ("edge_counts", EDGE_KINDS), ("structural_features", STRUCTURE_FIELDS)):
        properties[key] = closed_object({field: count for field in fields})
    properties["canonical_radius_histogram"] = {
        "type": "array", "minItems": 10, "maxItems": 10,
        "prefixItems": [closed_object({"lower": {"const": index / 10}, "upper": {"const": (index + 1) / 10}, "upper_inclusive": {"const": index == 9}, "count": count}) for index in range(10)],
        "items": False,
    }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:blastradius:structural-summary:1.0-draft", "title": "Synthetic Structural Summary v1.0-draft; CC-BY-4.0", **closed_object(properties)}


def validate_summary(summary):
    if next(Draft202012Validator(summary_schema()).iter_errors(summary), None):
        raise GraphError("Structural summary does not match the closed reviewed field list.")
    if sum(summary["principal_counts"].values()) != summary["node_counts"]["principal"] or sum(summary["credential_counts"].values()) != summary["node_counts"]["credential"]:
        raise GraphError("Summary subtype counts disagree with node counts.")
    if sum(bucket["count"] for bucket in summary["canonical_radius_histogram"]) != summary["node_counts"]["credential"]:
        raise GraphError("Summary histogram does not cover its credential population.")
    return summary


def structural_summary(graph, records, model="default"):
    if graph.get("synthetic") is not True:
        raise GraphError("Structural summaries are restricted to synthetic graphs.")
    histogram = [0] * 10
    for record in records:
        radius = Fraction(record["absolute_reach"], record["universe_size"])
        if not 0 <= radius <= 1:
            raise GraphError("Invalid reach in summary input.")
        histogram[min(9, radius.numerator * 10 // radius.denominator)] += 1
    nodes, edges = graph["nodes"], graph["edges"]
    assigned = {}
    for edge in edges:
        if edge["kind"] == "assigned":
            assigned.setdefault(edge["target"], set()).add(edge["source"])
    principal_counts = Counter(node["subtype"] for node in nodes if node["kind"] == "principal")
    credential_counts = Counter(node["subtype"] for node in nodes if node["kind"] == "credential")
    summary = {
        "summary_version": "1.0-draft", "synthetic": True, "submission_enabled": False,
        "privacy_reviewed": False, "anonymous": False, "schema_version": "0.1",
        "metric_profile": "1.0-draft", "normalizer_profile": "unasserted", "constraint_model": model,
        "action_profile": "core-1-3-5" if graph["action_weights"] == {"read": 1, "write": 3, "administer": 5, "read_metadata": 1, "read_secret": 1} else "custom-not-comparable",
        "node_counts": {kind: sum(node["kind"] == kind for node in nodes) for kind in NODE_KINDS},
        "principal_counts": {kind: principal_counts[kind] for kind in PRINCIPAL_TYPES},
        "credential_counts": {kind: credential_counts[kind] for kind in CREDENTIAL_TYPES},
        "edge_counts": {kind: sum(edge["kind"] == kind for edge in edges) for kind in EDGE_KINDS},
        "structural_features": {"shared_binding_count": sum(len(subjects) > 1 for subjects in assigned.values()), "eligible_binding_count": sum(bool(node.get("eligible")) for node in nodes), "constrained_item_count": len({item["id"] for item in nodes + edges if item.get("constraints")} | {edge["source"] for edge in edges if edge["kind"] == "constrained_by"})},
        "canonical_radius_histogram": [{"lower": index / 10, "upper": (index + 1) / 10, "upper_inclusive": index == 9, "count": count} for index, count in enumerate(histogram)],
    }
    return validate_summary(summary)


def structural_preview(result):
    if result.get("synthetic") is not True:
        raise GraphError("Structural previews are restricted to synthetic results.")
    return structural_summary(result["snapshot"], result["credentials"], result["constraint_model"])
