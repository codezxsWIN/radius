from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import socket
import subprocess

import pytest

from blastradius.engine import Engine
from blastradius.model import GraphError, canonical
from blastradius.repository import acquire_repository, analyze_repository, build_repository_graph, collect_repository_evidence
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
        "terraform_files": 0,
        "terraform_relevant_files": 0,
        "terraform_hcl_files": 0,
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


def test_literal_terraform_json_role_trust_and_policy_are_source_backed(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "deploy.yml").write_text(
        """on:
  push:
    branches: [main]
permissions:
  id-token: write
jobs:
  deploy:
    steps:
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-production
""",
        encoding="utf-8",
    )
    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {"StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                "token.actions.githubusercontent.com:sub": "repo:acme/payments:ref:refs/heads/main",
            }},
        }],
    }
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/database",
        }],
    }
    terraform = {
        "resource": {
            "aws_iam_role": {"deploy": {
                "name": "github-production",
                "assume_role_policy": json.dumps(trust),
            }},
            "aws_iam_role_policy": {"secrets": {
                "role": "github-production",
                "policy": json.dumps(policy),
            }},
        },
    }
    (tmp_path / "identity.tf.json").write_text(json.dumps(terraform, indent=2), encoding="utf-8")

    result = collect(tmp_path)

    assert result["coverage"]["terraform_files"] == 1
    assert result["coverage"]["cloudformation_files"] == 0
    assert len(result["facts"]["aws_roles"]) == 1
    assert len(result["facts"]["aws_trusts"]) == 1
    assert len(result["facts"]["aws_secret_grants"]) == 1
    assert result["facts"]["oidc_role_requests"][0]["trust_match"] == "exact-declared-configuration"
    assert all(fact["location"]["path"] == "identity.tf.json" for collection in (
        result["facts"]["aws_roles"], result["facts"]["aws_trusts"], result["facts"]["aws_secret_grants"]
    ) for fact in collection)
    graph, evidence_index = build_repository_graph(result)
    credential = next(node for node in graph["nodes"] if node["kind"] == "credential")
    assert len(Engine(graph).reach(credential["id"]).pairs) == 1
    terraform_items = [item for item in graph["nodes"] + graph["edges"] if item["provenance"]["source_api"] == "terraform-json"]
    assert terraform_items
    assert all(item["provenance"]["evidence_ref"] in evidence_index for item in terraform_items)
    analysis = analyze_repository(tmp_path, "acme/payments")
    assert analysis["summary"]["finding_count"] == 1
    assert analysis["findings"][0]["impact"]["resource_arn"].endswith(":secret:production/database")
    assert analysis["coverage"]["terraform_files"] == 1


def test_terraform_json_expressions_and_boundaries_never_create_complete_permissions(tmp_path):
    terraform = {
        "resource": {
            "aws_iam_role": {"deploy": {
                "name": "github-production",
                "permissions_boundary": "${aws_iam_policy.boundary.arn}",
                "assume_role_policy": "${data.aws_iam_policy_document.trust.json}",
            }},
            "aws_iam_role_policy": {
                "dynamic": {"role": "${aws_iam_role.deploy.name}", "policy": "${data.aws_iam_policy_document.permissions.json}"},
                "wildcard": {"role": "github-production", "policy": json.dumps({"Statement": [{
                    "Effect": "Allow",
                    "Action": "secretsmanager:GetSecretValue",
                    "Resource": "*",
                }]})},
            },
        },
    }
    (tmp_path / "identity.tf.json").write_text(json.dumps(terraform), encoding="utf-8")

    result = collect(tmp_path)

    assert result["facts"]["aws_roles"]
    assert result["facts"]["aws_trusts"] == []
    assert result["facts"]["aws_secret_grants"] == []
    codes = {item["code"] for item in result["diagnostics"]}
    assert {"UNRESOLVED_ROLE_RESTRICTION", "DYNAMIC_TERRAFORM_ROLE_REFERENCE"} <= codes


def test_malformed_terraform_policy_is_diagnostic_not_a_parser_escape(tmp_path):
    terraform = {"resource": {"aws_iam_role": {"deploy": {
        "name": "github-production",
        "assume_role_policy": "not-json",
    }}}}
    (tmp_path / "identity.tf.json").write_text(json.dumps(terraform), encoding="utf-8")

    result = collect(tmp_path)

    assert result["facts"]["aws_roles"]
    assert result["facts"]["aws_trusts"] == []
    assert any(item["code"] == "MALFORMED_TERRAFORM_POLICY" for item in result["diagnostics"])


