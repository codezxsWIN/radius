"""Freeze protocol hashes, then generate all prespecified synthetic experiments."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blastradius.aggregation import aggregate_synthetic
from blastradius.model import canonical, graph_hash
from blastradius.research import REGIMES, SEED, TENANTS, analyze_tenant, generate_tenant, privacy_experiment, summarize_regime
from blastradius.summary import summary_schema


def main():
    folder = ROOT / "research"
    receipt_path = folder / "reproducibility-receipt.json"
    receipt = {"protocol_sha256": sha256((ROOT / "PREREGISTRATION.md").read_bytes()).hexdigest(),
               "run_plan_sha256": sha256((folder / "RUN_PLAN.md").read_bytes()).hexdigest(),
               "recorded_before_generation_utc": datetime.now(timezone.utc).isoformat(), "seed": SEED, "tenants_per_regime": TENANTS,
               "status": "before-generation", "external_timestamp_attestation": False, "synthetic": True}
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text())
        if any(previous[key] != receipt[key] for key in ("protocol_sha256", "run_plan_sha256", "seed", "tenants_per_regime")):
            raise RuntimeError("Protocol changed after a previous run; an explicit amendment and separate run directory are required.")
        receipt = previous
    else:
        receipt_path.write_bytes(canonical(receipt) + b"\n")
    all_outcomes, summaries, configurations = {}, [], []
    for regime in REGIMES:
        outcomes = []
        for index in range(TENANTS):
            graph, config = generate_tenant(index, regime)
            outcome, summary = analyze_tenant(graph)
            outcomes.append({"tenant_index": index, **outcome})
            configurations.append({**config, "graph_sha256": graph_hash(graph)})
            if regime == "null":
                summaries.append(summary)
                if index == 0:
                    (folder / "example-synthetic-tenant.json").write_bytes(canonical(graph) + b"\n")
        all_outcomes[regime] = {"summary": summarize_regime(outcomes), "tenant_results": outcomes}
        print(json.dumps({"regime": regime, **all_outcomes[regime]["summary"]}), flush=True)
    (folder / "synthetic-summaries.jsonl").write_bytes(b"".join(canonical(summary) + b"\n" for summary in summaries))
    (folder / "tenant-configurations.jsonl").write_bytes(b"".join(canonical(config) + b"\n" for config in configurations))
    (folder / "illustrative-nhi-results.json").write_bytes(canonical({"synthetic": True, "protocol_sha256": receipt["protocol_sha256"], "regimes": all_outcomes}) + b"\n")
    privacy = privacy_experiment(summaries)
    (folder / "privacy-results.json").write_bytes(canonical(privacy) + b"\n")
    (folder / "noisy-aggregate.json").write_bytes(canonical(aggregate_synthetic(summaries, random.Random(SEED))) + b"\n")
    (ROOT / "schema/structural-summary-v1.0-draft.schema.json").write_text(json.dumps(summary_schema(), indent=2) + "\n", encoding="utf-8")
    receipt.update(status="completed", completed_utc=datetime.now(timezone.utc).isoformat(),
                   outputs={name: sha256((folder / name).read_bytes()).hexdigest() for name in ("synthetic-summaries.jsonl", "tenant-configurations.jsonl", "illustrative-nhi-results.json", "privacy-results.json", "noisy-aggregate.json")})
    receipt_path.write_bytes(canonical(receipt) + b"\n")
    print(json.dumps(privacy, indent=2))


if __name__ == "__main__":
    main()
