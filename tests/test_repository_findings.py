from hashlib import sha256
from pathlib import Path
import json
import shutil

import pytest

from blastradius.model import canonical
from blastradius.repository import analyze_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"


def test_repository_analysis_produces_evidence_path_and_breaking_remediation():
    first = analyze_repository(FIXTURE, "acme/payments")
    second = analyze_repository(FIXTURE, "acme/payments")

    assert canonical(first) == canonical(second)
    assert first["profile"] == "repository-attack-path-v0.1"
    assert first["repository"]["slug"] == "acme/payments"
    assert first["summary"] == {"finding_count": 1, "declared_reachable_secrets": 1}
    finding = first["findings"][0]
    assert finding["priority"] == "informational"
    assert finding["confidence"] == "declared-configuration"
    assert "assumed compromised" in finding["start_condition"]
    assert finding["impact"]["action"] == "secretsmanager:GetSecretValue"
    assert finding["impact"]["resource_arn"].endswith(":secret:production/database")
    assert [step["kind"] for step in finding["path"]] == ["authenticates_as", "can_assume", "assigned", "grants"]
    assert all(step["evidence"]["location"]["path"] for step in finding["path"])
    assert finding["remediation"] == {
        "type": "restrict-github-oidc-trust",
        "control_id": finding["authorization"]["trust"]["id"],
        "applied": False,
        "description": "Remove the selected declared GitHub OIDC trust statement from the model. All modeled uses of that statement are removed; other trust statements remain.",
        "before_absolute_reach": 1,
        "after_absolute_reach": 0,
        "path_broken": True,
        "remaining_access_unknown": False,
        "scope": "Modeled routes only; deployed access and required workload permissions remain unverified.",
    }
    assert finding["deployed_aws_state"] == "unverified"
    unsigned = {key: value for key, value in first.items() if key != "analysis_hash"}
    assert first["analysis_hash"] == sha256(canonical(unsigned)).hexdigest()


def test_no_complete_path_is_not_reported_as_safe(tmp_path):
    root = tmp_path / "repo"
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\non: push\njobs: {}\n", encoding="utf-8")

    result = analyze_repository(root, "acme/repo")
    assert result["findings"] == []
    assert result["summary"] == {"finding_count": 0, "declared_reachable_secrets": 0}
    assert result["conclusion"] == "No complete path was proven within the supported repository profile; this is not evidence that the repository or deployed environment is safe."
    assert result["coverage"]["deployed_aws_state"] == "unverified"


def test_repository_analysis_does_not_modify_source_files():
    before = {path.relative_to(FIXTURE).as_posix(): path.read_bytes() for path in FIXTURE.rglob("*") if path.is_file()}
    analyze_repository(FIXTURE, "acme/payments")
    after = {path.relative_to(FIXTURE).as_posix(): path.read_bytes() for path in FIXTURE.rglob("*") if path.is_file()}
    assert before == after


@pytest.mark.parametrize("targets", [["github-production"], [{"Ref": "GitHubProductionRole"}]])
def test_separately_attached_deny_cannot_disappear(tmp_path, targets):
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    template = root / "infra/identity.template.json"
    document = json.loads(template.read_text())
    document["Resources"]["RestrictSecret"] = {
        "Type": "AWS::IAM::Policy",
        "Properties": {"PolicyName": "RestrictSecret", "Roles": targets, "PolicyDocument": {
            "Statement": [{"Effect": "Deny", "Action": "secretsmanager:GetSecretValue", "Resource": "*"}],
        }},
    }
    template.write_text(json.dumps(document))
    result = analyze_repository(root, "acme/payments")
    assert result["findings"] == []
    assert any(issue["code"] in {"EXPLICIT_DENY_UNSUPPORTED", "UNRESOLVED_POLICY_ATTACHMENT"} for issue in result["diagnostics"])
    assert result["evidence_gaps"]


