import json
from pathlib import Path

from blastradius.conformance import reference_response, PROFILE, REQUIRED_MODELS
from blastradius.model import validate

ROOT=Path(__file__).resolve().parents[1]


def test_saved_reconstructions_are_valid_and_reproducible():
    cases=json.loads((ROOT/"reconstructions/results.json").read_text())["cases"]
    assert len(cases)==5
    for case in cases:
        folder=ROOT/"reconstructions"/case["id"]
        for input_name,output_name in (("input.json","engine-output.json"),("control-input.json","control-output.json")):
            graph=validate(json.loads((folder/input_name).read_text()))
            expected=json.loads((folder/output_name).read_text())
            for model in REQUIRED_MODELS:
                assert reference_response({"contract_version":PROFILE,"input":graph,"parameters":{"constraint_model":model,"step_bound":1,"threshold":"1/4"}})==expected[model]
        assert case["top_decile"]=="not_identifiable"


def test_session_theft_case_and_vulnerability_scope_are_explicit():
    records={case["id"]:case for case in json.loads((ROOT/"reconstructions/results.json").read_text())["cases"]}
    circle=records["circleci-2023"]
    assert circle["model_reach"]["default"]==0
    assert circle["model_reach"]["session-theft-aware"]==1
    assert circle["control_reach"]["session-theft-aware"]==0
    assert records["mlflow-cve-2026-64849"]["evidence_grade"].startswith("B:")
