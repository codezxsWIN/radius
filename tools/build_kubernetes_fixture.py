"""Materialize the reviewed synthetic Kubernetes adapter fixture and outputs."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blastradius.conformance import PROFILE, REQUIRED_MODELS, reference_response
from blastradius.connectors.kubernetes_rbac import ingest
from blastradius.model import canonical


def main():
    folder = ROOT / "connectors/kubernetes_rbac/fixtures"
    graph = ingest(folder / "basic.json")
    outcomes = {model: reference_response({"contract_version": PROFILE, "input": graph, "parameters": {"constraint_model": model, "step_bound": 0, "threshold": "1/4"}}) for model in REQUIRED_MODELS}
    for response in outcomes.values():
        assert response["status"] == "ok"
        assert sorted(record["absolute_reach"] for record in response["credentials"]) == [3, 4]
        assert all(record["universe_size"] == 6 and record["step_bounded_radius"] == "1/2" for record in response["credentials"])
    (folder / "normalized.json").write_bytes(canonical(graph) + b"\n")
    (folder / "expected.json").write_bytes(canonical(outcomes) + b"\n")
    print(canonical({"models": len(outcomes), "universe_size": 6, "absolute_reach": [3, 4], "zero_step_absolute_reach": [3, 3], "synthetic": True}).decode())


if __name__ == "__main__":
    main()
