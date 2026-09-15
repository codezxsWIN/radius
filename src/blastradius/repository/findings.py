"""End-to-end repository attack-path findings and remediation simulation."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from ..engine import Engine
from ..model import canonical, validate
from .acquisition import acquire_repository
from .evidence import collect_repository_evidence, summarize_evidence_gaps
from .graph import build_repository_graph
from .scenarios import repository_controls


PROFILE = "repository-attack-path-v0.1"
NO_PROOF = "No complete path was proven within the supported repository profile; this is not evidence that the repository or deployed environment is safe."


def _finding_id(snapshot_hash, credential_id, resource_id):
    return "finding-" + sha256(canonical([snapshot_hash, credential_id, resource_id])).hexdigest()[:24]


def _finish(result):
    result["analysis_hash"] = sha256(canonical(result)).hexdigest()
    return result


def analyze_repository(root: Path, repository_slug: str, *, review_context=None) -> dict:
    """Acquire, extract, map and analyze the bounded repository profile."""
    source = Path(root)
    manifest = acquire_repository(source)
    evidence = collect_repository_evidence(source, manifest, repository_slug)
    graph, evidence_index = build_repository_graph(evidence)
    if review_context is not None:
        review_context.clear()
        review_context.update({"graph": deepcopy(graph), "evidence_index": deepcopy(evidence_index)})
    result = {
        "profile": PROFILE,
        "repository": {
            "slug": repository_slug,
            "snapshot_hash": manifest["snapshot_hash"],
            "evidence_hash": evidence["evidence_hash"],
        },
        "summary": {"finding_count": 0, "declared_reachable_secrets": 0},
        "findings": [],
        "controls": repository_controls(graph, evidence_index),
        "source_files": deepcopy(evidence["source_files"]),
        "skipped_inputs": deepcopy(manifest["skipped"]),
        "identity_requests": deepcopy(evidence["facts"]["workflow_identities"]),
        "identity_summary": deepcopy(evidence["identity_summary"]),
        "evidence_gaps": summarize_evidence_gaps(evidence),
        "diagnostics": deepcopy(evidence["diagnostics"]),
        "coverage": deepcopy(evidence["coverage"]),
        "conclusion": NO_PROOF,
    }
    result["coverage"].update({
        "inventory_files": manifest["summary"]["file_count"],
        "out_of_profile_files": manifest["summary"]["file_count"] - evidence["coverage"]["selected_files"],
        "skipped_entries": manifest["summary"]["skipped_count"],
    })
    if graph is None:
        return _finish(result)

    engine = Engine(graph)
    nodes = engine.nodes
    findings = []
    reachable_resources = set()
    for credential_id, credential in sorted(nodes.items()):
        if credential.get("kind") != "credential":
            continue
        reach = engine.reach(credential_id)
        for resource_id, action in sorted(reach.pairs):
            if action != "read_secret":
                continue
            reachable_resources.add(resource_id)
            _, _, path_ids = reach.paths[(resource_id, action)]
            path = []
            for edge_id in path_ids:
                edge = engine.edges[edge_id]
                reference = edge["provenance"]["evidence_ref"]
                path.append({
                    "kind": edge["kind"],
                    "source": {"id": edge["source"], "name": nodes[edge["source"]]["name"]},
                    "target": {"id": edge["target"], "name": nodes[edge["target"]]["name"]},
                    "evidence": deepcopy(evidence_index[reference]),
                })

            request = evidence_index[credential["provenance"]["evidence_ref"]]
            workflow = nodes[credential["principal_id"]]
            grant_edge = engine.edges[path_ids[-1]]
            grant = evidence_index[grant_edge["provenance"]["evidence_ref"]]
            before_reach = len(reach.pairs)
            changed = deepcopy(graph)
            removed_trusts = {evidence_index[engine.edges[edge_id]["provenance"]["evidence_ref"]]["trust_id"] for edge_id in path_ids if engine.edges[edge_id]["kind"] == "can_assume"}
            changed["edges"] = [edge for edge in changed["edges"] if edge["kind"] != "can_assume" or evidence_index[edge["provenance"]["evidence_ref"]]["trust_id"] not in removed_trusts]
            validate(changed)
            changed_reach = Engine(changed).reach(credential_id)
            after_reach = len(changed_reach.pairs)
            workflow_fact = evidence_index[workflow["provenance"]["evidence_ref"]]
            correlation = next(step["evidence"] for step in path if step["kind"] == "can_assume")
            trust = evidence_index[correlation["trust_id"]]
            matched_request = evidence_index[correlation["request_id"]]
            findings.append({
                "id": _finding_id(manifest["snapshot_hash"], credential_id, resource_id),
                "title": "GitHub Actions job can reach a declared secret",
                "priority": "high",
                "confidence": "declared-configuration",
                "start_condition": f"The workflow {workflow_fact.get('name', workflow['name'])} job {request.get('job_id', 'unknown')} is assumed compromised; repository analysis does not prove a compromise occurred.",
                "impact": {
                    "action": grant["provider_action"],
                    "resource_arn": grant["resource_arn"],
                },
                "path": path,
                "authorization": {
                    "workflow": {
                        "name": workflow_fact.get("name", workflow["name"]),
                        "job_id": matched_request["job_id"],
                        "base_job_id": matched_request.get("base_job_id", matched_request["job_id"]),
                        "matrix": deepcopy(matched_request.get("matrix", {})),
                        "branches": deepcopy(matched_request["branches"]),
                        "role_arn": matched_request["role_arn"],
                        "audience": matched_request["audience"],
                        "action_reference": matched_request["action_reference"],
                        "location": deepcopy(matched_request["location"]),
                    },
                    "trust": deepcopy(trust),
                    "permission": deepcopy(grant),
                },
                "remediation": {
                    "type": "restrict-github-oidc-trust",
                    "control_id": trust["id"],
                    "applied": False,
                    "description": "Remove the selected declared GitHub OIDC trust statement from the model. All modeled uses of that statement are removed; other trust statements remain.",
                    "before_absolute_reach": before_reach,
                    "after_absolute_reach": after_reach,
                    "path_broken": after_reach < before_reach and (resource_id, action) not in changed_reach.pairs,
                },
                "deployed_aws_state": evidence["coverage"]["deployed_aws_state"],
            })

    findings.sort(key=lambda item: item["id"])
    result["findings"] = findings
    result["summary"] = {
        "finding_count": len(findings),
        "declared_reachable_secrets": len(reachable_resources),
    }
    if findings:
        result["conclusion"] = "A complete source-backed path exists in the supported repository declarations; deployed AWS state remains unverified."
    return _finish(result)
