from copy import deepcopy
from pathlib import Path

import pytest

from blastradius.engine import Engine
from blastradius.model import GraphError, validate
from blastradius.repository import acquire_repository, collect_repository_evidence
from blastradius.repository.graph import build_repository_graph
from blastradius.synthetic import fixture


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"


def evidence():
    return collect_repository_evidence(FIXTURE, acquire_repository(FIXTURE), "acme/payments")


def test_repository_evidence_maps_to_valid_non_synthetic_graph():
    graph, evidence_index = build_repository_graph(evidence())

    assert validate(graph) is graph
    assert graph["schema_version"] == "0.2"
    assert graph["synthetic"] is False
    assert graph["source_kind"] == "repository-declared-configuration"
    assert graph["organization"] == "acme/payments"
    assert graph["observed_at"] is None
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4
    assert {node["kind"] for node in graph["nodes"]} == {"principal", "credential", "binding", "resource"}
    assert {edge["kind"] for edge in graph["edges"]} == {"authenticates_as", "can_assume", "assigned", "grants"}
    assert all(item["provenance"]["snapshot_hash"] == evidence()["repository"]["snapshot_hash"] for item in graph["nodes"] + graph["edges"])
    assert all(item["provenance"]["evidence_ref"] in evidence_index for item in graph["nodes"] + graph["edges"])

    credential = next(node["id"] for node in graph["nodes"] if node["kind"] == "credential")
    reach = Engine(graph).reach(credential)
    assert len(reach.pairs) == 1
    assert next(iter(reach.pairs))[1] == "read_secret"


def test_only_exact_complete_evidence_creates_graph():
    incomplete = evidence()
    incomplete["facts"]["oidc_role_requests"][0]["trust_match"] = "broad-potential"
    assert build_repository_graph(incomplete) == (None, {})

    incomplete = evidence()
    incomplete["facts"]["aws_secret_grants"] = []
    assert build_repository_graph(incomplete) == (None, {})


def test_duplicate_declarations_of_one_secret_keep_one_resource():
    repeated = evidence()
    duplicate = deepcopy(repeated["facts"]["aws_secret_grants"][0])
    duplicate["id"] = "aws-secret-grant-repeated"
    repeated["facts"]["aws_secret_grants"].append(duplicate)

    graph, evidence_index = build_repository_graph(repeated)

    resources = [node for node in graph["nodes"] if node["kind"] == "resource"]
    assert len(resources) == 1
    assert resources[0]["provenance"]["evidence_ref"] in evidence_index
    credential = next(node["id"] for node in graph["nodes"] if node["kind"] == "credential")
    assert len(Engine(graph).reach(credential).pairs) == 1


def test_v02_source_profile_mismatches_fail_without_changing_v01():
    graph, _ = build_repository_graph(evidence())
    wrong = deepcopy(graph)
    wrong["synthetic"] = True
    with pytest.raises(GraphError):
        validate(wrong)
    wrong = deepcopy(graph)
    del wrong["source_kind"]
    with pytest.raises(GraphError):
        validate(wrong)

    original = fixture("direct")
    assert original["schema_version"] == "0.1"
    assert validate(original) is original


def test_unknown_graph_schema_version_is_rejected():
    graph, _ = build_repository_graph(evidence())
    graph["schema_version"] = "9.9"
    with pytest.raises(GraphError, match="schema version"):
        validate(graph)


def test_workflow_jobs_do_not_pool_each_others_role_access():
    supplied = evidence()
    request = deepcopy(supplied["facts"]["oidc_role_requests"][0])
    role = deepcopy(supplied["facts"]["aws_roles"][0])
    trust = deepcopy(supplied["facts"]["aws_trusts"][0])
    grant = deepcopy(supplied["facts"]["aws_secret_grants"][0])
    role["id"], role["role_name"] = "role-documentation", "documentation"
    trust["id"], trust["role_id"] = "trust-documentation", role["id"]
    grant["id"], grant["role_id"] = "grant-documentation", role["id"]
    grant["resource_arn"] = "arn:aws:secretsmanager:us-east-1:123456789012:secret:documentation/key"
    request.update(id="request-documentation", job_id="documentation", role_arn="arn:aws:iam::123456789012:role/documentation", matching_role_ids=[role["id"]], matching_trust_ids=[trust["id"]])
    for collection, record in (("oidc_role_requests", request), ("aws_roles", role), ("aws_trusts", trust), ("aws_secret_grants", grant)):
        supplied["facts"][collection].append(record)
    graph, _ = build_repository_graph(supplied)
    engine = Engine(graph)
    for credential in (node for node in graph["nodes"] if node["kind"] == "credential"):
        pairs = engine.reach(credential["id"]).pairs
        assert len(pairs) == 1, "A compromised job must not inherit a different job's role"
        target = engine.nodes[next(iter(pairs))[0]]["name"]
        assert ("documentation/key" in target) == ("documentation" in credential["name"])
