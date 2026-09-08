"""Generate the bounded IAM export fixture and independently checked result."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from test_aws import bundle
from blastradius.connectors.aws_iam import ingest
from blastradius.analysis import Analysis
from blastradius.model import canonical


if __name__ == "__main__":
    folder = ROOT / "connectors" / "aws_iam" / "fixtures" / "basic"
    folder.mkdir(parents=True, exist_ok=True)
    details, metadata = bundle()
    for filename, contents in (("authorization-details.json", details), ("metadata.json", metadata)):
        (folder / filename).write_text(json.dumps(contents, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    graph = ingest(folder)
    (folder / "expected-graph.json").write_bytes(canonical(graph) + b"\n")
    result = Analysis(graph).run(False)
    counts = {item["credential_id"]: item["absolute_reach"] for item in result["credentials"]}
    if counts != {"fictional-aws-user-metadata": 4, "fictional-aws-role-metadata": 2}:
        raise AssertionError("AWS fixture differs from hand-computed expectation")
    print(json.dumps({"aws_fixture_verified": True, "universe": result["universe_size"], "counts": counts}))
