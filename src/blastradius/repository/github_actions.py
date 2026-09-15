"""Bounded GitHub Actions evidence extraction."""

from hashlib import sha256
import re

from ..model import canonical
from .yaml_nodes import location, mapping, scalar, scalar_list, sequence


ROLE_ARN = re.compile(r"^arn:aws:iam::[0-9]{12}:role/[A-Za-z0-9+=,.@_/-]+$")
GLOB_CHARACTERS = frozenset("*?[]!")


def _identifier(kind, *parts):
    digest = sha256(canonical([kind, *parts])).hexdigest()[:20]
    return f"{kind}-{digest}"


def _diagnostic(code, message, path, node, severity="warning"):
    return {"code": code, "severity": severity, "message": message, "location": location(path, node)}


def _permissions(node):
    values = mapping(node)
    if values is None:
        return None
    return {name: scalar(value) for name, value in values.items()}


def _push_branches(on_node):
    if scalar(on_node) == "push":
        return [], True
    events = scalar_list(on_node)
    if events is not None:
        return ([], True) if "push" in events else ([], False)
    event_map = mapping(on_node)
    if event_map is None or "push" not in event_map:
        return [], False
    push = mapping(event_map["push"])
    if push is None:
        return [], True
    branches = scalar_list(push.get("branches")) if "branches" in push else []
    if branches is None:
        return [], True
    exact = [branch for branch in branches if branch and not any(character in branch for character in GLOB_CHARACTERS) and "${{" not in branch]
    return sorted(set(exact)), True


def extract_github_actions(path, root):
    diagnostics = []
    root_map = mapping(root)
    if root_map is None:
        return [], [], [_diagnostic("UNSUPPORTED_WORKFLOW_ROOT", "Workflow root must be a mapping.", path, root)]
    workflow_name = scalar(root_map.get("name")) if "name" in root_map else None
    workflow_id = _identifier("workflow", path)
    branches, has_push = _push_branches(root_map.get("on")) if "on" in root_map else ([], False)
    workflow = {
        "id": workflow_id,
        "name": workflow_name.strip() if workflow_name and workflow_name.strip() else path,
        "path": path,
        "triggers": [{"event": "push", "branches": branches}] if has_push else [],
        "confidence": "repository-verified",
        "location": location(path, root),
    }
    top_permissions = _permissions(root_map.get("permissions")) if "permissions" in root_map else {}
    jobs = mapping(root_map.get("jobs")) if "jobs" in root_map else None
    if jobs is None:
        if "jobs" in root_map:
            diagnostics.append(_diagnostic("UNSUPPORTED_JOBS", "Workflow jobs must be a mapping.", path, root_map["jobs"]))
        return [workflow], [], diagnostics

    requests = []
    for job_id, job_node in sorted(jobs.items()):
        job = mapping(job_node)
        if job is None:
            diagnostics.append(_diagnostic("UNSUPPORTED_JOB", "Workflow job must be a mapping.", path, job_node))
            continue
        if "uses" in job:
            diagnostics.append(_diagnostic("REUSABLE_WORKFLOW_UNSUPPORTED", "Reusable workflow jobs are outside this evidence profile.", path, job["uses"]))
            continue
        effective_permissions = top_permissions
        if "permissions" in job:
            effective_permissions = _permissions(job["permissions"])
            if effective_permissions is None:
                diagnostics.append(_diagnostic("DYNAMIC_PERMISSIONS", "Job permissions are not a supported literal mapping.", path, job["permissions"]))
                continue
        token_allowed = effective_permissions is not None and (effective_permissions.get("id-token") or "").lower() == "write"
        if "environment" in job and scalar(job["environment"]) is None:
            diagnostics.append(_diagnostic("UNSUPPORTED_ENVIRONMENT", "Object or dynamic workflow environments are outside this profile.", path, job["environment"]))
        steps = sequence(job.get("steps")) if "steps" in job else None
        if steps is None:
            continue
        for index, step_node in enumerate(steps):
            step = mapping(step_node)
            if step is None:
                continue
            action = scalar(step.get("uses")) if "uses" in step else None
            if not action or "@" not in action or action.split("@", 1)[0].lower() != "aws-actions/configure-aws-credentials":
                continue
            parameters = mapping(step.get("with")) if "with" in step else None
            role_node = parameters.get("role-to-assume") if parameters else None
            role_arn = scalar(role_node) if role_node is not None else None
            if role_node is None or not role_arn:
                diagnostics.append(_diagnostic("ROLE_ARN_MISSING", "AWS credential configuration has no literal role-to-assume.", path, step_node))
                continue
            if "${{" in role_arn or not ROLE_ARN.fullmatch(role_arn):
                diagnostics.append(_diagnostic("DYNAMIC_ROLE_ARN", "AWS role-to-assume is dynamic or outside the supported literal ARN profile.", path, role_node))
                if not token_allowed:
                    diagnostics.append(_diagnostic("OIDC_PERMISSION_MISSING", "The job does not grant id-token write permission.", path, step_node))
                continue
            if not token_allowed:
                diagnostics.append(_diagnostic("OIDC_PERMISSION_MISSING", "The job does not grant id-token write permission.", path, step_node))
                continue
            audience_node = parameters.get("audience") if parameters else None
            audience = scalar(audience_node) if audience_node is not None else "sts.amazonaws.com"
            if not audience or "${{" in audience:
                diagnostics.append(_diagnostic("DYNAMIC_OIDC_AUDIENCE", "OIDC audience is dynamic and cannot be matched safely.", path, audience_node or step_node))
                continue
            requests.append({
                "id": _identifier("oidc-request", path, job_id, index, role_arn),
                "workflow_id": workflow_id,
                "job_id": job_id,
                "role_arn": role_arn,
                "audience": audience,
                "branches": branches,
                "action_reference": action,
                "confidence": "repository-verified",
                "matching_role_ids": [],
                "matching_trust_ids": [],
                "trust_match": "unresolved",
                "location": location(path, role_node),
            })
    return [workflow], requests, diagnostics
