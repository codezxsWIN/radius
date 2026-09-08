"""Run the actual wheel outside the source tree with isolated Python."""

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheel = ROOT / "dist/blastradius_prototype-0.1.0-py3-none-any.whl"
    uv = shutil.which("uv")
    assert uv and wheel.is_file()
    environment = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}}
    with tempfile.TemporaryDirectory(prefix="blastradius-wheel-check-") as directory:
        working = Path(directory)
        virtual = working / "environment"
        subprocess.run([uv, "venv", "--offline", "--python", "3.12", str(virtual)], check=True, env=environment, cwd=working)
        python = virtual / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([uv, "pip", "install", "--offline", "--python", str(python), str(wheel)], check=True, env=environment, cwd=working)
        manifest = json.loads((ROOT / "conformance/manifest.json").read_text())
        count = 0
        for entry in manifest["fixtures"]:
            fixture = json.loads((ROOT / "conformance" / entry["file"]).read_text())
            for model in manifest["required_models"]:
                request = {"contract_version": "1.0-draft", "input": fixture["input"], "parameters": {"constraint_model": model, "step_bound": fixture["step_bound"], "threshold": "1/4"}}
                process = subprocess.run([str(python), "-I", "-B", "-m", "blastradius", "conformance", "adapter"], input=json.dumps(request).encode(), capture_output=True, check=True, cwd=working, env=environment)
                assert json.loads(process.stdout) == fixture["expected"][model], (fixture["id"], model)
                count += 1
        export = ROOT / "connectors/kubernetes_rbac/fixtures/basic.json"
        process = subprocess.run([str(python), "-I", "-B", "-m", "blastradius", "collect-kubernetes-rbac", "--exports", str(export)], capture_output=True, check=True, cwd=working, env=environment)
        assert json.loads(process.stdout) == json.loads((export.parent / "normalized.json").read_text())
        result = {"wheel": wheel.name, "wheel_sha256": sha256(wheel.read_bytes()).hexdigest(), "isolated_python": True, "outside_source_tree": True, "public_cases_passed": count, "kubernetes_normalization": "pass", "network_dependencies": "offline cache only"}
    (ROOT / "results/wheel-smoke.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
