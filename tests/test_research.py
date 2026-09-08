from hashlib import sha256
import json
from pathlib import Path

import pytest

from blastradius.model import canonical, graph_hash
from blastradius.research import analyze_tenant, generate_tenant, wilson
from blastradius.summary import summary_schema, validate_summary

ROOT = Path(__file__).resolve().parents[1]


def test_prospective_receipt_and_all_output_hashes():
    receipt = json.loads((ROOT / "research/reproducibility-receipt.json").read_text())
    assert receipt["status"] == "completed"
    assert receipt["protocol_sha256"] == sha256((ROOT / "PREREGISTRATION.md").read_bytes()).hexdigest()
    assert receipt["run_plan_sha256"] == sha256((ROOT / "research/RUN_PLAN.md").read_bytes()).hexdigest()
    for name, expected in receipt["outputs"].items():
        assert sha256((ROOT / "research" / name).read_bytes()).hexdigest() == expected


def test_five_hundred_closed_summaries_and_schema():
    summaries = [json.loads(line) for line in (ROOT / "research/synthetic-summaries.jsonl").read_text().splitlines()]
    assert len(summaries) == 500
    for summary in summaries:
        validate_summary(summary)
    assert json.loads((ROOT / "schema/structural-summary-v1.0-draft.schema.json").read_text()) == summary_schema()


def test_paired_generator_reproducibility_and_exact_union():
    configurations = [json.loads(line) for line in (ROOT / "research/tenant-configurations.jsonl").read_text().splitlines()]
    saved = json.loads((ROOT / "research/illustrative-nhi-results.json").read_text())["regimes"]
    for regime in ("null", "nhi-broader", "human-broader"):
        for index in (0, 49, 499):
            graph, config = generate_tenant(index, regime)
            assert graph_hash(graph) == next(record["graph_sha256"] for record in configurations if record["regime"] == regime and record["tenant_index"] == index)
            outcome, summary = analyze_tenant(graph)
            assert {"tenant_index": index, **outcome} == saved[regime]["tenant_results"][index]
            assert outcome["nhi_weighted_union"] <= 1
            assert outcome["weighted_total_union"] == pytest.approx(outcome["nhi_weighted_union"] + outcome["human_weighted_union"] - outcome["weighted_overlap"])


def test_wilson_known_symmetry_and_extremes():
    lower, upper = wilson(50, 100)
    assert lower == pytest.approx(0.4038315303659956)
    assert upper == pytest.approx(1 - lower)
    assert wilson(0, 100)[0] == pytest.approx(0)
    assert wilson(100, 100)[1] == pytest.approx(1)
