from copy import deepcopy

from blastradius.engine import Engine
from blastradius.model import validate
from test_model import example, PROVENANCE


def test_direct_half_radius_and_no_double_count():
    graph = example()
    graph["edges"].append({**graph["edges"][-1], "id": "duplicate-grant"})
    validate(graph)
    assert Engine(graph).reach("credential").pairs == {("resource", "read")}


def test_deny_subtracts_even_through_other_allow_binding():
    graph = deepcopy(example())
    graph["nodes"].append({**graph["nodes"][2], "id": "deny", "effect": "deny"})
    graph["edges"].extend([
        {"id": "deny-assign", "kind": "assigned", "source": "person", "target": "deny", "provenance": PROVENANCE},
        {"id": "deny-grant", "kind": "grants", "source": "deny", "target": "resource", "actions": ["read"], "provenance": PROVENANCE},
    ])
    validate(graph)
    assert not Engine(graph).reach("credential").pairs
