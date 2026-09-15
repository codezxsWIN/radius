from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys

from blastradius.cli import main
from blastradius.model import canonical
from blastradius.synthetic import fixture

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run([sys.executable, "-B", "-m", "blastradius", *map(str, args)], env=environment, capture_output=True, text=True, timeout=40)


def test_full_cli_roundtrip(tmp_path):
    tenant, result, key = (tmp_path / name for name in ("tenant.json", "result.json", "external.key"))
    generated = run_cli("synth", "--principals", 8, "--resources", 8, "--seed", 7, "--out", tenant)
    assert generated.returncode == 0, generated.stderr
    assert tenant.with_suffix(".expected.json").exists()
    arguments = ("analyze", tenant, "--signing-key", key, "--out", result)
    analyzed = run_cli(*arguments)
    assert analyzed.returncode == 0, analyzed.stderr
    initial_bytes = result.read_bytes()
    assert run_cli(*arguments, "--force").returncode == 0
    assert result.read_bytes() == initial_bytes
    assert run_cli("verify-manifest", result, "--signing-key", key).returncode == 0
    for format in ("json", "sarif", "md", "html"):
        exported = run_cli("report", result, "--signing-key", key, "--format", format, "--out", tmp_path / f"report.{format}")
        assert exported.returncode == 0, exported.stderr
    explanation = run_cli("explain", result, "--signing-key", key, "--credential", "credential-principal-00001")
    assert explanation.returncode == 0, explanation.stderr
    assert json.loads(explanation.stdout)["explanation"]
    source = tenant.read_bytes()
    scenario = run_cli("whatif", tenant, "--remove-binding", "shared-0")
    assert scenario.returncode == 0, scenario.stderr
    assert json.loads(scenario.stdout)["simulation_only"]
    assert tenant.read_bytes() == source


def test_invalid_and_overwrite_inputs(tmp_path):
    tenant = tmp_path / "tenant.json"
    tenant.write_bytes(canonical(fixture("direct")))
    key = tmp_path / "external.key"
    original = tenant.read_bytes()
    denied = run_cli("analyze", tenant, "--out", tenant, "--force", "--signing-key", key)
    assert denied.returncode == 2
    assert tenant.read_bytes() == original
    assert run_cli("synth", "--principals", 1).returncode == 2
    assert run_cli("analyze", tenant, "--steps", -1).returncode == 2
    tenant.write_text('{"synthetic":false}')
    assert run_cli("analyze", tenant).returncode == 2


def test_no_network_in_synthetic_cli(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access forbidden during synthetic execution")
    monkeypatch.setattr("socket.socket", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)
    tenant = tmp_path / "tenant.json"
    result = tmp_path / "result.json"
    key = tmp_path / "external.key"
    tenant.write_bytes(canonical(fixture("secret")))
    with redirect_stdout(StringIO()):
        assert main(["analyze", str(tenant), "--out", str(result), "--signing-key", str(key)]) == 0
        assert main(["report", str(result), "--signing-key", str(key), "--format", "html"]) == 0
        assert main(["whatif", str(tenant), "--remove-binding", "allow"]) == 0


def test_inspect_repository_cli_roundtrip_and_output_safety(tmp_path):
    repository = tmp_path / "sample-repository"
    repository.mkdir()
    (repository / "README.md").write_text("# Sample\n", encoding="utf-8")
    output = tmp_path / "repository-manifest.json"

    completed = run_cli("inspect-repo", repository, "--out", output)
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads(output.read_text(encoding="ascii"))
    assert manifest["profile"] == "safe-local-v0.1"
    assert manifest["files"][0]["path"] == "README.md"

    stdout = run_cli("inspect-repo", repository)
    assert stdout.returncode == 0, stdout.stderr
    assert json.loads(stdout.stdout) == manifest

    denied = run_cli("inspect-repo", repository, "--out", output)
    assert denied.returncode == 2
    assert run_cli("inspect-repo", repository, "--out", output, "--force").returncode == 0

    internal = repository / "manifest.json"
    refused = run_cli("inspect-repo", repository, "--out", internal)
    assert refused.returncode == 2
    assert not internal.exists()


def test_inspect_repository_cli_has_controlled_invalid_input(tmp_path):
    missing = tmp_path / "private" / "missing"
    completed = run_cli("inspect-repo", missing)
    assert completed.returncode == 2
    assert str(missing) not in completed.stderr


def test_inspect_repository_evidence_cli_roundtrip(tmp_path):
    repository = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"
    output = tmp_path / "repository-evidence.json"
    arguments = ("inspect-repo-evidence", repository, "--repository-slug", "acme/payments")

    completed = run_cli(*arguments, "--out", output)
    assert completed.returncode == 0, completed.stderr
    evidence = json.loads(output.read_text(encoding="ascii"))
    assert evidence["profile"] == "github-actions-aws-cfn-v0.1"
    assert evidence["facts"]["oidc_role_requests"][0]["trust_match"] == "exact-declared-configuration"
    assert evidence["coverage"]["deployed_aws_state"] == "unverified"

    stdout = run_cli(*arguments)
    assert stdout.returncode == 0, stdout.stderr
    assert json.loads(stdout.stdout) == evidence
    assert run_cli(*arguments, "--out", output).returncode == 2
    assert run_cli(*arguments, "--out", output, "--force").returncode == 0


def test_inspect_repository_evidence_cli_rejects_internal_output_and_bad_slug(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    internal = repository / "evidence.json"
    refused = run_cli("inspect-repo-evidence", repository, "--repository-slug", "acme/repo", "--out", internal)
    assert refused.returncode == 2
    assert not internal.exists()
    invalid = run_cli("inspect-repo-evidence", repository, "--repository-slug", "invalid")
    assert invalid.returncode == 2


def test_analyze_repository_cli_roundtrip_and_output_safety(tmp_path):
    repository = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"
    output = tmp_path / "repository-analysis.json"
    arguments = ("analyze-repo", repository, "--repository-slug", "acme/payments")

    completed = run_cli(*arguments, "--out", output)
    assert completed.returncode == 0, completed.stderr
    analysis = json.loads(output.read_text(encoding="ascii"))
    assert analysis["profile"] == "repository-attack-path-v0.1"
    assert analysis["summary"] == {"declared_reachable_secrets": 1, "finding_count": 1}

    stdout = run_cli(*arguments)
    assert stdout.returncode == 0, stdout.stderr
    assert json.loads(stdout.stdout) == analysis
    assert run_cli(*arguments, "--out", output).returncode == 2
    assert run_cli(*arguments, "--out", output, "--force").returncode == 0

    internal = repository / "repository-analysis.json"
    refused = run_cli(*arguments, "--out", internal)
    assert refused.returncode == 2
    assert not internal.exists()


def test_analyze_public_github_cli_uses_url_and_ref(monkeypatch, capsys, tmp_path):
    import blastradius.repository as repository_module

    calls = []
    expected = {"profile": "repository-attack-path-v0.1", "findings": [], "analysis_hash": "0" * 64}

    def analyze(url, ref):
        calls.append((url, ref))
        return expected

    monkeypatch.setattr(repository_module, "analyze_public_github_repository", analyze)
    assert main(["analyze-github", "https://github.com/acme/payments", "--ref", "main"]) == 0
    assert json.loads(capsys.readouterr().out) == expected
    assert calls == [("https://github.com/acme/payments", "main")]

    output = tmp_path / "github-analysis.json"
    assert main(["analyze-github", "https://github.com/acme/payments", "--out", str(output)]) == 0
    assert json.loads(output.read_text(encoding="ascii")) == expected
    assert calls[-1] == ("https://github.com/acme/payments", None)
