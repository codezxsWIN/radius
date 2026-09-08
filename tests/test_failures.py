from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest

from blastradius.analysis import Analysis, modify_binding, compare
from blastradius.cli import main
from blastradius.connectors.entra_azure import read_exports, normalize_exports
from blastradius.connectors.transport import ReadOnlyTransport
from blastradius.engine import Engine
from blastradius.model import GraphError, read_graph, validate
from blastradius.oracle import expected
from blastradius.reports import render
from blastradius.signing import load_key
from blastradius.synthetic import fixture, synth
from test_connector import exports, rich_exports
from test_transport import Credential, Response


@pytest.mark.parametrize("case", ["wrong-kind-field", "unknown-action", "bad-credential", "wrong-relation-field", "wrong-source", "group-target", "empty-universe", "unknown-constraint", "secret-guard"])
def test_structural_and_semantic_rejections(case):
    graph = fixture("secret")
    if case == "wrong-kind-field": next(node for node in graph["nodes"] if node["kind"] == "principal")["effect"] = "allow"
    if case == "unknown-action": next(node for node in graph["nodes"] if node["kind"] == "resource")["actions"].append("undefined")
    if case == "bad-credential": next(node for node in graph["nodes"] if node["kind"] == "credential")["principal_id"] = "r0"
    if case == "wrong-relation-field": graph["edges"][0]["actions"] = ["read"]
    if case == "wrong-source": graph["edges"][0]["source"] = "r1"
    if case == "group-target": graph["edges"][0].update(kind="member_of", source="alpha", target="beta")
    if case == "empty-universe": graph["nodes"] = [node for node in graph["nodes"] if node["kind"] != "resource"]; graph["edges"] = []
    if case == "unknown-constraint": graph["edges"][0]["constraints"] = ["missing"]
    if case == "secret-guard": next(edge for edge in graph["edges"] if edge["kind"] == "can_read_secret")["requires"]["resource_id"] = "r1"
    with pytest.raises(GraphError): validate(graph)


@pytest.mark.parametrize("payload", ['{"synthetic":true,"synthetic":false}', '{"weight":NaN}', 'not-json'])
def test_bad_json_has_a_safe_error(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(payload)
    with pytest.raises(GraphError): read_graph(path)


def test_invalid_models_budgets_and_helpers(tmp_path):
    graph = fixture("direct")
    with pytest.raises(GraphError): Engine(graph, "unknown")
    with pytest.raises(GraphError): Engine(graph).reach("missing")
    with pytest.raises(GraphError): Engine(graph).reach("credential-alpha", -1)
    with pytest.raises(GraphError): Analysis(graph, steps=-1)
    with pytest.raises(GraphError): Analysis(graph, threshold=2)
    with pytest.raises(GraphError): synth(7, 8, 1)
    with pytest.raises(GraphError): synth(8, 8, -1)
    with pytest.raises(GraphError): modify_binding(graph, remove="r0")
    with pytest.raises(GraphError): modify_binding(graph)
    assert Engine(modify_binding(fixture("deny"), remove="deny")).reach("credential-alpha").pairs == {("r0", "read")}
    with pytest.raises(GraphError): render({}, "unknown")
    with pytest.raises(GraphError): render({"synthetic": False}, "html")
    key = tmp_path / "bad.key"
    key.write_bytes(b"")
    with pytest.raises(GraphError): load_key(key)


def test_cli_error_paths_are_executed_in_process(tmp_path, capsys):
    assert main(["synth", "--principals", "0"]) == 2
    assert main(["verify-manifest", str(tmp_path / "missing")]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_transport_permanent_error_and_network_exhaustion():
    url = "https://graph.microsoft.com/v1.0/users"
    def unauthorized(request, timeout): raise HTTPError(url, 403, "forbidden", {}, None)
    transport = ReadOnlyTransport(Credential(), True, SimpleNamespace(open=unauthorized), sleeper=lambda seconds: None)
    with pytest.raises(GraphError, match="403"): transport.collection(url)
    attempts = []
    def offline(request, timeout):
        attempts.append(1)
        raise URLError("offline")
    transport = ReadOnlyTransport(Credential(), True, SimpleNamespace(open=offline), sleeper=lambda seconds: None, attempts=2)
    with pytest.raises(GraphError, match="bounded retries"): transport.collection(url)
    assert len(attempts) == 2
    assert transport._delay("unparseable", 2) == 4
    assert transport._delay("120", 0) == 30


def test_transport_full_collection_uses_only_fake_get_responses():
    calls = []
    def opened(request, timeout):
        calls.append(request.full_url)
        assert request.get_method() == "GET"
        value = [{"id": "11111111-1111-4111-8111-111111111111"}] if "/groups?" in request.full_url or "/servicePrincipals?" in request.full_url else []
        return Response({"value": value}, request.full_url)
    transport = ReadOnlyTransport(Credential(), True, SimpleNamespace(open=opened))
    bundle = transport.collect("11111111-1111-4111-8111-111111111111")
    assert bundle["synthetic"] is False
    assert len(bundle["collections"]) == 15
    assert any("/members" in url for url in calls)
    assert any("/appRoleAssignments" in url for url in calls)
    assert any("2024-11-01" in url for url in calls)


def test_export_incomplete_pages_and_missing_files_fail(tmp_path):
    folder = Path(__file__).resolve().parents[1] / "connectors" / "entra_azure" / "fixtures" / "basic"
    for source in folder.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    users = tmp_path / "users.json"
    value = json.loads(users.read_text())
    value["@odata.nextLink"] = "https://graph.microsoft.com/v1.0/users?next"
    users.write_text(json.dumps(value))
    with pytest.raises(GraphError, match="incomplete page"): read_exports(tmp_path)
    users.unlink()
    with pytest.raises(GraphError, match="missing"): read_exports(tmp_path)


def test_expired_pim_does_not_create_access():
    data = rich_exports()
    data["roleEligibilityScheduleInstances"][0]["endDateTime"] = "2026-01-01T00:00:00Z"
    data["metadata"]["pim_requirements"] = {}
    result = Analysis(normalize_exports(data), "permissive").run(False)
    agent = next(record for record in result["credentials"] if record["credential_id"] == "fictional-agent-metadata")
    assert agent["absolute_reach"] == 2
