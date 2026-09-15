from copy import deepcopy
from pathlib import Path

import pytest

from blastradius.model import GraphError
from blastradius.repository import analyze_repository, render_repository_markdown


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
    assert "1 high-priority declared path" in first
    assert "assumed compromised" in first
    assert "secretsmanager:GetSecretValue" in first
    assert "arn:aws:secretsmanager:us-east-1:123456789012:secret:production/database" in first
    assert "authenticates_as -> can_assume -> assigned -> grants" in first
    assert ".github/workflows/deploy.yml:17:27" in first
    assert "infra/identity.template.json:11:13" in first
    assert "Before: 1 | After: 0 | Path broken: yes" in first
    assert "Deployed AWS state: unverified" in first
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

    report = render_repository_markdown(result)

    assert "\n# injected" not in report
    assert "[click](https://evil.example)" not in report
    assert "\n# HEADING" not in report
    assert "line\rbreak" not in report


def test_report_rejects_non_repository_results():
    with pytest.raises(GraphError):
        render_repository_markdown({"profile": "wrong"})