def test_literal_attached_policy_retains_its_source(tmp_path):
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    template = root / "infra/identity.template.json"
    document = json.loads(template.read_text())
    properties = document["Resources"]["GitHubProductionRole"]["Properties"]
    policy = properties.pop("Policies")[0]
    document["Resources"]["AttachedRead"] = {"Type": "AWS::IAM::Policy", "Properties": {**policy, "Roles": [properties["RoleName"]]}}
    template.write_text(json.dumps(document, indent=2))
    result = analyze_repository(root, "acme/payments")
    assert len(result["findings"]) == 1
    source = result["findings"][0]["authorization"]["permission"]["location"]
    assert source["path"] == "infra/identity.template.json"
    assert source["start_line"] > template.read_text().splitlines().index('    "AttachedRead": {')


def test_iam_action_capitalization_preserves_semantics_and_source_spelling(tmp_path):
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    template = root / "infra/identity.template.json"
    template.write_text(template.read_text().replace("secretsmanager:GetSecretValue", "SecretsManager:GetSecretValue").replace("sts:AssumeRoleWithWebIdentity", "STS:assumerolewithwebidentity"))
    result = analyze_repository(root, "acme/payments")
    assert len(result["findings"]) == 1
    authorization = result["findings"][0]["authorization"]
    assert "SecretsManager:GetSecretValue" in authorization["permission"]["declared_actions"]
    assert "STS:assumerolewithwebidentity" in authorization["trust"]["declared_actions"]
    assert authorization["permission"]["provider_action"] == "secretsmanager:GetSecretValue"


@pytest.mark.parametrize("case", ["deny", "boundary", "trust-extra-condition", "trust-deny", "environment", "ambiguous-role", "wrong-account", "wrong-role-path", "managed-policy", "conditional-role", "session-policy"])
def test_unresolved_restrictions_do_not_produce_a_proven_path(tmp_path, case):
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    template = root / "infra/identity.template.json"
    document = json.loads(template.read_text())
    role = document["Resources"]["GitHubProductionRole"]
    properties = role["Properties"]
    trust = properties["AssumeRolePolicyDocument"]["Statement"]
    grants = properties["Policies"][0]["PolicyDocument"]["Statement"]
    if case == "deny":
        grants.append({"Effect": "Deny", "Action": "secretsmanager:GetSecretValue", "Resource": "*"})
    elif case == "boundary":
        properties["PermissionsBoundary"] = "arn:aws:iam::123456789012:policy/restrictive-boundary"
    elif case == "trust-extra-condition":
        trust[0]["Condition"]["StringEquals"]["aws:PrincipalTag/reviewed"] = "yes"
    elif case == "trust-deny":
        trust.append({"Effect": "Deny", "Principal": "*", "Action": "sts:AssumeRoleWithWebIdentity"})
    elif case == "environment":
        workflow = root / ".github/workflows/deploy.yml"
        workflow.write_text(workflow.read_text().replace("    runs-on:", "    environment: production\n    runs-on:"))
    elif case == "ambiguous-role":
        document["Resources"]["ConflictingSameName"] = json.loads(json.dumps(role))
    elif case == "wrong-account":
        trust[0]["Principal"]["Federated"] = "arn:aws:iam::999999999999:oidc-provider/token.actions.githubusercontent.com"
    elif case == "wrong-role-path":
        properties["Path"] = "/different/"
    elif case == "managed-policy":
        properties["ManagedPolicyArns"] = ["arn:aws:iam::123456789012:policy/restrictive-policy"]
    elif case == "conditional-role":
        role["Condition"] = "OnlyInProduction"
    elif case == "session-policy":
        workflow = root / ".github/workflows/deploy.yml"
        workflow.write_text(workflow.read_text().replace("          aws-region:", "          managed-session-policies: arn:aws:iam::123456789012:policy/restricted\n          aws-region:"))
    template.write_text(json.dumps(document))
    result = analyze_repository(root, "acme/payments")
    assert result["findings"] == []
    assert result["diagnostics"]
    assert "not evidence" in result["conclusion"]


def test_trust_removal_covers_every_use_in_the_same_job(tmp_path):
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    workflow = root / ".github/workflows/deploy.yml"
    text = workflow.read_text()
    step = text[text.index("      - name: Configure AWS credentials"):]
    workflow.write_text(text + step)
    result = analyze_repository(root, "acme/payments")
    assert len(result["findings"]) == 2
    assert all(finding["remediation"]["path_broken"] for finding in result["findings"])
    assert all(finding["remediation"]["after_absolute_reach"] == 0 for finding in result["findings"])


