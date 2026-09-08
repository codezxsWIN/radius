import json
from pathlib import Path

from blastradius.analysis import Analysis
from blastradius.cli import main
from blastradius.connectors.entra_azure import ingest
from blastradius.model import canonical

ROOT = Path(__file__).resolve().parents[1]


def test_saved_synthetic_exports_ingest_and_have_expected_radii(tmp_path):
    for name, expected in (("basic", [1, 1]), ("rich", [0, 2, 3])):
        folder = ROOT / "connectors" / "entra_azure" / "fixtures" / name
        graph = ingest(folder)
        assert sorted(item["absolute_reach"] for item in Analysis(graph).run(False)["credentials"]) == expected
        assert canonical(graph) + b"\n" == (folder / "expected-graph.json").read_bytes()
        output = tmp_path / (name + ".json")
        assert main(["collect-entra-azure", "--exports", str(folder), "--out", str(output)]) == 0
        assert output.read_bytes() == canonical(graph) + b"\n"


def test_declarative_manifest_is_read_only_and_marks_gaps():
    manifest = json.loads((ROOT / "connectors" / "entra_azure" / "manifest.json").read_text())
    assert manifest["http_methods"] == ["GET"]
    assert manifest["live_execution_in_this_session"] is False
    assert len(manifest["collections"]) == 15
    assert all(item["reference"].startswith("https://learn.microsoft.com/") for item in manifest["collections"])
    assert any("unverified" in item["verification"] for item in manifest["collections"])
