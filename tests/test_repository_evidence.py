from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import socket
import subprocess

import pytest

from blastradius.model import GraphError, canonical
from blastradius.repository import acquire_repository, collect_repository_evidence
from blastradius.repository import yaml_nodes


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"


def collect(root=FIXTURE, slug="acme/payments"):
    return collect_repository_evidence(root, acquire_repository(root), slug)


def test_positive_evidence_is_deterministic_source_backed_and_honest():
    first = collect()
    second = collect()

    assert canonical(first) == canonical(second)
    assert first["profile"] == "github-actions-aws-cfn-v0.1"
    assert first["repository"]["slug"] == "acme/payments"
    assert first["coverage"] == {
        "selected_files": 2,
        "parsed_files": 2,
        "unsupported_files": 0,
        "workflow_files": 1,
        "cloudformation_files": 1,
        "deployed_aws_state": "unverified",
    }
    assert len(first["facts"]["workflows"]) == 1
    request = first["facts"]["oidc_role_requests"][0]
    assert request["role_arn"] == "arn:aws:iam::123456789012:role/github-production"
    assert request["branches"] == ["main"]
    assert request["audience"] == "sts.amazonaws.com"
    assert request["confidence"] == "repository-verified"
    assert request["trust_match"] == "exact-declared-configuration"
    assert len(request["matching_role_ids"]) == 1
    assert len(request["matching_trust_ids"]) == 1

    trust = first["facts"]["aws_trusts"][0]
    assert trust["subjects"] == ["repo:acme/payments:ref:refs/heads/main"]
    assert trust["broad"] is False
    assert trust["confidence"] == "declared-configuration"
    grant = first["facts"]["aws_secret_grants"][0]
    assert grant["action"] == "read_secret"
    assert grant["resource_arn"].endswith(":secret:production/database")
    assert grant["confidence"] == "declared-configuration"

    locations = [request["location"], trust["location"], grant["location"]]
    assert all(item["path"] and item["start_line"] >= 1 and item["start_column"] >= 1 for item in locations)
    assert all(not Path(item["path"]).is_absolute() for item in locations)
    unsigned = {key: value for key, value in first.items() if key != "evidence_hash"}
    assert first["evidence_hash"] == sha256(canonical(unsigned)).hexdigest()
    assert str(FIXTURE) not in json.dumps(first)


def test_changed_snapshot_fails_closed(tmp_path):
    root = tmp_path / "repo"
    workflow = root / ".github" / "workflows"
    workflow.mkdir(parents=True)
    target = workflow / "deploy.yml"
    target.write_text("name: first\n", encoding="utf-8")
    manifest = acquire_repository(root)
    target.write_text("name: changed\n", encoding="utf-8")

    with pytest.raises(GraphError, match="snapshot changed"):
        collect_repository_evidence(root, manifest, "acme/repo")


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("name: one\nname: two\n", "duplicate"),
        ("base: &base {id-token: write}\npermissions: *base\n", "alias"),
        ("value: !Danger anything\n", "custom YAML tag"),
        ("permissions:\n  <<: {id-token: write}\n", "merge key"),
    ],
)
def test_unsafe_yaml_features_fail_the_collection(tmp_path, source, message):
    root = tmp_path / "repo"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "unsafe.yml").write_text(source, encoding="utf-8")

    with pytest.raises(GraphError, match=message):
        collect_repository_evidence(root, acquire_repository(root), "acme/repo")


def test_yaml_node_and_depth_limits_fail_closed(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    target = workflows / "limits.yml"
    target.write_text("name: demo\non: push\njobs: {}\n", encoding="utf-8")
    manifest = acquire_repository(root)

    monkeypatch.setattr(yaml_nodes, "MAX_DOCUMENT_NODES", 2)
    with pytest.raises(GraphError, match="node-count limit"):
        collect_repository_evidence(root, manifest, "acme/repo")

    monkeypatch.setattr(yaml_nodes, "MAX_DOCUMENT_NODES", 20_000)
    monkeypatch.setattr(yaml_nodes, "MAX_DOCUMENT_DEPTH", 1)
    with pytest.raises(GraphError, match="depth limit"):
        collect_repository_evidence(root, manifest, "acme/repo")


def test_missing_token_permission_and_dynamic_role_are_diagnostics(tmp_path):
    root = tmp_path / "repo"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "dynamic.yml").write_text(
        """name: Dynamic
on: push
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ secrets.ROLE_ARN }}
""",
        encoding="utf-8",
    )

    result = collect_repository_evidence(root, acquire_repository(root), "acme/repo")
    assert result["facts"]["oidc_role_requests"] == []
    codes = {item["code"] for item in result["diagnostics"]}
    assert codes == {"DYNAMIC_ROLE_ARN", "OIDC_PERMISSION_MISSING"}


