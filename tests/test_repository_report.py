from copy import deepcopy
from pathlib import Path

import pytest

from blastradius.model import GraphError
from blastradius.repository import analyze_repository, render_repository_markdown
from blastradius.repository.report import render_repository_sarif
from blastradius.repository.view import render_repository_html, render_repository_workbench


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"


def test_positive_repository_report_is_evidence_first_and_deterministic():
    result = analyze_repository(FIXTURE, "acme/payments")
    original = deepcopy(result)

    first = render_repository_markdown(result)
    second = render_repository_markdown(result)

    assert first == second
    assert result == original
    assert "# Blast Radius Repository Analysis" in first
    assert "1 declared capabilities" in first
    assert "policy violations have not been assessed" in first
    assert "assumed compromised" in first
    assert "secretsmanager:GetSecretValue" in first
    assert "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/database" in first
    assert "authenticates_as -> can_assume -> assigned -> grants" in first
    assert ".github/workflows/deploy.yml:17:27" in first
    assert "infra/identity.template.json:11:13" in first
    assert "Before: 1 | After: 0 | Path broken: yes" in first
    assert "Deployed AWS state: unverified" in first
    assert "### Matched declarations" in first
    assert "repo:acme/payments:ref:refs/heads/main" in first
    assert "Trust audience: sts.amazonaws.com" in first
    assert "### Selected source files" in first
    assert "Inventoried files: 2" in first
    assert result["analysis_hash"] in first


def test_no_finding_report_is_not_a_safety_verdict(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    result = analyze_repository(root, "acme/repo")

    report = render_repository_markdown(result)

    assert "No complete path was proven" in report
    assert "not evidence that the repository or deployed environment is safe" in report
    assert "Findings: 0" in report


def test_report_neutralizes_untrusted_markdown_and_control_characters():
    result = analyze_repository(FIXTURE, "acme/payments")
    result["findings"][0]["title"] = "# injected\n[click](https://evil.example) `break`"
    result["diagnostics"] = [{"severity": "warning", "code": "BAD\n# HEADING", "message": "line\rbreak"}]
    result["findings"][0]["authorization"]["trust"]["subjects"] = ["[click](https://evil.example)\n# injected"]

    report = render_repository_markdown(result)

    assert "\n# injected" not in report
    assert "[click](https://evil.example)" not in report
    assert "\n# HEADING" not in report
    assert "line\rbreak" not in report


def test_report_rejects_non_repository_results():
    with pytest.raises(GraphError):
        render_repository_markdown({"profile": "wrong"})


def test_sarif_keeps_the_declared_path_evidence_and_simulation():
    result = analyze_repository(FIXTURE, "acme/payments")
    original = deepcopy(result)
    report = render_repository_sarif(result)
    assert report == render_repository_sarif(result)
    assert result == original
    assert report["version"] == "2.1.0"
    run = report["runs"][0]
    finding = run["results"][0]
    assert finding["kind"] == "review"
    assert "assumed compromised" in finding["message"]["text"]
    assert "unverified" in finding["message"]["text"]
    assert finding["locations"][0]["physicalLocation"]["region"]["startLine"] == 17
    assert finding["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == ".github/workflows/deploy.yml"
    assert finding["relatedLocations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "infra/identity.template.json"
    assert finding["properties"]["beforeAbsoluteReach"] == 1
    assert finding["properties"]["afterAbsoluteReach"] == 0
    assert finding["properties"]["remediationApplied"] is False
    assert len(finding["codeFlows"][0]["threadFlows"][0]["locations"]) >= 4
    assert run["properties"]["zeroFindingsIsNotSafety"] is True


def test_empty_sarif_still_discloses_no_proof(tmp_path):
    report = render_repository_sarif(analyze_repository(tmp_path, "acme/empty"))
    run = report["runs"][0]
    assert run["results"] == []
    assert "not evidence" in run["invocations"][0]["toolExecutionNotifications"][0]["message"]["text"]


@pytest.mark.parametrize("path", ["../private", "/etc/passwd", "C:/private", "https://example.test/a", "a\\b", "a\nfile"])
def test_sarif_rejects_unsafe_source_paths(path):
    result = analyze_repository(FIXTURE, "acme/payments")
    result["findings"][0]["path"][0]["evidence"]["location"]["path"] = path
    with pytest.raises(GraphError):
        render_repository_sarif(result)


def test_offline_html_is_deterministic_self_contained_and_neutralizes_source():
    result = analyze_repository(FIXTURE, "acme/payments")
    first = render_repository_html(result)
    assert first == render_repository_html(result)
    assert "__REVIEW_" not in first
    assert "__ATKINSON_FONT__" not in first
    assert "data:font/ttf;base64," in first
    assert "script-src 'sha256-" in first
    assert '<script src=' not in first
    assert '"mode":"snapshot"' in first
    assert '.github/workflows/deploy.yml' in first
    attack = '</script><script>globalThis.INJECTED=true</script>'
    result["findings"][0]["title"] = attack
    result["findings"][0]["start_condition"] = attack
    result["findings"][0]["path"][0]["source"]["name"] = attack
    result["findings"][0]["impact"]["resource_arn"] = '__REVIEW_SCRIPT__'
    rendered = render_repository_html(result)
    assert attack not in rendered
    assert rendered.count('<script>') == 1
    assert rendered.count('<script type="application/json"') == 1


def test_workbench_has_no_result_or_persisted_local_path():
    document = render_repository_workbench("test-session-token")
    assert '"mode":"live"' in document
    assert '"token":"test-session-token"' in document
    assert '"result":' not in document
    assert "localStorage" not in document


def test_unresolved_identity_report_does_not_promote_observations_to_findings(tmp_path):
    import json
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    workflow = {"permissions": {"id-token": "write"}, "jobs": {"deploy": {"steps": [{"uses": "aws-actions/configure-aws-credentials@v4", "with": {"role-to-assume": "${{ secrets.DEPLOY_ROLE }}"}}]}}}
    (workflows / "deploy.yml").write_text(json.dumps(workflow))
    result = analyze_repository(tmp_path, "acme/unknown")
    markdown = render_repository_markdown(result)
    assert "## Workflow identity evidence" in markdown
    assert "Identity request variants: 1" in markdown
    assert "Evidence needed to continue" in markdown
    assert "secrets.DEPLOY" in markdown
    assert "No supported IAM role declarations" in markdown
    assert "not additional vulnerability findings" in markdown
    sarif = render_repository_sarif(result)
    assert sarif["runs"][0]["results"] == []
    assert sarif["runs"][0]["properties"]["identitySummary"]["unresolved_requests"] == 1
    assert sarif["runs"][0]["properties"]["evidenceGaps"]
    result["evidence_gaps"][0]["title"] = "[unsafe](https://invalid.example)\n# heading"
    assert "[unsafe](https://invalid.example)" not in render_repository_markdown(result)
