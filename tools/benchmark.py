"""Record the full synthetic build/validation/analysis/serialization workload."""

import argparse
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blastradius.analysis import Analysis
from blastradius.model import canonical, validate
from blastradius.synthetic import synth, classic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--principals", type=int, default=10000)
    parser.add_argument("--resources", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--classic", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    start = perf_counter()
    graph = classic() if args.classic else synth(args.principals, args.resources, args.seed)
    generated = perf_counter()
    validate(graph)
    validated = perf_counter()
    result = Analysis(graph).run(recommendations=False, path_limit=10)
    analyzed = perf_counter()
    payload = canonical(result)
    serialized = perf_counter()
    if args.classic:
        expected = {"credential-finance": 1240, "credential-cicd": 9600, "credential-legacy": 31200, "credential-copilot": 14400}
        for item in result["credentials"]:
            if item["absolute_reach"] != expected[item["credential_id"]]: raise AssertionError("Classic expected cardinality mismatch")
    else:
        for item in result["credentials"]:
            index = int(item["principal_id"].rsplit("-", 1)[1])
            if index >= 80 and item["absolute_reach"] != (2 if index % 3 == 0 else 1):
                raise AssertionError("Sparse-tail closed-form mismatch")
    report = {"workload": "classic-cardinality" if args.classic else "feature-complete-synthetic", "principals": 4 if args.classic else args.principals, "resources": 16000 if args.classic else args.resources,
              "seed": args.seed, "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]), "universe_size": result["universe_size"],
              "generation_seconds": generated-start, "schema_validation_seconds": validated-generated, "analysis_seconds": analyzed-validated, "serialization_seconds": serialized-analyzed,
              "total_wall_seconds": serialized-start, "serialized_bytes": len(payload), "recommendation_search": "excluded; no optimum claimed", "path_limit": 10,
              "verification": "four hand-declared classic cardinalities" if args.classic else "hand conformance suite plus closed-form sparse tail for all principals numbered >=80; spotlight topology covered by small oracle fixtures",
              "environment": {"python": platform.python_version(), "os": platform.platform(), "processor": platform.processor(), "logical_cpus": os.cpu_count()},
              "credential_radii": [{key:item[key] for key in ("credential_id","absolute_reach","canonical_radius","sensitivity_weighted_radius","action_weighted_radius")} for item in result["credentials"]] if args.classic else [],
              "max_radius": result["statistics"]["canonical_radius"]["max"], "p95": result["statistics"]["canonical_radius"]["p95"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.classic:
        (args.out.parent / "classic-result-unsigned.json").write_bytes(payload + b"\n")
        (ROOT / "tests" / "fixtures" / "classic-worked-example.json").write_bytes(canonical(graph) + b"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