def test_terraform_explicit_deny_in_separate_policy_suppresses_allow(tmp_path):
    trust = {"Statement": [{
        "Effect": "Allow",
        "Principal": {"Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"},
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {"StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
            "token.actions.githubusercontent.com:sub": "repo:acme/payments:ref:refs/heads/main",
        }},
    }]}
    allow = {"Statement": [{
        "Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
        "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/database",
    }]}
    deny = {"Statement": [{
        "Effect": "Deny", "Action": "secretsmanager:GetSecretValue", "Resource": "*",
    }]}
    terraform = {"resource": {
        "aws_iam_role": {"deploy": {"name": "github-production", "assume_role_policy": json.dumps(trust)}},
        "aws_iam_role_policy": {
            "allow": {"role": "github-production", "policy": json.dumps(allow)},
            "deny": {"role": "github-production", "policy": json.dumps(deny)},
        },
    }}
    (tmp_path / "identity.tf.json").write_text(json.dumps(terraform), encoding="utf-8")

    result = collect(tmp_path)

    assert result["facts"]["aws_secret_grants"] == []
    assert any(item["code"] == "EXPLICIT_DENY_UNSUPPORTED" for item in result["diagnostics"])


def test_multiple_terraform_json_files_are_visible_but_not_joined(tmp_path):
    for name in ("role.tf.json", "policy.tf.json"):
        (tmp_path / name).write_text(json.dumps({"resource": {"aws_iam_role": {}}}), encoding="utf-8")

    result = collect(tmp_path)

    assert result["coverage"]["terraform_files"] == 2
    assert result["facts"]["aws_roles"] == []
    assert sum(item["code"] == "MULTIPLE_TERRAFORM_FILES_UNSUPPORTED" for item in result["diagnostics"]) == 2
    analysis = analyze_repository(tmp_path, "acme/payments")
    gap = next(item for item in analysis["evidence_gaps"] if item["code"] == "MULTIPLE_TERRAFORM_FILES_UNSUPPORTED")
    assert "does not combine Terraform declarations" in gap["evidence_needed"]


def test_terraform_version_only_file_does_not_erase_literal_role_evidence(tmp_path):
    import shutil
    root = tmp_path / "repository"
    shutil.copytree(ROOT / "tests/fixtures/repositories/aws-oidc-terraform-json", root)
    (root / "infra/versions.tf.json").write_text(json.dumps({"terraform": {"required_version": ">= 1.5"}}))
    result = analyze_repository(root, "acme/terraform-service")
    assert len(result["findings"]) == 1
    assert result["coverage"]["terraform_files"] == 2
    assert result["coverage"]["terraform_relevant_files"] == 1
    assert not any(issue["code"] == "MULTIPLE_TERRAFORM_FILES_UNSUPPORTED" for issue in result["diagnostics"])


def test_hcl_is_counted_as_unassessed_not_silently_omitted(tmp_path):
    (tmp_path / "main.tf").write_text('resource "aws_iam_role" "deployment" {}')
    result = analyze_repository(tmp_path, "acme/example")
    assert result["coverage"]["terraform_hcl_files"] == 1
    assert result["coverage"]["out_of_profile_files"] == 1
    assert result["findings"] == []
    assert any(issue["code"] == "TERRAFORM_HCL_UNSUPPORTED" for issue in result["diagnostics"])


@pytest.mark.parametrize("restriction", ["unknown-policy", "missing-policy", "count-zero"])
def test_unresolved_terraform_restriction_cannot_leave_a_complete_allow(tmp_path, restriction):
    import shutil
    root = tmp_path / "repository"
    shutil.copytree(ROOT / "tests/fixtures/repositories/aws-oidc-terraform-json", root)
    template = root / "infra/identity.tf.json"
    document = json.loads(template.read_text())
    if restriction == "count-zero":
        document["resource"]["aws_iam_role"]["deploy"]["count"] = 0
    else:
        policy = {"role": "github-production"}
        if restriction == "unknown-policy":
            policy["policy"] = "${data.aws_iam_policy_document.restriction.json}"
        document["resource"]["aws_iam_role_policy"]["restriction"] = policy
    template.write_text(json.dumps(document))
    result = analyze_repository(root, "acme/terraform-service")
    assert result["findings"] == []
    assert result["diagnostics"]


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


