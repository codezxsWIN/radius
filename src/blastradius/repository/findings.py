"""End-to-end repository attack-path findings and remediation simulation."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from ..engine import Engine
from ..model import canonical, validate
from .acquisition import acquire_repository
from .evidence import collect_repository_evidence
from .graph import build_repository_graph


PROFILE = "repository-attack-path-v0.1"
NO_PROOF = "No complete path was proven within the supported repository profile; this is not evidence that the repository or deployed environment is safe."


def _finding_id(snapshot_hash, credential_id, resource_id):
    return "finding-" + sha256(canonical([snapshot_hash, credential_id, resource_id])).hexdigest()[:24]


def _finish(result):
    result["analysis_hash"] = sha256(canonical(result)).hexdigest()
    return result


def analyze_repository(root: Path, repository_slug: str) -> dict:
    """Acquire, extract, map and analyze the bounded repository profile."""
    source = Path(root)
    manifest = acquire_repository(source)
    evidence = collect_repository_evidence(source, manifest, repository_slug)
    graph, evidence_index = build_repository_graph(evidence)
    result = {
        "profile": PROFILE,
        "repository": {
            "slug": repository_slug,
            "snapshot_hash": manifest["snapshot_hash"],
            "evidence_hash": evidence["evidence_hash"],
        },
        "summary": {"finding_count": 0, "declared_reachable_secrets": 0},
        "findings": [],
        "diagnostics": deepcopy(evidence["diagnostics"]),
        "coverage": deepcopy(evidence["coverage"]),
        "conclusion": NO_PROOF,
    }
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
            changed["edges"] = [edge for edge in changed["edges"] if edge["id"] not in path_ids or edge["kind"] != "can_assume"]
            validate(changed)
            changed_reach = Engine(changed).reach(credential_id)
            after_reach = len(changed_reach.pairs)
            workflow_fact = evidence_index[workflow["provenance"]["evidence_ref"]]
            findings.append({
                "id": _finding_id(manifest["snapshot_hash"], credential_id, resource_id),
                "title": "GitHub Actions workflow can reach a declared production secret",
                "priority": "high",
                "confidence": "declared-configuration",
                "start_condition": f"The workflow {workflow_fact.get('name', workflow['name'])} job {request.get('job_id', 'unknown')} is assumed compromised; repository analysis does not prove a compromise occurred.",
                "impact": {
                    "action": grant["provider_action"],
                    "resource_arn": grant["resource_arn"],
                },
                "path": path,
                "remediation": {
                    "type": "restrict-github-oidc-trust",
                    "applied": False,
                    "description": "Restrict or remove the declared GitHub OIDC trust that connects this workflow to the AWS role.",
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
