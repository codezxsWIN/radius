from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/repository_ci.py"


def invoke(repository, output, *extra):
    return subprocess.run([sys.executable, "-I", "-B", str(RUNNER), "--repository", str(repository), "--repository-slug", "acme/payments", "--out", str(output), *extra], cwd=repository, env=dict(os.environ, PYTHONPATH=str(repository)), capture_output=True, text=True, timeout=40)


def test_ci_runner_does_not_import_or_execute_target_code(tmp_path):
    source = tmp_path / "target"
    shutil.copytree(ROOT / "tests/fixtures/repositories/aws-oidc-path", source)
    marker = tmp_path / "EXECUTED"
    malicious = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\nraise RuntimeError('Target code was executed')\n"
    for module in ("sitecustomize.py", "json.py", "yaml.py", "blastradius.py"):
        (source / module).write_text(malicious, encoding="utf-8")
    output = tmp_path / "reports"
    completed = invoke(source, output)
    assert completed.returncode == 0, completed.stderr
    assert not marker.exists()
    result = json.loads((output / "analysis.json").read_text())
    assert result["summary"]["finding_count"] == 1
    context = json.loads((output / "context.json").read_text())
    assert context["source_executed"] is False
    assert context["completion_is_not_security_assurance"] is True
    for filename, digest in context["report_sha256"].items():
        assert sha256((output / filename).read_bytes()).hexdigest() == digest
    original = (output / "analysis.json").read_bytes()
    assert invoke(source, output).returncode == 2
    assert (output / "analysis.json").read_bytes() == original
    assert invoke(source, source / "reports").returncode == 2
    assert not (source / "reports").exists()
    assert invoke(source, tmp_path / "gated", "--fail-on-findings").returncode == 1


def test_ci_runner_no_proof_and_revision_validation(tmp_path):
    source = tmp_path / "empty"
    source.mkdir()
    output = tmp_path / "reports"
    assert invoke(source, output, "--analyzer-ref", "not-a-sha").returncode == 2
    assert not output.exists()
    completed = invoke(source, output, "--fail-on-findings")
    assert completed.returncode == 0, completed.stderr
    assert "not evidence" in json.loads((output / "analysis.json").read_text())["conclusion"]


def test_ci_workflow_separates_trusted_code_and_untrusted_source():
    workflow = yaml.load((ROOT / ".github/workflows/repository-review.yml").read_text(), Loader=yaml.BaseLoader)
    assert "pull_request_target" in workflow["on"]
    assert "pull_request" not in workflow["on"]
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["review"]
    assert "base.sha" in job["env"]["ANALYZER_REVISION"]
    assert "head.sha" in job["env"]["TARGET_REVISION"]
    checkouts = [step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@")]
    assert [step["with"]["path"] for step in checkouts] == ["trusted", "target"]
    assert all(step["with"]["persist-credentials"] == "false" for step in checkouts)
    installation = next(step for step in job["steps"] if "pip install" in step.get("run", ""))
    assert '"$GITHUB_WORKSPACE/trusted"' in installation["run"]
    assert installation["working-directory"] == "${{ runner.temp }}"
    analysis = next(step for step in job["steps"] if "repository_ci.py" in step.get("run", ""))
    assert "python -I -B" in analysis["run"]
    assert analysis["working-directory"] == "${{ runner.temp }}"
    assert '"$GITHUB_WORKSPACE/trusted/tools/repository_ci.py"' in analysis["run"]
    assert '"$GITHUB_WORKSPACE/target"' in analysis["run"]
    publisher = workflow["jobs"]["publish-manual-sarif"]
    assert "workflow_dispatch" in publisher["if"] and "inputs.publish_sarif" in publisher["if"]
    assert publisher["permissions"]["security-events"] == "write"
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"[^@]+@[a-f0-9]{40}", step["uses"])