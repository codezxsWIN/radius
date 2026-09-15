"""Strict synthetic graph parsing and canonical serialization."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATHS = {
    "0.1": Path(__file__).with_name("assets") / "blastradius-graph-v0.1.schema.json",
    "0.2": Path(__file__).with_name("assets") / "blastradius-graph-v0.2.schema.json",
}
# Backward-compatible public path for consumers of the frozen v0.1 contract.
SCHEMA_PATH = SCHEMA_PATHS["0.1"]
MODELS = {
    "default": frozenset({"device_required", "approval_required"}),
    "strict": frozenset({"device_required", "approval_required", "network_restriction", "time_window"}),
    "session-theft-aware": frozenset({"device_required", "approval_required"}),
    "permissive": frozenset(),
}
FORMATS = FormatChecker(formats=[])


@FORMATS.checks("date-time", raises=ValueError)
def valid_time(value):
    return not isinstance(value, str) or datetime.fromisoformat(value).tzinfo is not None


class GraphError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def normalized(graph):
    result = deepcopy(graph)
    result["nodes"] = sorted(result["nodes"], key=lambda item: item["id"])
    result["edges"] = sorted(result["edges"], key=lambda item: item["id"])
    for item in result["nodes"] + result["edges"]:
        for field in ("actions", "constraints", "session_satisfied_constraints"):
            if field in item:
                item[field] = sorted(item[field])
    return result


def graph_hash(graph):
    return sha256(canonical(normalized(graph))).hexdigest()


def validate(graph):
    version = graph.get("schema_version") if isinstance(graph, dict) else None
    if version not in SCHEMA_PATHS:
        raise GraphError("Unsupported graph schema version.")
    schema = json.loads(SCHEMA_PATHS[version].read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FORMATS)
    error = next(validator.iter_errors(graph), None)
    if error:
        location = "/".join(map(str, error.absolute_path))
        raise GraphError(f"Schema validation failed at {location or 'root'} ({error.validator}); values are not echoed.")
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = {edge["id"]: edge for edge in graph["edges"]}
    if len(nodes) != len(graph["nodes"]) or len(edges) != len(graph["edges"]) or nodes.keys() & edges.keys():
        raise GraphError("Node/edge identifiers must be globally unique.")
    action_ids = set(graph["action_weights"])
    for node in nodes.values():
        allowed = {"id", "kind", "subtype", "name", "provenance"} | {
            "principal": {"provisioned_at"}, "credential": {"principal_id", "provisioned_at", "session_satisfied_constraints"},
            "binding": {"effect", "constraints", "eligible"}, "resource": {"actions", "sensitivity"}, "constraint": set(),
        }[node["kind"]]
        if set(node) - allowed:
            raise GraphError("A node contains fields from a different node kind.")
        if node["kind"] == "resource" and not set(node["actions"]) <= action_ids:
            raise GraphError("A resource action has no declared action weight.")
        if node["kind"] == "resource" and not math.isfinite(node["sensitivity"]):
            raise GraphError("Resource sensitivity must be finite.")
        if node["kind"] == "credential":
            if node.get("session_satisfied_constraints") and node["subtype"] != "token":
                raise GraphError("Only an explicitly modeled issued token can carry completed authentication factors.")
            owner = nodes.get(node["principal_id"], {})
            if owner.get("kind") != "principal" or owner.get("subtype") == "group":
                raise GraphError("Credential owner must be a non-group principal.")
        for constraint_id in node.get("constraints", []):
            if nodes.get(constraint_id, {}).get("kind") != "constraint":
                raise GraphError("Unknown binding constraint.")
    for edge in edges.values():
        source, target = nodes.get(edge["source"]), nodes.get(edge["target"])
        relation = edge["kind"]
        if relation != "grants" and "actions" in edge or relation != "can_read_secret" and "requires" in edge:
            raise GraphError("Action/secret prerequisites are attached to the wrong relation kind.")
        if relation == "constrained_by":
            if edge["source"] not in nodes and edge["source"] not in edges:
                raise GraphError("Unknown constrained source.")
            if target is None or target["kind"] != "constraint":
                raise GraphError("constrained_by must target a constraint.")
            if source is not None and source["kind"] != "binding":
                raise GraphError("Only binding nodes or authorization edges can carry constrained_by annotations.")
            continue
        if source is None or target is None:
            raise GraphError("An edge has a dangling reference.")
        for constraint_id in edge.get("constraints", []):
            if nodes.get(constraint_id, {}).get("kind") != "constraint":
                raise GraphError("Unknown edge constraint.")
        endpoints = (source["kind"], target["kind"])
        expected = {
            "authenticates_as": ("credential", "principal"), "member_of": ("principal", "principal"),
            "assigned": ("principal", "binding"), "grants": ("binding", "resource"),
            "can_assume": ("principal", "principal"), "can_read_secret": ("principal", "credential"),
        }
        if endpoints != expected[relation]:
            raise GraphError("Invalid endpoint kinds for relation.")
        if relation == "authenticates_as" and source["principal_id"] != target["id"]:
            raise GraphError("An authenticator must target its declared principal.")
        if relation == "member_of" and target["subtype"] != "group":
            raise GraphError("Membership must target a group principal.")
        if relation == "can_assume" and target["subtype"] == "group":
            raise GraphError("Groups cannot be assumed as identities.")
        if relation == "grants" and not set(edge["actions"]) <= set(target["actions"]):
            raise GraphError("A grant exceeds the target action inventory.")
        if relation == "assigned" and target["effect"] == "deny" and (target["eligible"] or target["constraints"] or edge.get("constraints")):
            raise GraphError("Deny assignments must already be effective, active and independent of attacker-satisfiable constraints.")
        if relation == "can_read_secret":
            prerequisite = edge["requires"]
            resource = nodes.get(prerequisite["resource_id"], {})
            if resource.get("subtype") != "secret_store" or prerequisite["action"] != "read_secret" or "read_secret" not in resource.get("actions", []):
                raise GraphError("Credential acquisition requires an explicit secret-store read_secret capability.")
        if edge.get("actor_id") and nodes.get(edge["actor_id"], {}).get("kind") != "principal":
            raise GraphError("Unknown actor restriction.")
    universe = {(node["id"], action) for node in nodes.values() if node["kind"] == "resource" for action in node["actions"]}
    if not universe:
        raise GraphError("An empty resource-action universe has undefined radius.")
    return graph


def _unique(members):
    result = {}
    for key, value in members:
        if key in result:
            raise GraphError("Duplicate JSON properties are rejected.")
        result[key] = value
    return result


def read_json(stream):
    def reject_number(value):
        raise GraphError("Nonfinite JSON values are rejected.")
    def exact_float(token):
        value = float(token)
        if not math.isfinite(value) or Decimal(str(value)) != Decimal(token):
            raise GraphError("Decimal token loses value in the v0.1 wire profile; use a supported exact decimal or a separately defined decimal profile.")
        return value
    return json.load(stream, object_pairs_hook=_unique, parse_constant=reject_number, parse_float=exact_float)


def read_graph(path):
    try:
        with Path(path).open(encoding="utf-8-sig") as stream:
            graph = read_json(stream)
        return validate(graph)
    except (json.JSONDecodeError, RecursionError, UnicodeError):
        raise GraphError("Input is not valid UTF-8 graph JSON.") from None


def number(value):
    return Fraction(str(value))
