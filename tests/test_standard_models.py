from copy import deepcopy
import pytest

from blastradius.engine import Engine
from blastradius.model import validate, GraphError
from blastradius.synthetic import fixture, Builder


def token_fixture():
    builder = Builder()
    builder.graph = fixture("direct")
    credential = next(node for node in builder.graph["nodes"] if node["kind"] == "credential")
    credential.update(subtype="token", session_satisfied_constraints=["device_required"])
    builder.node("completed-device", "constraint", "device_required")
    next(edge for edge in builder.graph["edges"] if edge["kind"] == "authenticates_as")["constraints"] = ["completed-device"]
    return validate(builder.graph)


def test_session_model_only_reuses_explicit_completed_authentication():
    graph = token_fixture()
    assert not Engine(graph, "default").reach("credential-alpha").pairs
    assert not Engine(graph, "strict").reach("credential-alpha").pairs
    assert len(Engine(graph, "session-theft-aware").reach("credential-alpha").pairs) == 1
    unclaimed = deepcopy(graph)
    next(node for node in unclaimed["nodes"] if node["kind"] == "credential")["session_satisfied_constraints"] = []
    assert not Engine(unclaimed, "session-theft-aware").reach("credential-alpha").pairs


def test_session_model_does_not_waive_access_controls_or_approval():
    graph = token_fixture()
    next(node for node in graph["nodes"] if node["id"] == "allow")["constraints"] = ["completed-device"]
    assert not Engine(graph, "session-theft-aware").reach("credential-alpha").pairs
    graph = token_fixture()
    next(node for node in graph["nodes"] if node["id"] == "completed-device")["subtype"] = "approval_required"
    assert not Engine(graph, "session-theft-aware").reach("credential-alpha").pairs


def test_password_cannot_claim_a_precompleted_session_factor():
    graph = token_fixture()
    next(node for node in graph["nodes"] if node["kind"] == "credential")["subtype"] = "password"
    with pytest.raises(GraphError): validate(graph)
