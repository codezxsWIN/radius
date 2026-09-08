from copy import deepcopy
import json
from pathlib import Path

import pytest

from blastradius.analysis import Analysis
from blastradius.cli import main
from blastradius.connectors.kubernetes_rbac import identifier, ingest, ingest_data
from blastradius.model import GraphError, canonical

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "connectors/kubernetes_rbac/fixtures/basic.json"


def bundle():
    return json.loads(FIXTURE.read_text())


def records(data=None):
    graph = ingest_data(data or bundle())
    return Analysis(graph).run(False)["credentials"]


def test_namespace_scope_secret_list_and_guarded_acquisition():
    graph = ingest(FIXTURE)
    analysis = Analysis(graph)
    observer = analysis.credential(identifier("credential", "alpha-observer-token"))
    worker = analysis.credential(identifier("credential", "beta-worker-token"))
    assert observer["absolute_reach"] == 4 and observer["universe_size"] == 6
    assert observer["exact"]["sensitivity"] == "5/8"
    assert worker["absolute_reach"] == 3 and worker["exact"]["sensitivity"] == "3/8"
    assert len(analysis.engine.reach(observer["credential_id"], 0).pairs) == 3
    assert (identifier("collection", "beta", "secrets"), "read_secret") not in analysis.engine.reach(observer["credential_id"]).pairs


def test_missing_stored_token_does_not_invent_escalation():
    data = bundle();data["metadata"]["stored_credentials"] = []
    assert max(record["absolute_reach"] for record in records(data)) == 3


def test_no_token_is_inferred_from_a_service_account_object():
    data=bundle();data["metadata"]["credential_inventory"]=[];data["metadata"]["stored_credentials"]=[]
    assert records(data)==[]


def test_rolebinding_clusterrole_is_still_local_and_cross_namespace_subject_works():
    data=bundle();data["metadata"]["stored_credentials"]=[]
    data["bindings"][0]["metadata"]["namespace"]="beta"
    graph=ingest_data(data)
    pairs=Analysis(graph).engine.reach(identifier("credential","alpha-observer-token")).pairs
    assert (identifier("collection","beta","secrets"),"read_secret") in pairs
    assert (identifier("collection","alpha","secrets"),"read_secret") not in pairs


@pytest.mark.parametrize("case",["real","secret-value","wildcard","write","named","aggregate","impersonate","bypass","external-authorizer","unresolved","subresource"])
def test_unsupported_semantics_and_values_reject(case):
    data=bundle()
    if case=="real":data["metadata"]["synthetic"]=False
    if case=="secret-value":data["metadata"]["credential_inventory"][0]["token_value"]="not-allowed"
    if case=="wildcard":data["roles"][0]["rules"][0]["resources"]=["*"]
    if case=="write":data["roles"][0]["rules"][0]["verbs"]=["create"]
    if case=="named":data["roles"][0]["rules"][0]["resourceNames"]=["specific"]
    if case=="aggregate":data["roles"][0]["aggregationRule"]={"clusterRoleSelectors":[]}
    if case=="impersonate":data["roles"][0]["rules"][0]["verbs"]=["impersonate"]
    if case=="bypass":data["bindings"][1]["subjects"][0]["name"]="system:masters"
    if case=="external-authorizer":data["metadata"]["context"]["authorizer"]="RBAC-and-webhook"
    if case=="unresolved":data["bindings"][0]["roleRef"]["name"]="missing"
    if case=="subresource":data["roles"][0]["rules"][0]["resources"]=["pods/exec"]
    with pytest.raises(GraphError):ingest_data(data)


def test_input_order_and_network_independence(monkeypatch):
    data=bundle();expected=canonical(ingest_data(data))
    data["service_accounts"].reverse();data["roles"].reverse();data["bindings"].reverse();data["metadata"]["namespaces"].reverse()
    def forbidden(*args,**kwargs):raise AssertionError("Offline adapter must not connect")
    monkeypatch.setattr("socket.socket",forbidden)
    assert canonical(ingest_data(data))==expected


def test_cli_saved_fixture_and_input_protection(tmp_path):
    destination=tmp_path/"normalized.json"
    assert main(["collect-kubernetes-rbac","--exports",str(FIXTURE),"--out",str(destination)])==0
    assert json.loads(destination.read_text())==ingest(FIXTURE)
    assert main(["collect-kubernetes-rbac","--exports",str(FIXTURE),"--out",str(FIXTURE),"--force"])==2