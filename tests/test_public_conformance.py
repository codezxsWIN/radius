import json
from hashlib import sha256
from pathlib import Path
import sys

import pytest

from blastradius.conformance import PROFILE, REQUIRED_MODELS, reference_response, run_suite
from blastradius.model import GraphError, canonical

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_core_expectations_match_reference():
    manifest=json.loads((ROOT/"conformance/manifest.json").read_text())
    assert len(manifest["fixtures"]) >= 25
    for entry in manifest["fixtures"]:
        case=json.loads((ROOT/"conformance"/entry["file"]).read_text())
        for model in REQUIRED_MODELS:
            request={"contract_version":PROFILE,"input":case["input"],"parameters":{"constraint_model":model,"step_bound":case["step_bound"],"threshold":"1/4"}}
            assert reference_response(request)==case["expected"][model], (case["id"],model)


def test_unknown_contract_is_rejected():
    assert reference_response({"contract_version":"future"})["error"]=="UNSUPPORTED_CONTRACT"


def test_runner_reports_bad_tool_instead_of_passing(tmp_path):
    fixture={"id":"BR-X","requirements":["BR-R20"],"input":{},"step_bound":1,"expected":{model:{} for model in REQUIRED_MODELS}}
    (tmp_path/"case.json").write_bytes(canonical(fixture))
    (tmp_path/"manifest.json").write_text(json.dumps({"profile":PROFILE,"required_models":list(REQUIRED_MODELS),"fixtures":[{"file":"case.json","sha256":sha256(canonical(fixture)).hexdigest()}]}))
    report=run_suite('"'+sys.executable+'" -c "print(123)"',tmp_path,tmp_path/"report")
    assert report["failed"]==3
    assert report["requirements"]["BR-R20"]=="fail"


@pytest.mark.parametrize("failure", ["empty", "hash", "path", "duplicate", "profile"])
def test_invalid_suite_cannot_claim_a_pass(tmp_path, monkeypatch, failure):
    manifest=json.loads((ROOT/"conformance/manifest.json").read_text())
    entry=dict(manifest["fixtures"][0]);entry["file"]="case.json"
    (tmp_path/"case.json").write_bytes((ROOT/"conformance"/manifest["fixtures"][0]["file"]).read_bytes())
    manifest["fixtures"]=[entry]
    if failure=="empty":manifest["fixtures"]=[]
    if failure=="hash":entry["sha256"]="0"*64
    if failure=="path":entry["file"]="../outside.json"
    if failure=="duplicate":manifest["fixtures"].append(dict(entry))
    if failure=="profile":manifest["profile"]="future"
    (tmp_path/"manifest.json").write_bytes(canonical(manifest))
    def forbidden(*args, **kwargs):raise AssertionError("Invalid suites must fail before executing a supplied tool")
    monkeypatch.setattr("subprocess.run",forbidden)
    with pytest.raises(GraphError):run_suite("unused",tmp_path,tmp_path/"out")


def test_public_and_bundled_graph_schemas_match():
    assert json.loads((ROOT/"schema/blastradius-graph-v0.1.schema.json").read_text())==json.loads((ROOT/"src/blastradius/assets/blastradius-graph-v0.1.schema.json").read_text())
