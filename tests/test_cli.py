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