def test_review_exposes_the_matched_authorization_conditions():
    finding = analyze_repository(FIXTURE, "acme/payments")["findings"][0]
    authorization = finding["authorization"]
    assert authorization["workflow"]["job_id"] == "deploy"
    assert authorization["workflow"]["branches"] == ["main"]
    assert authorization["trust"]["subjects"] == ["repo:acme/payments:ref:refs/heads/main"]
    assert authorization["trust"]["audience"] == ["sts.amazonaws.com"]
    assert authorization["trust"]["provider_accounts"] == ["123456789012"]
    assert authorization["trust"]["location"]["start_line"] == 11
    assert authorization["permission"]["provider_action"] == "secretsmanager:GetSecretValue"
    assert authorization["permission"]["location"]["start_line"] == 32
    assert finding["remediation"]["control_id"] == authorization["trust"]["id"]


def test_change_set_preserves_alternate_trust_and_recomputes_shared_jobs(tmp_path):
    from copy import deepcopy
    from blastradius.repository.scenarios import simulate_repository_review, render_change_request
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    workflow = root / ".github/workflows/deploy.yml"
    original_workflow = workflow.read_text()
    second_job = original_workflow[original_workflow.index("  deploy:"):].replace("  deploy:", "  verify:", 1)
    workflow.write_text(original_workflow + second_job)
    template = root / "infra/identity.template.json"
    document = json.loads(template.read_text())
    statements = document["Resources"]["GitHubProductionRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"]
    alternate = deepcopy(statements[0])
    alternate["Sid"] = "IndependentTrust"
    statements.append(alternate)
    template.write_text(json.dumps(document))
    context = {}
    result = analyze_repository(root, "acme/payments", review_context=context)
    before = deepcopy((result, context))
    controls = [control["id"] for control in result["controls"]]
    assert len(controls) == 2
    assert len(result["findings"]) == 2
    assert all(len(control["jobs"]) == 2 for control in result["controls"])
    unchanged = simulate_repository_review(result, context, [])
    assert unchanged["before"] == unchanged["after"]
    partial = simulate_repository_review(result, context, controls[:1])
    assert partial["blocked_findings"] == 0
    assert all(state["remaining_controls"] == controls[1:] for state in partial["finding_states"])
    complete = simulate_repository_review(result, context, controls)
    assert complete["after"] == {"reachable_findings": 0, "reachable_secrets": 0, "reachable_jobs": 0}
    assert complete["blocked_findings"] == 2
    assert complete == simulate_repository_review(result, context, list(reversed(controls)))
    assert (result, context) == before
    assert "2 -> 0" in render_change_request(complete)
    assert "not an executable patch" in render_change_request(complete)
    for invalid in (["unrecognized"], controls * 2, "all", [None]):
        with pytest.raises(Exception, match="trust control"):
            simulate_repository_review(result, context, invalid)


def test_unmodeled_wildcard_alternative_survives_exact_trust_simulation(tmp_path):
    from copy import deepcopy
    from blastradius.repository.scenarios import simulate_repository_review, render_change_request
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    template = root / "infra/identity.template.json"
    document = json.loads(template.read_text())
    trusts = document["Resources"]["GitHubProductionRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"]
    alternate = deepcopy(trusts[0])
    alternate["Condition"]["StringEquals"].pop("token.actions.githubusercontent.com:sub")
    alternate["Condition"]["StringLike"] = {"token.actions.githubusercontent.com:sub": "repo:acme/payments:*"}
    trusts.append(alternate)
    template.write_text(json.dumps(document))
    context = {}
    result = analyze_repository(root, "acme/payments", review_context=context)
    finding = result["findings"][0]
    assert finding["classification"] == "declared-capability"
    assert finding["priority"] == "informational"
    assert finding["remediation"]["after_absolute_reach"] == 0
    assert finding["remediation"]["remaining_access_unknown"] is True
    assert finding["unmodeled_alternatives"][0]["subjects"] == ["repo:acme/payments:*"]
    comparison = simulate_repository_review(result, context, [finding["remediation"]["control_id"]])
    assert comparison["remaining_access_unknown"] is True
    assert comparison["finding_states"][0]["remaining_access_unknown"] is True
    assert "remaining access unknown" in render_change_request(comparison)


