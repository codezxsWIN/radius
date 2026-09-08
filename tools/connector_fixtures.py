"""Materialize realistic JSON export envelopes with deterministic fictional UUIDs."""

import json
from pathlib import Path
import sys
from uuid import uuid5, NAMESPACE_URL

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from test_connector import exports, rich_exports
from blastradius.connectors.entra_azure import ingest
from blastradius.analysis import Analysis
from blastradius.model import canonical


def transform(value, names):
    if isinstance(value, str):
        if value == "fictional-region": return "eastus"
        for original, replacement in sorted(names.items(), key=lambda item: -len(item[0])):
            value = value.replace(original, replacement)
        return value
    if isinstance(value, dict): return {transform(key, names): transform(child, names) for key, child in value.items()}
    if isinstance(value, list): return [transform(child, names) for child in value]
    return value


def write_bundle(name, bundle):
    identities = {item["id"] for collection in ("users", "groups", "servicePrincipals", "appRoleAssignments", "directoryRoleAssignments", "directoryRoleDefinitions", "roleEligibilityScheduleInstances", "oauth2PermissionGrants", "conditionalAccessPolicies") for item in bundle[collection]}
    identities |= {role["id"] for item in bundle["servicePrincipals"] for role in item.get("appRoles", [])}
    identities |= {"fictional-role", "fictional-assignment", "fictional-schedule"}
    replacements = {identifier: str(uuid5(NAMESPACE_URL, "urn:fictional-blastradius:" + identifier)) for identifier in identities}
    bundle = transform(bundle, replacements)
    folder = ROOT / "connectors" / "entra_azure" / "fixtures" / name
    folder.mkdir(parents=True, exist_ok=True)
    for collection, content in bundle.items():
        wrapped = content if collection in {"metadata", "groupMembers"} else {"value": content}
        (folder / f"{collection}.json").write_text(json.dumps(wrapped, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    graph = ingest(folder)
    (folder / "expected-graph.json").write_bytes(canonical(graph) + b"\n")
    result = Analysis(graph).run(False)
    print(json.dumps({"fixture": name, "universe": result["universe_size"], "credentials": [{key:record[key] for key in ("credential_id","absolute_reach","canonical_radius")} for record in result["credentials"]]}))


if __name__ == "__main__":
    write_bundle("basic", exports())
    write_bundle("rich", rich_exports())
