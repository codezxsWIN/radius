"""Rebuild all demo artifacts through the public CLI and verify reproducibility."""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    commands = [
        ["synth", "--principals", "80", "--resources", "40", "--seed", "7", "--out", "results/tenant.json", "--force"],
        ["analyze", "results/tenant.json", "--constraint-model", "default", "--out", "results/result.json", "--force"],
        ["verify-manifest", "results/result.json"],
        ["report", "results/result.json", "--format", "html", "--out", "demo/index.html", "--force"],
        ["report", "results/result.json", "--format", "md", "--out", "results/report.md", "--force"],
        ["report", "results/result.json", "--format", "sarif", "--out", "results/report.sarif", "--force"],
        ["report", "results/result.json", "--format", "json", "--out", "results/report.json", "--force"],
        ["explain", "results/result.json", "--credential", "credential-principal-00001", "--out", "results/explanation.json", "--force"],
        ["whatif", "results/tenant.json", "--remove-binding", "shared-2", "--out", "results/whatif.json", "--force"],
    ]
    for arguments in commands:
        subprocess.run([sys.executable, "-B", "-m", "blastradius", *arguments], cwd=ROOT, env=environment, check=True)
    first = (ROOT / "results" / "result.json").read_bytes()
    subprocess.run([sys.executable, "-B", "-m", "blastradius", *commands[1]], cwd=ROOT, env=environment, check=True)
    if (ROOT / "results" / "result.json").read_bytes() != first:
        raise AssertionError("Repeated signed analysis was not byte-identical.")
    subprocess.run([sys.executable, "-B", str(ROOT / "tools" / "demo_script.py")], cwd=ROOT, env=environment, check=True)
    (ROOT / "results" / "demo-build-commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
    print("All public demo commands executed; HMAC verified; repeated signed output is byte-identical.")


if __name__ == "__main__":
    main()