@pytest.mark.parametrize(("job_count", "secret_count"), [(8, 8), (32, 16)])
def test_shared_control_simulations_validate_once_per_distinct_change(tmp_path, monkeypatch, job_count, secret_count):
    from time import perf_counter
    from blastradius.repository import findings as implementation
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    workflow = {"on": {"push": {"branches": ["main"]}}, "permissions": {"id-token": "write"}, "jobs": {"deploy": {"strategy": {"matrix": {"job": list(range(job_count))}}, "steps": [{"uses": "aws-actions/configure-aws-credentials@v5", "with": {"role-to-assume": "arn:aws:iam::123456789012:role/github-production"}}]}}}
    (root / ".github/workflows/deploy.yml").write_text(json.dumps(workflow))
    template = root / "infra/identity.template.json"
    document = json.loads(template.read_text())
    statement = document["Resources"]["GitHubProductionRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"][0]
    statement["Resource"] = [f"arn:aws:secretsmanager:us-east-1:123456789012:secret:production/secret-{index}" for index in range(secret_count)]
    template.write_text(json.dumps(document))
    validations = []
    original = implementation.validate

    def counted(graph):
        validations.append(len(graph["edges"]))
        return original(graph)

    monkeypatch.setattr(implementation, "validate", counted)
    started = perf_counter()
    result = analyze_repository(root, "acme/payments")
    elapsed = perf_counter() - started
    assert len(result["findings"]) == job_count * secret_count
    assert len(validations) == 1
    assert all(finding["remediation"]["after_absolute_reach"] == 0 for finding in result["findings"])
    assert elapsed < 10, "Repository-shaped analysis exceeded its 10-second regression budget"
    print(json.dumps({"jobs": job_count, "secrets": secret_count, "findings": len(result["findings"]), "analysis_seconds": elapsed, "result_bytes": len(canonical(result))}))


def test_review_reports_parser_scope_and_skipped_inputs(tmp_path):
    (tmp_path / "README.md").write_text("unrelated source")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "bad.cfn.json").write_text("{")
    result = analyze_repository(tmp_path, "acme/review")
    assert result["coverage"]["inventory_files"] == 2
    assert result["coverage"]["out_of_profile_files"] == 1
    assert result["coverage"]["skipped_entries"] == 1
    assert result["source_files"][0]["status"] == "unparsed"
    assert result["source_files"][0]["diagnostic_count"] == 1
    assert result["skipped_inputs"][0]["path"] == "node_modules"


