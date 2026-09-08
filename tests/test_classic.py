import pytest

from blastradius.engine import Engine
from blastradius.synthetic import classic


@pytest.fixture(scope="module")
def classic_engine():
    return Engine(classic())


@pytest.mark.parametrize("credential_id,count", [("credential-finance", 1240), ("credential-cicd", 9600), ("credential-legacy", 31200), ("credential-copilot", 14400)])
def test_classic_worked_example_exact_cardinalities(classic_engine, credential_id, count):
    graph = classic_engine.graph
    universe = sum(len(node["actions"]) for node in graph["nodes"] if node["kind"] == "resource")
    assert universe == 48000
    assert len(classic_engine.reach(credential_id).pairs) == count
