from fractions import Fraction
import pytest

from blastradius.engine import Engine
from blastradius.model import validate, canonical
from blastradius.oracle import expected
from blastradius.synthetic import FIXTURE_COUNTS, fixture, synth


@pytest.mark.parametrize("name,count", FIXTURE_COUNTS.items())
def test_hand_computed_fixture(name, count):
    graph = validate(fixture(name))
    reach = Engine(graph).reach("credential-alpha")
    assert len(reach.pairs) == count
    assert Fraction(len(reach.pairs), 4) == Fraction(count, 4)
    assert reach.pairs == {tuple(pair) for pair in expected(graph)["credential-alpha"]["pairs"]}


def test_pim_activation_cost_and_approval():
    assert not Engine(fixture("pim")).reach("credential-alpha", 0).pairs
    assert len(Engine(fixture("pim")).reach("credential-alpha", 1).pairs) == 1
    assert not Engine(fixture("approval")).reach("credential-alpha").pairs
    assert len(Engine(fixture("approval"), "permissive").reach("credential-alpha").pairs) == 1


def test_secret_chain_steps_and_metadata_guard():
    graph = fixture("secret")
    assert len(Engine(graph).reach("credential-alpha", 0).pairs) == 2
    assert len(Engine(graph).reach("credential-alpha", 1).pairs) == 3
    assert len(Engine(fixture("metadata")).reach("credential-alpha").pairs) == 1


def test_generator_feature_coverage_and_determinism():
    graph = validate(synth(8, 8, 7))
    assert canonical(graph) == canonical(synth(8, 8, 7))
    assert len([node for node in graph["nodes"] if node["subtype"] == "ai_agent"]) >= 2
    assert len([node for node in graph["nodes"] if node["subtype"] == "group"]) >= 3
    assert len([node for node in graph["nodes"] if node["kind"] == "constraint"]) == 5
    truth = expected(graph)
    engine = Engine(graph)
    for credential_id, record in truth.items():
        assert engine.reach(credential_id).pairs == {tuple(pair) for pair in record["pairs"]}