def test_literal_matrix_expands_role_requests_without_merging_jobs(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    roles = ["arn:aws:iam::123456789012:role/production", "arn:aws:iam::123456789012:role/staging"]
    document = {
        "on": {"push": {"branches": ["main"]}},
        "permissions": {"id-token": "write"},
        "jobs": {"deploy": {
            "strategy": {"matrix": {"os": ["ubuntu-latest", "windows-latest"], "role": roles}},
            "runs-on": "${{ matrix.os }}",
            "steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ matrix.role }}"}}],
        }},
    }
    (workflows / "deploy.yml").write_text(json.dumps(document), encoding="utf-8")
    evidence = collect(tmp_path)
    requests = evidence["facts"]["oidc_role_requests"]
    assert len(requests) == 4
    assert len({request["job_id"] for request in requests}) == 4
    assert {request["role_arn"] for request in requests} == set(roles)
    assert all(request["base_job_id"] == "deploy" for request in requests)
    assert {request["matrix"]["os"] for request in requests} == {"ubuntu-latest", "windows-latest"}
    assert all(request["supporting_locations"][0]["kind"] == "literal-matrix" for request in requests)
    assert all("MATRIX_WORKFLOW_UNSUPPORTED" != issue["code"] for issue in evidence["diagnostics"])


def test_matrix_include_exclude_preserves_original_axes_and_overrides_added_values():
    from blastradius.repository.github_actions import _matrix_rows
    base_role = "arn:aws:iam::123456789012:role/base"
    specialized = "arn:aws:iam::123456789012:role/specialized"
    matrix = {"os": ["ubuntu", "windows"], "stage": ["staging", "production"],
              "exclude": [{"os": "windows", "stage": "production"}],
              "include": [{"role": base_role}, {"os": "ubuntu", "role": specialized}, {"os": "macos", "role": base_role}, {"os": "macos", "stage": "production", "role": specialized}]}
    root = yaml_nodes.compose_document(json.dumps({"matrix": matrix}).encode())
    rows = _matrix_rows(root)
    assert len(rows) == 5
    assert {row["role"] for row in rows if row["os"] == "ubuntu"} == {specialized}
    assert not any(row["os"] == "windows" and row.get("stage") == "production" for row in rows)
    assert len([row for row in rows if row["os"] == "macos"]) == 2


