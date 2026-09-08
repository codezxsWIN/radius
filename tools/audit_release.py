"""Check required public artifacts and archive exclusions without publishing."""

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md", "HANDOVER.md", "TEST_REPORT.md", "DECISIONS.md", "DIRECTION.md", "LICENSING.md",
    "spec/METRIC_SPECIFICATION_v1.0-draft.md", "spec/registries.json", "CONFORMANCE.md",
    "conformance/manifest.json", "conformance/reports/reference/report.json", "conformance/reports/javascript/report.json",
    "STRUCTURAL_SUMMARY.md", "PRIVACY_ANALYSIS.md", "PREREGISTRATION.md", "schema/structural-summary-v1.0-draft.schema.json",
    "research/RUN_PLAN.md", "research/reproducibility-receipt.json", "research/synthetic-summaries.jsonl", "research/privacy-results.json",
    "research/illustrative-nhi-results.json", "research/STATE_OF_BLAST_RADIUS_TEMPLATE.md", "research/DATASET_CARD.md",
    "RECONSTRUCTION_METHOD.md", "reconstructions/sources.json", "reconstructions/results.json",
    "paper/PAPER_1_DRAFT.md", "paper/RELATED_WORK.md", "paper/REFERENCES.md", "paper/SUBMISSION_PLAN.md",
    "GOVERNANCE.md", "NEUTRALITY.md", "CODE_OF_CONDUCT.md", "reference-js/reference.mjs", "reference-js/verify.mjs",
    "connectors/kubernetes_rbac/fixtures/basic.json", "connectors/kubernetes_rbac/fixtures/expected.json", "demo/index.html",
)


def forbidden(name):
    path = PurePosixPath(name.replace("\\", "/"))
    return any(part in {".venv", ".git", "__pycache__", "exports-live"} or part.startswith(".env") for part in path.parts) or path.suffix.lower() in {".key", ".pem", ".pfx", ".pdf"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--sdist", type=Path)
    arguments = parser.parse_args()
    checks = []
    for relative in REQUIRED:
        assert (ROOT / relative).is_file(), relative
        checks.append("exists:" + relative)
    manifest = json.loads((ROOT / "conformance/manifest.json").read_text())
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    suite_hash = sha256(canonical).hexdigest()
    for entry in manifest["fixtures"]:
        assert sha256((ROOT / "conformance" / entry["file"]).read_bytes()).hexdigest() == entry["sha256"]
    for name in ("reference", "javascript"):
        report = json.loads((ROOT / "conformance/reports" / name / "report.json").read_text())
        assert report["suite_hash"] == suite_hash and report["failed"] == 0 and report["passed"] == 3 * len(manifest["fixtures"])
        assert report["determinism_repetitions"] == 2
        checks.append("conformance:" + name)
    summaries = (ROOT / "research/synthetic-summaries.jsonl").read_text().splitlines()
    assert len(summaries) == 500 and all(json.loads(line)["synthetic"] is True for line in summaries)
    receipt = json.loads((ROOT / "research/reproducibility-receipt.json").read_text())
    for name, expected in receipt["outputs"].items():
        assert sha256((ROOT / "research" / name).read_bytes()).hexdigest() == expected
    assert sha256((ROOT / "PREREGISTRATION.md").read_bytes()).hexdigest() == receipt["protocol_sha256"]
    assert sha256((ROOT / "research/RUN_PLAN.md").read_bytes()).hexdigest() == receipt["run_plan_sha256"]
    checks.append("prospective-protocol-and-output-hashes")
    text = (ROOT / "spec/METRIC_SPECIFICATION_v1.0-draft.md").read_text(encoding="utf-8")
    assert {f"BR-R{number:02d}" for number in range(1, 33)} <= set(re.findall(r"BR-R\d{2}", text))
    assert len(re.findall(r"^### Theorem \d+:", text, re.MULTILINE)) == 8
    checks.append("normative-identifiers-and-eight-theorems")
    archives = []
    for path, archive_type in ((arguments.zip, "zip"), (arguments.sdist, "sdist")):
        if path is None:
            continue
        if archive_type == "zip":
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                names = [name for name in archive.namelist() if not name.endswith("/")]
                for relative in REQUIRED:
                    member = "blast-radius-v0.1/" + relative
                    assert member in names, member
                    assert archive.read(member) == (ROOT / relative).read_bytes(), member
        else:
            with tarfile.open(path) as archive:
                names = [member.name for member in archive.getmembers() if member.isfile()]
                for relative in REQUIRED:
                    assert any(name.endswith("/" + relative) for name in names), relative
        assert not [name for name in names if forbidden(name)], "Archive contains excluded material"
        archives.append({"kind": archive_type, "name": path.name, "sha256": sha256(path.read_bytes()).hexdigest(), "members": len(names), "exclusions_passed": True})
    result = {"passed_checks": len(checks), "required_artifacts": len(REQUIRED), "suite_hash": suite_hash, "synthetic_summary_count": len(summaries),
              "demo_sha256": sha256((ROOT / "demo/index.html").read_bytes()).hexdigest(), "archives": archives, "checks": checks}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
