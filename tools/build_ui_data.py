"""Generate fresh engine result inputs for the offline visual instrument."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blastradius.analysis import Analysis
from blastradius.conformance import REQUIRED_MODELS
from blastradius.model import canonical, validate
from blastradius.summary import structural_preview
from blastradius.synthetic import synth


def main():
    folder = ROOT / "ui/data"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {"visual_catalog_version": "0.1", "synthetic": True, "datasets": [], "fixtures": [], "incidents": [], "files": {}}
    def save(name, value):
        payload = canonical(value) + b"\n"
        (folder / name).write_bytes(payload)
        manifest["files"][name] = sha256(payload).hexdigest()
        return name
    def models(graph, prefix, recommendations=False):
        validate(graph)
        return {model: save(f"{prefix}-{model}.json", Analysis(graph, model).run(recommendations, 100)) for model in REQUIRED_MODELS}
    graph = synth(40, 24, 7)
    graph["organization"] = "Fictional Meridian Laboratory"
    graph["edges"] = [edge for edge in graph["edges"] if not (edge["id"].startswith("membership-") and int(edge["id"].split("-")[1]) % 3 == 0)]
    without = deepcopy(graph)
    without["edges"] = [edge for edge in without["edges"] if edge["id"] != "agent-assume-build"]
    primary = {"id": "meridian", "title": "Meridian Laboratory", "label": "Illustrative synthetic tenant", "models": models(graph, "meridian", True),
               "without_approximations": models(without, "meridian-without-assumptions"),
               "approximation_ledger": {"agent-assume-build": "Illustrative assumed trust: treat this explicitly selected synthetic edge as uncertain for the visual experiment, not as an observed platform fact."}}
    manifest["datasets"].append(primary)
    baseline = json.loads((folder / primary["models"]["default"]).read_text())
    primary["structural_summary"] = save("meridian-structural-summary.json", structural_preview(baseline))
    fixture_manifest = json.loads((ROOT / "conformance/manifest.json").read_text())
    for entry in fixture_manifest["fixtures"]:
        case = json.loads((ROOT / "conformance" / entry["file"]).read_text())
        valid = case["expected"]["default"]["status"] == "ok"
        record = {"id": case["id"], "title": case["name"], "derivation": case["derivation"], "requirements": case["requirements"], "valid": valid,
                  "graph": save(f"{case['id']}-graph.json", case["input"])}
        if valid:
            record["models"] = models(case["input"], case["id"])
        manifest["fixtures"].append(record)
    for case in json.loads((ROOT / "reconstructions/results.json").read_text())["cases"]:
        source = ROOT / "reconstructions" / case["id"]
        evidence = json.loads((source / "evidence.json").read_text())
        manifest["incidents"].append({"id": case["id"], "title": evidence["title"], "evidence": evidence,
                                      "models": models(json.loads((source / "input.json").read_text()), case["id"]),
                                      "control_models": models(json.loads((source / "control-input.json").read_text()), case["id"] + "-control")})
    manifest["conformance_reports"] = {name: save(f"conformance-{name}.json", json.loads((ROOT / "conformance/reports" / name / "report.json").read_text())) for name in ("reference", "javascript")}
    manifest["privacy_analysis"] = save("privacy-analysis.json", json.loads((ROOT / "research/privacy-results.json").read_text()))
    save_manifest = canonical(manifest) + b"\n"
    (folder / "manifest.json").write_bytes(save_manifest)
    receipt = {"executed_at": datetime.now(timezone.utc).isoformat(), "engine_result_format": "0.1 unchanged", "visual_catalog_version": "0.1", "manifest_sha256": sha256(save_manifest).hexdigest(), "engine_runs": 6 + 3*sum(case["valid"] for case in manifest["fixtures"]) + 6*len(manifest["incidents"]), "primary_credentials": len(baseline["credentials"]), "primary_statistics": baseline["statistics"]["canonical_radius"]}
    (folder / "build-receipt.json").write_bytes(canonical(receipt) + b"\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()