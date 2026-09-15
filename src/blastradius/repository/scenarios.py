"""Deterministic repository-wide trust-removal comparisons, without source edits."""

from copy import deepcopy
from hashlib import sha256

from ..engine import Engine
from ..model import GraphError, canonical, validate


def repository_controls(graph, evidence_index):
    if graph is None:
        return []
    nodes = {node["id"]: node for node in graph["nodes"]}
    controls = {}
    for edge in graph["edges"]:
        if edge["kind"] != "can_assume":
            continue
        correlation = evidence_index[edge["provenance"]["evidence_ref"]]
        trust = evidence_index[correlation["trust_id"]]
        role = evidence_index[trust["role_id"]]
        if trust["id"] not in controls:
            controls[trust["id"]] = {
                "id": trust["id"], "kind": "remove-github-oidc-trust", "role_name": role["role_name"],
                "location": deepcopy(trust["location"]), "subjects": deepcopy(trust["subjects"]),
                "audience": deepcopy(trust["audience"]), "operator": trust["operator"], "jobs": [],
            }
        job = {"id": edge["source"], "name": nodes[edge["source"]]["name"]}
        if job not in controls[trust["id"]]["jobs"]:
            controls[trust["id"]]["jobs"].append(job)
    for control in controls.values():
        control["jobs"].sort(key=lambda job: job["id"])
    return sorted(controls.values(), key=lambda control: (control["role_name"], control["location"]["path"], control["location"]["start_line"], control["id"]))


def simulate_repository_review(result, context, selected_controls):
    """Recompute all finding reach on the retained graph, not the displayed witnesses."""
    if (not isinstance(selected_controls, list) or len(selected_controls) > 128
            or any(not isinstance(control, str) for control in selected_controls)
            or len(set(selected_controls)) != len(selected_controls)):
        raise GraphError("Select at most 128 distinct known trust controls.")
    controls = {control["id"]: control for control in result.get("controls", [])}
    selected = set(selected_controls)
    if selected - controls.keys():
        raise GraphError("A selected trust control does not belong to this analysis.")
    graph = context.get("graph")
    states, jobs = [], {}
    before_resources, after_resources = set(), set()
    if graph is not None:
        evidence_index = context["evidence_index"]
        changed = deepcopy(graph)
        changed["edges"] = [edge for edge in changed["edges"] if edge["kind"] != "can_assume" or evidence_index[edge["provenance"]["evidence_ref"]]["trust_id"] not in selected]
        validate(changed)
        before_engine, after_engine = Engine(graph), Engine(changed)
        before_reach, after_reach = {}, {}
        for credential in (node for node in graph["nodes"] if node["kind"] == "credential"):
            identifier, job_id = credential["id"], credential["principal_id"]
            before_reach[identifier] = before_engine.reach(identifier)
            after_reach[identifier] = after_engine.reach(identifier)
            job = jobs.setdefault(job_id, {"id": job_id, "name": before_engine.nodes[job_id]["name"], "before": set(), "after": set()})
            job["before"].update(before_reach[identifier].pairs)
            job["after"].update(after_reach[identifier].pairs)
        for finding in result["findings"]:
            credential_id = finding["path"][0]["source"]["id"]
            resource_id = finding["path"][-1]["target"]["id"]
            pair = (resource_id, "read_secret")
            reach = after_reach[credential_id]
            reachable = pair in reach.pairs
            remaining_controls = []
            if reachable:
                after_resources.add(resource_id)
                for edge_id in reach.paths[pair][2]:
                    edge = after_engine.edges[edge_id]
                    if edge["kind"] == "can_assume":
                        remaining_controls.append(evidence_index[edge["provenance"]["evidence_ref"]]["trust_id"])
            before_resources.add(resource_id)
            states.append({"finding_id": finding["id"], "reachable": reachable, "remaining_controls": remaining_controls})
    elif result["findings"]:
        raise GraphError("The retained model for this analysis is unavailable.")
    job_rows = [{"id": job["id"], "name": job["name"], "before_reachable_secrets": len(job["before"]), "after_reachable_secrets": len(job["after"])} for job in sorted(jobs.values(), key=lambda job: job["id"])]
    after_count = sum(state["reachable"] for state in states)
    comparison = {
        "profile": "repository-review-change-set-v0.1", "base_analysis_hash": result["analysis_hash"],
        "repository_slug": result["repository"]["slug"], "simulation_only": True, "applied": False,
        "selected_controls": [deepcopy(controls[identifier]) for identifier in sorted(selected)],
        "before": {"reachable_findings": len(result["findings"]), "reachable_secrets": len(before_resources), "reachable_jobs": sum(bool(job["before"]) for job in jobs.values())},
        "after": {"reachable_findings": after_count, "reachable_secrets": len(after_resources), "reachable_jobs": sum(bool(job["after"]) for job in jobs.values())},
        "blocked_findings": len(result["findings"]) - after_count,
        "finding_states": states, "jobs": job_rows,
        "scope": "All modeled uses of the selected trust statements are removed together. Alternate trust statements remain. Repository and deployed AWS configuration are unchanged.",
    }
    comparison["comparison_hash"] = sha256(canonical(comparison)).hexdigest()
    return comparison


def render_change_request(comparison):
    from .report import _safe
    lines = ["# Blast Radius Change Request", "", f"Repository: {_safe(comparison['repository_slug'])}", "", "Status: proposed, simulation only. No source or AWS change was applied.", "", "## Proposed Trust Removals", ""]
    if not comparison["selected_controls"]:
        lines.append("No trust removal selected.")
    for control in comparison["selected_controls"]:
        source = control["location"]
        lines.extend([f"- {_safe(control['role_name'])}: {_safe(source['path'])}:{source['start_line']}:{source['start_column']}", f"  Subjects: {_safe(', '.join(control['subjects']))}", f"  Declared jobs using this statement: {len(control['jobs'])}"])
    lines.extend(["", "## Recomputed Impact", "", f"Reachable findings: {comparison['before']['reachable_findings']} -> {comparison['after']['reachable_findings']}", f"Distinct reachable secrets: {comparison['before']['reachable_secrets']} -> {comparison['after']['reachable_secrets']}", f"Jobs with declared secret access: {comparison['before']['reachable_jobs']} -> {comparison['after']['reachable_jobs']}", "", "## Job Breakdown", ""])
    for job in comparison["jobs"]:
        lines.append(f"- {_safe(job['name'])}: {job['before_reachable_secrets']} -> {job['after_reachable_secrets']} declared reachable secrets")
    lines.extend(["", comparison["scope"], "", "Validate deployment and legitimate workload impact independently before changing a policy. This is not an executable patch or deployed-access verification.", "", f"Baseline analysis hash: {comparison['base_analysis_hash']}", f"Comparison hash: {comparison['comparison_hash']}", ""])
    return "\n".join(lines)