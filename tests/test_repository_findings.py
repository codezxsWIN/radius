from hashlib import sha256
from pathlib import Path

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
    assert finding["priority"] == "high"
    assert finding["confidence"] == "declared-configuration"
    assert "assumed compromised" in finding["start_condition"]
    assert finding["impact"]["action"] == "secretsmanager:GetSecretValue"
    assert finding["impact"]["resource_arn"].endswith(":secret:production/database")
    assert [step["kind"] for step in finding["path"]] == ["authenticates_as", "can_assume", "assigned", "grants"]
    assert all(step["evidence"]["location"]["path"] for step in finding["path"])
    assert finding["remediation"] == {
        "type": "restrict-github-oidc-trust",
        "applied": False,
        "description": "Restrict or remove the declared GitHub OIDC trust that connects this workflow to the AWS role.",
        "before_absolute_reach": 1,
        "after_absolute_reach": 0,
        "path_broken": True,
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