@pytest.mark.parametrize("matrix", ["${{ fromJSON(needs.generate.outputs.matrix) }}", {"os": ["${{ inputs.os }}"]}, {"os": [{"name": "ubuntu"}]}, {"one": list(range(9)), "two": list(range(8))}, {"os": []}])
def test_unsupported_or_excessive_matrix_never_yields_role_requests(tmp_path, matrix):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    document = {"on": {"push": {"branches": ["main"]}}, "permissions": {"id-token": "write"}, "jobs": {"deploy": {"strategy": {"matrix": matrix}, "steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "arn:aws:iam::123456789012:role/production"}}]}}}
    (workflows / "deploy.yml").write_text(json.dumps(document))
    evidence = collect(tmp_path)
    assert evidence["facts"]["oidc_role_requests"] == []
    assert any(issue["code"] == "MATRIX_WORKFLOW_UNSUPPORTED" for issue in evidence["diagnostics"])


def test_matrix_include_only_and_typed_exclusions():
    from blastradius.repository.github_actions import _matrix_rows
    include = {"matrix": {"include": [{"os": "ubuntu", "version": 20}, {"os": "windows", "version": 22}]}}
    assert _matrix_rows(yaml_nodes.compose_document(json.dumps(include).encode())) == include["matrix"]["include"]
    typed = {"matrix": {"version": [1, True, "1"], "exclude": [{"version": True}]}}
    assert _matrix_rows(yaml_nodes.compose_document(json.dumps(typed).encode())) == [{"version": 1}, {"version": "1"}]


def test_literal_environment_scopes_resolve_but_secrets_and_local_actions_remain_unresolved(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    document = {
        "on": {"push": {"branches": ["main"]}}, "env": {"ROLE": "arn:aws:iam::123456789012:role/top"},
        "permissions": "write-all", "jobs": {"deploy": {
            "env": {"ROLE": "arn:aws:iam::123456789012:role/job"},
            "steps": [
                {"uses": "aws-actions/configure-aws-credentials@v4", "env": {"ROLE": "arn:aws:iam::123456789012:role/step"}, "with": {"role-to-assume": "${{ env.ROLE }}", "force-skip-oidc": False}},
                {"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ secrets.ROLE_ARN }}"}},
                {"uses": "./", "with": {"role-to-assume": "${{ vars.DEPLOYMENT_ROLE }}"}},
            ],
        }},
    }
    (workflows / "deploy.yml").write_text(json.dumps(document))
    evidence = collect(tmp_path)
    assert [request["role_arn"] for request in evidence["facts"]["oidc_role_requests"]] == ["arn:aws:iam::123456789012:role/step"]
    assert evidence["facts"]["oidc_role_requests"][0]["supporting_locations"][0]["kind"] == "literal-env"
    supporting = evidence["facts"]["oidc_role_requests"][0]["supporting_locations"][0]
    assert "role/step" in json.dumps(document)[supporting["start_column"] - 1:supporting["end_column"] - 1]
    identities = evidence["facts"]["workflow_identities"]
    assert len(identities) == 3
    unknown = [identity for identity in identities if identity["status"] == "unresolved"]
    assert len(unknown) == 2
    assert {reference["context"] for identity in unknown for reference in identity["references"]} == {"secrets", "vars"}
    assert all(identity["role_arn"] is None and identity["token_permission"] == "write" for identity in unknown)
    assert any("LOCAL_ACTION_UNVERIFIED" in identity["reason_codes"] for identity in unknown)


def test_unresolved_environment_override_cannot_inherit_literal_parent_role(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    document = {"on": {"push": {"branches": ["main"]}}, "permissions": {"id-token": "write"}, "env": {"ROLE": "arn:aws:iam::123456789012:role/parent"}, "jobs": {"deploy": {"env": {"ROLE": "${{ secrets.ROLE_ARN }}"}, "steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ env.ROLE }}"}}]}}}
    (workflows / "deploy.yml").write_text(json.dumps(document))
    evidence = collect(tmp_path)
    assert evidence["facts"]["oidc_role_requests"] == []
    assert evidence["facts"]["workflow_identities"][0]["role_arn"] is None


def test_identity_limit_and_sensitive_matrix_metadata_are_bounded(tmp_path, monkeypatch):
    from blastradius.repository import github_actions
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    document = {"permissions": {"id-token": "write"}, "jobs": {"deploy": {"strategy": {"matrix": {"os": ["ubuntu", "windows"], "password": ["not-for-output"]}}, "steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ secrets.ROLE }}"}}]}}}
    (workflows / "deploy.yml").write_text(json.dumps(document))
    evidence = collect(tmp_path)
    assert b"not-for-output" not in canonical(evidence)
    assert all(identity["matrix"]["password"] == "[redacted]" for identity in evidence["facts"]["workflow_identities"])
    monkeypatch.setattr(github_actions, "MAX_IDENTITY_REQUESTS", 1)
    with pytest.raises(GraphError, match="identity-request limit"):
        collect(tmp_path)


def test_cloudformation_intrinsics_are_opaque_to_all_literal_helpers():
    for source in ("!Ref RoleName", "!Sub literal-text", "!GetAtt [Role, Arn]", "!If {condition: value}"):
        with pytest.raises(GraphError, match="custom YAML tag"):
            yaml_nodes.compose_document(source.encode())
        node = yaml_nodes.compose_document(source.encode(), allow_cloudformation_tags=True)
        assert yaml_nodes.scalar(node) is None
        assert yaml_nodes.mapping(node) is None
        assert yaml_nodes.sequence(node) is None
        assert yaml_nodes.scalar_list(node) is None
    with pytest.raises(GraphError, match="custom YAML tag"):
        yaml_nodes.compose_document(b"!Arbitrary execute", allow_cloudformation_tags=True)
    with pytest.raises(GraphError, match="mapping key"):
        yaml_nodes.compose_document(b"!Ref Key: value", allow_cloudformation_tags=True)


def test_matrix_version_strings_and_environment_scalars_remain_exact():
    from blastradius.repository.github_actions import _matrix_rows, _literal_environment
    matrix = yaml_nodes.compose_document(b"matrix: {version: [20.x, '3.12', 22], experimental: [true, false]}")
    rows = _matrix_rows(matrix)
    assert len(rows) == 6
    assert {row["version"] for row in rows} == {"20.x", "3.12", 22}
    scope = yaml_nodes.mapping(yaml_nodes.compose_document(b"env: {ACCOUNT: 123456789012, FLOAT: 1.0, TEXT: '1.0', FLAG: false}"))
    assert _literal_environment(scope) == {"ACCOUNT": "123456789012", "FLOAT": None, "TEXT": "1.0", "FLAG": "false"}
