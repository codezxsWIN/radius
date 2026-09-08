from copy import deepcopy
import json

import pytest
from jsonschema import Draft202012Validator

from blastradius.model import GraphError, SCHEMA_PATH, validate

PROVENANCE = {"connector": "synthetic", "source_api": "fixture", "observed_at": "2026-09-09T00:00:00Z", "evidence_ref": "invented"}


def example():
    return {
        "schema_version": "0.1", "synthetic": True, "organization": "Fictional Lumen Orchard",
        "observed_at": PROVENANCE["observed_at"], "action_weights": {"read": 1, "write": 3}, "coverage": [],
        "nodes": [
            {"id": "person", "kind": "principal", "subtype": "human_user", "name": "Fictional Mira Vale", "provenance": PROVENANCE},
            {"id": "credential", "kind": "credential", "subtype": "password", "name": "Mira metadata only", "principal_id": "person", "provenance": PROVENANCE},
            {"id": "binding", "kind": "binding", "subtype": "role_assignment", "name": "Read assignment", "effect": "allow", "eligible": False, "constraints": [], "provenance": PROVENANCE},
            {"id": "resource", "kind": "resource", "subtype": "database", "name": "Fictional Ledger", "actions": ["read", "write"], "sensitivity": 0.8, "provenance": PROVENANCE},
        ],
        "edges": [
            {"id": "auth", "kind": "authenticates_as", "source": "credential", "target": "person", "provenance": PROVENANCE},
            {"id": "assign", "kind": "assigned", "source": "person", "target": "binding", "provenance": PROVENANCE},
            {"id": "grant", "kind": "grants", "source": "binding", "target": "resource", "actions": ["read"], "provenance": PROVENANCE},
        ],
    }


def test_schema_and_example():
    Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text()))
    assert validate(example())["synthetic"] is True


@pytest.mark.parametrize("change", ["tenant", "secret", "reference", "duplicate", "weight"])
def test_reject_invalid_graph(change):
    graph = deepcopy(example())
    if change == "tenant": graph["synthetic"] = False
    if change == "secret": graph["nodes"][1]["secret"] = "REJECT-SENTINEL"
    if change == "reference": graph["edges"][0]["target"] = "missing"
    if change == "duplicate": graph["nodes"].append(graph["nodes"][0])
    if change == "weight": graph["nodes"][-1]["sensitivity"] = -0.1
    with pytest.raises(GraphError): validate(graph)