def test_broad_trust_is_potential_and_wildcard_secret_is_not_a_finite_grant(tmp_path):
    root = tmp_path / "repo"
    workflow = root / ".github" / "workflows"
    workflow.mkdir(parents=True)
    (workflow / "deploy.yml").write_text(
        """name: Deploy
on:
  push:
    branches: [main]
permissions:
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: arn:aws:iam::123456789012:role/broad-role
""",
        encoding="utf-8",
    )
    infra = root / "infra"
    infra.mkdir()
    template = {
        "Resources": {
            "BroadRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": "broad-role",
                    "AssumeRolePolicyDocument": {
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"},
                            "Action": "sts:AssumeRoleWithWebIdentity",
                            "Condition": {
                                "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
                                "StringLike": {"token.actions.githubusercontent.com:sub": "repo:acme/*"},
                            },
                        }],
                    },
                    "Policies": [{
                        "PolicyName": "Wildcard",
                        "PolicyDocument": {"Statement": [{
                            "Effect": "Allow",
                            "Action": "secretsmanager:GetSecretValue",
                            "Resource": "*",
                        }]},
                    }],
                },
            },
        },
    }
    (infra / "identity.template.json").write_text(json.dumps(template), encoding="utf-8")

    result = collect_repository_evidence(root, acquire_repository(root), "acme/repo")
    assert result["facts"]["aws_trusts"][0]["confidence"] == "potential"
    assert result["facts"]["aws_trusts"][0]["broad"] is True
    assert result["facts"]["aws_secret_grants"] == []
    assert result["facts"]["oidc_role_requests"][0]["trust_match"] == "broad-potential"
    codes = {item["code"] for item in result["diagnostics"]}
    assert "BROAD_GITHUB_TRUST" in codes
    assert "NONFINITE_SECRET_RESOURCE" in codes


def test_malformed_selected_file_is_reported_without_hiding_valid_files(tmp_path):
    root = tmp_path / "repo"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "bad.yml").write_text("jobs: [", encoding="utf-8")
    (workflows / "valid.yml").write_text("name: Valid\non: push\njobs: {}\n", encoding="utf-8")

    result = collect_repository_evidence(root, acquire_repository(root), "acme/repo")
    assert result["coverage"]["selected_files"] == 2
    assert result["coverage"]["parsed_files"] == 1
    assert result["coverage"]["unsupported_files"] == 1
    assert result["diagnostics"][0]["code"] == "MALFORMED_DOCUMENT"


def test_evidence_collection_does_not_execute_or_use_network(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    marker = tmp_path / "executed"
    (workflows / "data.yml").write_text(
        f"name: ${{{{ Path({str(marker)!r}).write_text('bad') }}}}\non: push\njobs: {{}}\n",
        encoding="utf-8",
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Evidence collection cannot execute subprocesses or use the network.")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    result = collect_repository_evidence(root, acquire_repository(root), "acme/repo")
    assert result["facts"]["workflows"]
    assert not marker.exists()


def test_invalid_manifest_and_slug_are_rejected():
    manifest = acquire_repository(FIXTURE)
    changed = deepcopy(manifest)
    changed["snapshot_hash"] = "0" * 64
    with pytest.raises(GraphError, match="manifest"):
        collect_repository_evidence(FIXTURE, changed, "acme/payments")
    with pytest.raises(GraphError, match="slug"):
        collect_repository_evidence(FIXTURE, manifest, "not-a-slug")