def test_same_job_role_requests_show_the_correlated_role_not_start_credential(tmp_path):
    root = tmp_path / "repository"
    shutil.copytree(ROOT / "tests/fixtures/repositories/aws-oidc-shared", root)
    workflow = root / ".github/workflows/deploy.yml"
    steps = [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": f"arn:aws:iam::123456789012:role/{role_name}"}} for role_name in ("github-publisher", "github-production")]
    workflow.write_text(json.dumps({"name": "Combined deployment", "on": {"push": {"branches": ["main", "release"]}}, "permissions": {"id-token": "write"}, "jobs": {"deploy": {"runs-on": "ubuntu-latest", "steps": steps}}}))
    result = analyze_repository(root, "acme/release-platform")
    assert len(result["findings"]) == 6, result["diagnostics"]
    for finding in result["findings"]:
        authorization = finding["authorization"]
        role_name = authorization["workflow"]["role_arn"].split("/")[-1]
        expected = "github-publisher" if "packages/registry-token" in finding["impact"]["resource_arn"] else "github-production"
        assert role_name == expected
        correlation = next(step["evidence"] for step in finding["path"] if step["kind"] == "can_assume")
        assert authorization["workflow"]["location"] == correlation["location"]


def test_unresolved_identities_produce_specific_evidence_requests_not_findings(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    workflow = {"on": "workflow_dispatch", "permissions": {"id-token": "write"}, "jobs": {"deploy": {"strategy": {"matrix": {"os": ["ubuntu", "windows"]}}, "steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ secrets.DEPLOY_ROLE }}"}}]}}}
    (workflows / "deploy.yml").write_text(json.dumps(workflow))
    result = analyze_repository(tmp_path, "acme/repo")
    assert result["findings"] == []
    assert result["identity_summary"]["identity_requests"] == 2
    assert result["identity_summary"]["expanded_job_variants"] == 2
    assert result["identity_summary"]["unresolved_requests"] == 2
    assert result["identity_summary"]["unresolved_matrix_jobs"] == 0
    gaps = {gap["code"]: gap for gap in result["evidence_gaps"]}
    assert gaps["DYNAMIC_ROLE_ARN"]["references"] == [{"context": "secrets", "name": "DEPLOY_ROLE", "field": "role-to-assume"}]
    assert "Do not provide access keys" in gaps["DYNAMIC_ROLE_ARN"]["evidence_needed"]
    assert "IAM_DECLARATIONS_REQUIRED" in gaps
    assert "not evidence" in result["conclusion"]


def test_matrix_variants_never_pool_distinct_role_permissions(tmp_path):
    root = tmp_path / "repository"
    shutil.copytree(ROOT / "tests/fixtures/repositories/aws-oidc-shared", root)
    roles = ["arn:aws:iam::123456789012:role/github-publisher", "arn:aws:iam::123456789012:role/github-production"]
    workflow = {"on": {"push": {"branches": ["main"]}}, "permissions": {"id-token": "write"}, "jobs": {"deploy": {"strategy": {"matrix": {"role": roles}}, "steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ matrix.role }}"}}]}}}
    (root / ".github/workflows/deploy.yml").write_text(json.dumps(workflow))
    result = analyze_repository(root, "acme/release-platform")
    assert len(result["findings"]) == 3
    for finding in result["findings"]:
        requested = finding["authorization"]["workflow"]
        assert requested["base_job_id"] == "deploy"
        assert requested["matrix"]["role"] == requested["role_arn"]
        expected = "github-publisher" if "packages/registry-token" in finding["impact"]["resource_arn"] else "github-production"
        assert requested["role_arn"].endswith(expected)


@pytest.mark.parametrize("relative", ["template.yaml", "infra/identity.cfn.yml", "cloudformation/roles.yaml", "infra/template.json"])
def test_conventional_cloudformation_files_are_selected_without_executing_intrinsics(tmp_path, relative):
    import yaml
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    original = root / "infra/identity.template.json"
    document = json.loads(original.read_text())
    original.unlink()
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document) if target.suffix == ".json" else yaml.safe_dump(document, sort_keys=False))
    result = analyze_repository(root, "acme/payments")
    assert len(result["findings"]) == 1
    assert result["findings"][0]["authorization"]["trust"]["location"]["path"] == relative


def test_cloudformation_tagged_values_never_become_literal_permissions(tmp_path):
    import yaml
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root)
    original = root / "infra/identity.template.json"
    document = json.loads(original.read_text())
    original.unlink()
    literal = yaml.safe_dump(document, sort_keys=False)
    target = root / "template.yaml"
    target.write_text(literal.replace("RoleName: github-production", "RoleName: !Sub github-production"))
    result = analyze_repository(root, "acme/payments")
    assert result["findings"] == []
    assert any(issue["code"] == "CLOUDFORMATION_INTRINSICS_UNEVALUATED" for issue in result["diagnostics"])
    assert any(issue["code"] == "DYNAMIC_ROLE_NAME" for issue in result["diagnostics"])
    target.write_text(literal + "Metadata: !Sub retained-without-evaluation\n")
    result = analyze_repository(root, "acme/payments")
    assert len(result["findings"]) == 1
    assert next(record for record in result["source_files"] if record["path"] == "template.yaml")["status"] == "partial"
