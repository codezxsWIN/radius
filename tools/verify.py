"""Run the full test suite from the project folder and record real outputs."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    environment = dict(os.environ, COVERAGE_FILE=str(output / ".coverage"), PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", "-m", "pytest", "tests", "--cov=blastradius", "--cov-report=term-missing", "--cov-report=json:results/coverage.json", "--junitxml=results/junit.xml", "-q"]
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8")
    text = "COMMAND: " + " ".join(command) + "\n\n" + result.stdout + result.stderr
    (output / "pytest-output.txt").write_text(text, encoding="utf-8")
    print(text)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
