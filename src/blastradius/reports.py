"""Deterministic report exports; HTML embeds only verified synthetic result data."""

from fractions import Fraction
from html import escape
import json
from pathlib import Path
import re

from .analysis import distribution
from .model import GraphError


def percent(value):
    return "n/a" if value is None else f"{value * 100:.2f}%"


def markdown(result):
    stats = result["statistics"]["canonical_radius"]
    lines = ["# Blast Radius", "", f"**{result['organization']} | synthetic tenant**", "",
             f"Credentials: {stats['count']}; maximum: {percent(stats['max'])}; p95: {percent(stats['p95'])}; Gini: {stats['gini']}; share above {result['parameters']['threshold']}: {percent(stats['share_above_threshold'])}.", "",
             "| Credential | Principal Type | Absolute Reach | Canonical | Sensitivity | Action | Step-Bounded |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for record in result["credentials"]:
        name = record["name"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {name} | {record['principal_type']} | {record['absolute_reach']} | {percent(record['canonical_radius'])} | {percent(record['sensitivity_weighted_radius'])} | {percent(record['action_weighted_radius'])} | {percent(record['step_bounded_radius'])} |")
    lines.extend(["", "## Top Ten Explanations", ""])
    for record in result["credentials"][:10]:
        lines.append(f"### {record['name']}")
        explanation = record["explanation"]
        if not explanation:
            lines.extend(["", "No reachable witness is present for this credential.", ""])
            continue
        lines.extend(["", f"Most sensitive reachable resource: {explanation['resource_name']} / {explanation['action']}; {explanation['escalation_steps']} escalation steps.", ""])
        for index, step in enumerate(explanation["steps"], 1):
            lines.append(f"{index}. {step['source_name']} -> {step['kind']} -> {step['target_name']}. Evidence: {step['provenance']['evidence_ref']}.")
        lines.append("")
    lines.extend(["## Best Single Modeled Change", "", result["recommendation_status"], ""])
    positive = [change for change in result["recommendations"] if change["delta_p95"] < 0]
    if positive:
        best = positive[0]
        lines.append(f"Remove binding **{best['binding_id']}**: canonical p95 {percent(best['before_p95'])} -> {percent(best['after_p95'])}. {best['evaluated_candidates']} candidates were actually evaluated. No platform change was executed.")
    else:
        lines.append("No evaluated single binding removal reduced p95; no best improvement is invented.")
    lines.extend(["", "## Provenance and Limits", "", f"Snapshot SHA-256: `{result['snapshot_hash']}`", "", f"Engine {result['engine_version']}; schema {result['schema_version']}; model {result['constraint_model']}; snapshot generation time {result['generated_at']}.", "", "Signature verification was performed when this report was exported. HTML and Markdown renderings are not independently signed artifacts; verify the source JSON with the external key.", ""])
    lines.extend(f"- {note}" for note in result["coverage"])
    return "\n".join(lines) + "\n"


def sarif(result):
    findings = []
    threshold = Fraction(result["parameters"]["threshold"])
    for record in result["credentials"]:
        above = Fraction(record["exact"]["canonical"]) > threshold
        findings.append({"ruleId": "BR001", "level": "warning" if above else "note", "kind": "review" if above else "informational",
                         "message": {"text": f"{record['name']}: {record['absolute_reach']} resource-action pairs, canonical radius {percent(record['canonical_radius'])}. Synthetic tenant only."},
                         "locations": [{"logicalLocations": [{"name": record["name"], "fullyQualifiedName": record["credential_id"], "kind": "resource"}]}],
                         "partialFingerprints": {"credential/v1": record["credential_id"]},
                         "properties": {field: record[field] for field in ("canonical_radius", "sensitivity_weighted_radius", "action_weighted_radius", "step_bounded_radius", "absolute_reach", "principal_type")}})
    return {"$schema": "https://www.schemastore.org/sarif-2.1.0.json", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Blast Radius", "version": result["engine_version"], "rules": [{"id": "BR001", "name": "CredentialReach", "shortDescription": {"text": "Synthetic credential reach exceeds a configured threshold"}}]}},
             "results": findings, "properties": {"synthetic": True, "snapshotHash": result["snapshot_hash"], "constraintModel": result["constraint_model"]}}]}


def dashboard(result):
    if result.get("synthetic") is not True:
        raise GraphError("The dashboard accepts synthetic results only.")
    summary = {key: value for key, value in result.items() if key != "snapshot"}
    groups = {
        "Human": {"human_user"}, "Agent": {"ai_agent"},
        "Service / workload": {"service_principal", "managed_identity", "workload_identity"},
    }
    summary["identity_comparison"] = {label: distribution([Fraction(record["exact"]["canonical"]) for record in result["credentials"] if record["principal_type"] in kinds]) for label, kinds in groups.items()}
    rows = []
    for index, record in enumerate(result["credentials"], 1):
        rows.append(f"<tr><td>{index}</td><td>{escape(record['name'])}</td><td>{escape(record['principal_type'])}</td><td>{record['absolute_reach']}</td><td>{percent(record['canonical_radius'])}</td><td>{percent(record['sensitivity_weighted_radius'])}</td><td>{percent(record['action_weighted_radius'])}</td><td>{percent(record['step_bounded_radius'])}</td></tr>")
    template = Path(__file__).with_name("assets").joinpath("dashboard.html").read_text(encoding="utf-8")
    data = json.dumps(summary, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    replacements = {"__DATA__": data, "__ROWS__": "".join(rows), "__ORGANIZATION__": escape(result["organization"]), "__SNAPSHOT_HASH__": escape(result["snapshot_hash"]),
                    "__VERSION__": escape(result["engine_version"]), "__MODEL__": escape(result["constraint_model"]), "__TIME__": escape(result["generated_at"])}
    return re.sub("|".join(map(re.escape, replacements)), lambda match: replacements[match.group()], template)


def render(result, format):
    if format == "json": return json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if format == "md": return markdown(result)
    if format == "sarif": return json.dumps(sarif(result), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if format == "html": return dashboard(result)
    raise GraphError("Unsupported report format.")
