from copy import deepcopy
from fractions import Fraction
import secrets

import pytest

from blastradius.analysis import Analysis, distribution, modify_binding, compare
from blastradius.model import GraphError, canonical, validate
from blastradius.oracle import expected
from blastradius.signing import sign, verify
from blastradius.synthetic import fixture, synth


def test_weighted_hand_calculation():
    result = Analysis(fixture("direct")).run()
    record = result["credentials"][0]
    assert record["absolute_reach"] == 1
    assert record["canonical_radius"] == 0.25
    assert record["sensitivity_weighted_radius"] == 0.1
    assert record["action_weighted_radius"] == 0.125
    assert result["recommendations"][0]["after_p95"] == 0


def test_zero_sensitivity_is_undefined():
    assert Analysis(fixture("zero-sensitivity")).run()["credentials"][0]["sensitivity_weighted_radius"] is None


def test_all_metrics_match_independent_oracle():
    graph = synth(8, 8, 19)
    for model in ("default", "strict", "permissive"):
        truth = expected(graph, model)
        for record in Analysis(graph, model).run(recommendations=False)["credentials"]:
            for metric in ("canonical_radius", "absolute_reach", "sensitivity_weighted_radius", "action_weighted_radius"):
                assert record[metric] == truth[record["credential_id"]][metric]


def test_statistics_empty_zero_and_nearest_rank():
    assert distribution([])["p95"] is None
    assert distribution([Fraction(), Fraction()])["gini"] == 0
    assert distribution([Fraction(), Fraction(1)])["gini"] == 0.5
    assert distribution([Fraction(index, 19) for index in range(20)])["p95"] == float(Fraction(18, 19))


def test_signed_manifest_determinism_and_tamper_detection():
    key = secrets.token_bytes(32)
    first = sign(Analysis(fixture("secret")).run(), key)
    second = sign(Analysis(fixture("secret")).run(), key)
    assert canonical(first) == canonical(second)
    assert verify(first, key)
    altered = deepcopy(first)
    altered["credentials"][0]["absolute_reach"] += 1
    with pytest.raises(GraphError): verify(altered, key)
    with pytest.raises(GraphError): verify(first, secrets.token_bytes(32))


def test_add_remove_binding_whatif_and_preserve_input():
    graph = fixture("direct")
    original = canonical(graph)
    removed = modify_binding(graph, remove="allow")
    assert canonical(graph) == original
    comparison = compare(Analysis(graph).run(False), Analysis(removed).run(False))
    assert comparison["credentials"][0]["deltas"]["canonical_radius"] == -0.25
    binding = next(node for node in graph["nodes"] if node["id"] == "allow")
    addition = {"binding": binding, "edges": [edge for edge in graph["edges"] if "allow" in (edge["source"], edge["target"])]}
    restored = validate(modify_binding(removed, addition=addition))
    assert canonical(restored) == canonical(graph)


def test_deny_removal_and_addition_report_increased_and_decreased_reach():
    graph = fixture("deny")
    changed = validate(modify_binding(graph, remove="deny"))
    before, after = Analysis(graph).run(False), Analysis(changed).run(False)
    assert compare(before, after)["credentials"][0]["deltas"]["canonical_radius"] == 0.25
    deny = next(node for node in graph["nodes"] if node["id"] == "deny")
    edges = [edge for edge in graph["edges"] if "deny" in (edge["source"], edge["target"])]
    restored = validate(modify_binding(changed, addition={"binding": deny, "edges": edges}))
    assert compare(after, Analysis(restored).run(False))["credentials"][0]["deltas"]["canonical_radius"] == -0.25

