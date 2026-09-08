"""Public exact-rational conformance contract and subprocess runner."""

from fractions import Fraction
from hashlib import sha256
from io import StringIO
import json
import math
from pathlib import Path
import shlex
import subprocess

from .engine import Engine
from .model import GraphError, canonical, graph_hash, number, read_json, validate

PROFILE = "1.0-draft"
REQUIRED_MODELS = ("default", "strict", "session-theft-aware")


def exact_statistics(values, threshold):
    values = sorted(values)
    count = len(values)
    if not count:
        return {"credential_count": 0, "maximum": None, "p95": None, "gini": None, "share_above_threshold": None}
    total = sum(values)
    gini = sum((2 * rank - count - 1) * value for rank, value in enumerate(values, 1)) / (count * total) if total else Fraction()
    return {"credential_count": count, "maximum": str(values[-1]), "p95": str(values[(95 * count + 99) // 100 - 1]),
            "gini": str(gini), "share_above_threshold": str(Fraction(sum(value > threshold for value in values), count))}


def summarize_pairs(graph, pairs_by_credential, bounded_by_credential, parameters):
    resources = {node["id"]: node for node in graph["nodes"] if node["kind"] == "resource"}
    universe = {(identifier, action) for identifier, node in resources.items() for action in node["actions"]}
    sensitivity = {identifier: number(node["sensitivity"]) for identifier, node in resources.items()}
    sensitivity_total = sum(sensitivity[identifier] for identifier, action in universe)
    action_total = sum(graph["action_weights"][action] for identifier, action in universe)
    credentials = []
    for identifier, pairs in sorted(pairs_by_credential.items()):
        credentials.append({"credential_id": identifier, "absolute_reach": len(pairs), "universe_size": len(universe),
                            "canonical_radius": str(Fraction(len(pairs), len(universe))),
                            "sensitivity_weighted_radius": str(sum(sensitivity[resource] for resource, action in pairs) / sensitivity_total) if sensitivity_total else None,
                            "action_weighted_radius": str(Fraction(sum(graph["action_weights"][action] for resource, action in pairs), action_total)),
                            "step_bounded_radius": str(Fraction(len(bounded_by_credential[identifier]), len(universe))),
                            "reachable_pairs": [list(pair) for pair in sorted(pairs)],
                            "bounded_pairs": [list(pair) for pair in sorted(bounded_by_credential[identifier])]})
    statistics = {}
    for field in ("canonical_radius", "sensitivity_weighted_radius", "action_weighted_radius", "step_bounded_radius"):
        values = [Fraction(record[field]) for record in credentials if record[field] is not None]
        statistics[field] = exact_statistics(values, Fraction(parameters["threshold"]))
    response = {"contract_version": PROFILE, "status": "ok", "snapshot_hash": graph_hash(graph), "parameters": parameters,
                "credentials": credentials, "statistics": statistics}
    response["manifest_hash"] = sha256(canonical(response)).hexdigest()
    return response


def reference_response(request):
    if not isinstance(request, dict) or request.get("contract_version") != PROFILE:
        return {"contract_version": PROFILE, "status": "error", "error": "UNSUPPORTED_CONTRACT"}
    try:
        graph = validate(request["input"])
        parameters = request["parameters"]
        if set(parameters) != {"constraint_model", "step_bound", "threshold"} or parameters["constraint_model"] not in REQUIRED_MODELS:
            raise GraphError("Unsupported conformance parameters.")
        if type(parameters["step_bound"]) is not int or parameters["step_bound"] < 0 or not isinstance(parameters["threshold"], str) or not 0 <= Fraction(parameters["threshold"]) <= 1:
            raise GraphError("Invalid conformance parameters.")
        engine = Engine(graph, parameters["constraint_model"])
        full, bounded = {}, {}
        for node in graph["nodes"]:
            if node["kind"] == "credential":
                reach = engine.reach(node["id"])
                full[node["id"]] = reach.pairs
                bounded[node["id"]] = {pair for pair, rank in reach.paths.items() if rank[0] <= parameters["step_bound"]}
        response = summarize_pairs(graph, full, bounded, parameters)
        resources = {node["id"]: node for node in graph["nodes"] if node["kind"] == "resource"}
        for record in response["credentials"]:
            reach = engine.reach(record["credential_id"])
            witness = None
            if reach.pairs:
                pair = min(reach.pairs, key=lambda pair: (-number(resources[pair[0]]["sensitivity"]), reach.paths[pair], pair))
                rank = reach.paths[pair]
                witness = {"resource_id": pair[0], "action": pair[1], "escalation_steps": rank[0], "graph_hops": rank[1], "edge_ids": list(rank[2])}
            record["witness"] = witness
        response.pop("manifest_hash")
        response["manifest_hash"] = sha256(canonical(response)).hexdigest()
        return response
    except (GraphError, KeyError, TypeError, ValueError, ZeroDivisionError):
        return {"contract_version": PROFILE, "status": "error", "error": "INVALID_GRAPH_OR_PARAMETERS"}


def run_suite(tool, suite, output, timeout=10):
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise GraphError("Tool timeout must be a finite positive number.")
    suite, output = Path(suite), Path(output)
    manifest = json.loads((suite / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("profile") != PROFILE or manifest.get("required_models") != list(REQUIRED_MODELS) or not manifest.get("fixtures"):
        raise GraphError("Unsupported, incomplete or empty conformance manifest.")
    checked, identifiers, paths = [], set(), set()
    for entry in manifest["fixtures"]:
        location = (suite / entry["file"]).resolve()
        if not location.is_relative_to(suite.resolve()) or location in paths or not entry.get("sha256"):
            raise GraphError("Conformance fixture paths and required hashes must be unique and contained in the suite.")
        fixture_bytes = location.read_bytes()
        if sha256(fixture_bytes).hexdigest() != entry["sha256"]:
            raise GraphError("Conformance fixture integrity does not match its frozen manifest.")
        fixture = json.loads(fixture_bytes)
        if not fixture.get("id") or fixture["id"] in identifiers or set(fixture.get("expected", {})) != set(REQUIRED_MODELS):
            raise GraphError("Fixture identities or required-model expectations are incomplete.")
        identifiers.add(fixture["id"])
        paths.add(location)
        checked.append(fixture)
    command = shlex.split(tool)
    if not command:
        raise GraphError("Conformance needs an explicit tool command.")
    records = []
    for fixture in checked:
        for model in REQUIRED_MODELS:
            request = {"contract_version": PROFILE, "input": fixture["input"], "parameters": {"constraint_model": model, "step_bound": fixture["step_bound"], "threshold": "1/4"}}
            results, failure = [], None
            for repeat in range(2):
                try:
                    process = subprocess.run(command, input=canonical(request) + b"\n", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, shell=False)
                    if process.returncode != 0:
                        failure = "nonzero-exit"
                        break
                    if len(process.stdout) > 4 * 1024 * 1024:
                        failure = "output-limit"
                        break
                    results.append(process.stdout)
                except subprocess.TimeoutExpired:
                    failure = "timeout"
                    break
                except OSError:
                    failure = "command-unavailable"
                    break
            if failure is None:
                try:
                    observed = read_json(StringIO(results[0].decode("utf-8")))
                    if observed != fixture["expected"][model]: failure = "semantic-mismatch"
                    elif results[0] != results[1]: failure = "nondeterministic-bytes"
                except (ValueError, UnicodeError, RecursionError):
                    failure = "invalid-json"
            records.append({"fixture_id": fixture["id"], "constraint_model": model, "requirements": fixture["requirements"], "passed": failure is None, "failure": failure})
    requirements = {}
    for record in records:
        for requirement in record["requirements"]:
            requirements.setdefault(requirement, []).append(record["passed"])
    report = {"conformance_profile": PROFILE, "suite_hash": sha256(canonical(manifest)).hexdigest(), "fixture_count": len(manifest["fixtures"]),
              "case_count": len(records), "passed": sum(item["passed"] for item in records), "failed": sum(not item["passed"] for item in records),
              "tool_command": command, "determinism_repetitions": 2, "requirements": {key: "pass" if all(values) else "fail" for key, values in sorted(requirements.items())},
              "manual_requirements": ["BR-R31 claim disclosure", "BR-R32 change governance"], "cases": records,
              "claim_limit": "Passing this finite core suite is not certification, platform-normalizer validation or proof of completeness."}
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_bytes(canonical(report) + b"\n")
    lines = ["# Blast Radius Conformance Report", "", f"Profile: {PROFILE}. Fixtures: {report['fixture_count']}. Cases passed: {report['passed']}/{report['case_count']}. Failed: {report['failed']}.", "", f"Suite SHA-256: `{report['suite_hash']}`", "", "| Fixture | Model | Result | Failure |", "| --- | --- | --- | --- |"]
    lines.extend(f"| {item['fixture_id']} | {item['constraint_model']} | {'PASS' if item['passed'] else 'FAIL'} | {item['failure'] or ''} |" for item in records)
    lines.extend(["", "## Requirement Results", "", *[f"- {key}: {value}" for key, value in report["requirements"].items()], "", "Claim disclosure and change-governance requirements need manual review; this is a public self-test, not a paid certificate.", ""])
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return report
