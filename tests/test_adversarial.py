from copy import deepcopy
import json
import re
import secrets

import pytest

from blastradius.analysis import Analysis, modify_binding
from blastradius.engine import Engine
from blastradius.model import GraphError, validate
from blastradius.oracle import expected
from blastradius.reports import dashboard
from blastradius.signing import sign, verify
from blastradius.synthetic import Builder, fixture


def test_actor_restricted_deny_does_not_apply_to_another_group_member():
    builder = Builder()
    builder.identity("alpha")
    builder.identity("beta")
    builder.node("group", "principal", "group")
    builder.node("resource", "resource", "database", actions=["read"], sensitivity=1)
    builder.edge("alpha-group", "member_of", "alpha", "group")
    builder.edge("beta-group", "member_of", "beta", "group")
    builder.binding("allow", "group", [("resource", ["read"])])
    builder.binding("deny", "group", [("resource", ["read"])], effect="deny")
    next(edge for edge in builder.graph["edges"] if edge["id"] == "assigned-deny")["actor_id"] = "alpha"
    engine = Engine(validate(builder.graph))
    assert engine.reach("credential-alpha").pairs == set()
    assert engine.reach("credential-beta").pairs == {("resource", "read")}
    truth = expected(builder.graph)
    assert truth["credential-alpha"]["absolute_reach"] == 0
    assert truth["credential-beta"]["absolute_reach"] == 1


def test_binding_addition_cannot_smuggle_an_assume_edge():
    graph = fixture("cycle")
    binding = deepcopy(next(node for node in graph["nodes"] if node["id"] == "allow"))
    binding["id"] = "new-binding"
    addition = {"binding": binding, "edges": [{"id": "unrelated-assume", "kind": "can_assume", "source": "alpha", "target": "beta", "provenance": binding["provenance"]}]}
    with pytest.raises(GraphError, match="unrelated escalation"):
        modify_binding(graph, addition=addition)


def test_html_placeholder_like_data_is_never_reinterpreted():
    result = sign(Analysis(fixture("direct")).run(), secrets.token_bytes(32))
    result["organization"] = 'Fictional __ROWS__ __ORGANIZATION__ __DATA__ "</script>"'
    html = dashboard(result)
    embedded = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    decoded = json.loads(embedded)
    assert decoded["organization"] == result["organization"]
    assert '<script id="report-data"' not in embedded


def test_nonfinite_sensitivity_rejected_for_in_memory_callers():
    graph = fixture("direct")
    next(node for node in graph["nodes"] if node["kind"] == "resource")["sensitivity"] = float("nan")
    with pytest.raises(GraphError, match="finite"): validate(graph)


def test_short_signing_keys_and_double_signing_are_rejected():
    result = Analysis(fixture("direct")).run()
    with pytest.raises(GraphError): sign(result, b"")
    with pytest.raises(GraphError): verify(result, b"")
    key = secrets.token_bytes(32)
    with pytest.raises(GraphError): sign(sign(result, key), key)


def test_blocked_membership_cannot_supply_secret_acquisition_authority():
    builder = Builder()
    builder.identity("alpha")
    builder.identity("beta")
    builder.node("group", "principal", "group")
    builder.node("device", "constraint", "device_required")
    builder.node("vault", "resource", "secret_store", actions=["read_secret"], sensitivity=1)
    builder.node("records", "resource", "database", actions=["read"], sensitivity=1)
    builder.binding("vault-read", "alpha", [("vault", ["read_secret"])])
    builder.binding("records-read", "beta", [("records", ["read"])])
    builder.edge("gated-membership", "member_of", "alpha", "group", constraints=["device"])
    builder.edge("group-acquires", "can_read_secret", "group", "credential-beta", requires={"resource_id": "vault", "action": "read_secret"})
    graph = validate(builder.graph)
    assert Engine(graph).reach("credential-alpha").pairs == {("vault", "read_secret")}
    assert len(Engine(graph, "permissive").reach("credential-alpha").pairs) == 2
    assert expected(graph)["credential-alpha"]["absolute_reach"] == 1
    assert expected(graph, "permissive")["credential-alpha"]["absolute_reach"] == 2


@pytest.mark.parametrize("signature", [None, [], "not-an-object"])
def test_malformed_signature_objects_fail_cleanly(signature):
    key = secrets.token_bytes(32)
    with pytest.raises(GraphError, match="signature object"):
        verify({"synthetic": True, "signature": signature}, key)


def test_nonobject_manifest_is_a_controlled_cli_rejection(tmp_path, capsys):
    from blastradius.cli import main
    path = tmp_path / "invalid-result.json"
    path.write_text("[]", encoding="utf-8")
    assert main(["verify-manifest", str(path)]) == 2
    assert "Traceback" not in capsys.readouterr().err


