"""Bounded GitHub Actions evidence extraction."""

from hashlib import sha256
from itertools import product
import json
import re

from ..model import GraphError, canonical
from .yaml_nodes import location, mapping, scalar, scalar_list, sequence


ROLE_ARN = re.compile(r"^arn:aws:iam::[0-9]{12}:role/[A-Za-z0-9+=,.@_/-]+$")
GLOB_CHARACTERS = frozenset("*?[]!")
MAX_MATRIX_VARIANTS = 64
MAX_WORKFLOW_VARIANTS = 256
LITERAL_REFERENCE = re.compile(r"\$\{\{\s*(matrix|env)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
CONTEXT_REFERENCE = re.compile(r"\b(secrets|vars|env|matrix|inputs|needs|steps)\.([A-Za-z_][A-Za-z0-9_.-]*)")
SENSITIVE_MATRIX_KEY = re.compile(r"password|secret|token|credential|access.?key|private.?key", re.IGNORECASE)
MAX_IDENTITY_REQUESTS = 512


def _matrix_value(node):
    value = scalar(node)
    if value is None or len(value) > 1024 or "${{" in value or any(ord(character) < 32 for character in value):
        raise ValueError("Matrix values must be bounded literal scalars.")
    if node.style not in {"'", '"'}:
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if re.fullmatch(r"-?(0|[1-9][0-9]*)", value):
            number = int(value)
            if abs(number) > 2 ** 53 - 1:
                raise ValueError("Matrix integer exceeds the exact scalar range.")
            return number
        numeric = re.fullmatch(r"[+-]?(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9_]+)(?:[eE][+-]?[0-9_]+)?", value)
        special_numeric = re.fullmatch(r"[+-]?(?:0[xob][0-9a-f_]+|\.(?:inf|nan))", value, re.IGNORECASE)
        if value.lower() in {"null", "~", ""} or numeric or special_numeric:
            raise ValueError("Ambiguous or noninteger matrix scalars need explicit strings.")
    return value


def _matrix_records(node):
    entries = sequence(node)
    if entries is None or len(entries) > MAX_MATRIX_VARIANTS:
        raise ValueError("Matrix include/exclude must be a bounded list.")
    records = []
    for entry in entries:
        values = mapping(entry)
        if not values or len(values) > 16 or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", key) for key in values):
            raise ValueError("Matrix include/exclude entries must be literal mappings.")
        records.append({key: _matrix_value(value) for key, value in values.items()})
    return records


def _same_scalar(left, right):
    return type(left) is type(right) and left == right


def _matrix_rows(strategy_node):
    strategy = mapping(strategy_node)
    if strategy is None:
        raise ValueError("Strategy must be a literal mapping.")
    if "matrix" not in strategy:
        return [{}]
    matrix = mapping(strategy["matrix"])
    if matrix is None or len(matrix) > 18:
        raise ValueError("Matrix must be a finite literal mapping.")
    axes = []
    combinations = 1
    for key, node in sorted(matrix.items()):
        if key in {"include", "exclude"}:
            continue
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", key):
            raise ValueError("Matrix axis names are outside the bounded key profile.")
        values = sequence(node)
        if values is None or not values:
            raise ValueError("Matrix axes must be nonempty scalar lists.")
        combinations *= len(values)
        if combinations > MAX_MATRIX_VARIANTS:
            raise ValueError("Matrix expansion exceeds 64 variants.")
        axes.append((key, [_matrix_value(value) for value in values]))
    included = _matrix_records(matrix["include"]) if "include" in matrix else []
    excluded = _matrix_records(matrix["exclude"]) if "exclude" in matrix else []
    if not axes and not included:
        raise ValueError("Matrix has no finite variants.")
    originals = [dict(zip([key for key, _ in axes], values)) for values in product(*(values for _, values in axes))] if axes else []
    originals = [row for row in originals if not any(all(key in row and _same_scalar(row[key], value) for key, value in excluded_row.items()) for excluded_row in excluded)]
    expanded = [dict(row) for row in originals]
    additions = []
    for addition in included:
        matches = [index for index, original in enumerate(originals) if all(key not in original or _same_scalar(original[key], value) for key, value in addition.items())]
        if matches:
            for index in matches:
                expanded[index].update(addition)
        else:
            additions.append(dict(addition))
    rows = expanded + additions
    if len(rows) > MAX_MATRIX_VARIANTS:
        raise ValueError("Matrix expansion exceeds 64 variants.")
    return list({canonical(row): row for row in rows}.values())


def _expanded_jobs(jobs, path, diagnostics):
    expanded = []
    for base_job_id, job_node in sorted(jobs.items()):
        job = mapping(job_node)
        try:
            rows = _matrix_rows(job["strategy"]) if job and "strategy" in job else [{}]
        except ValueError as failure:
            diagnostics.append(_diagnostic("MATRIX_WORKFLOW_UNSUPPORTED", str(failure), path, job["strategy"]))
            expanded.append((base_job_id, job_node, base_job_id, {}, False))
            continue
        for row in rows:
            variant = sha256(canonical(row)).hexdigest()[:12]
            job_id = f"{base_job_id}[{variant}]" if row else base_job_id
            expanded.append((job_id, job_node, base_job_id, row, True))
            if len(expanded) > MAX_WORKFLOW_VARIANTS:
                diagnostics.append(_diagnostic("WORKFLOW_VARIANT_LIMIT", "Workflow exceeds 256 expanded job variants; no workflow role paths are admitted.", path, job_node))
                return []
    return expanded


def _literal_environment(*scopes):
    environment = {}
    for scope in scopes:
        if "env" not in scope:
            continue
        values = mapping(scope["env"])
        if values is None:
            environment.clear()
            continue
        for name, node in values.items():
            try:
                value = _matrix_value(node)
                environment[name] = value if isinstance(value, str) else json.dumps(value)
            except ValueError:
                environment[name] = None
    return environment


def _resolution_locations(path, fields, matrix, environment, *scopes):
    references = [match for value in fields if isinstance(value, str) for match in LITERAL_REFERENCE.finditer(value)]
    sources = []
    for reference in references:
        context, name = reference.group(1), reference.group(2)
        if context == "matrix" and name in matrix:
            for scope in scopes:
                strategy = mapping(scope.get("strategy"))
                if strategy and "matrix" in strategy:
                    sources.append({"kind": "literal-matrix", **location(path, strategy["matrix"])})
        elif context == "env" and environment.get(name) is not None:
            for scope in reversed(scopes):
                bindings = mapping(scope.get("env"))
                if bindings and name in bindings:
                    sources.append({"kind": "literal-env", "name": name, **location(path, bindings[name])})
                    break
    return list({canonical(source): source for source in sources}.values())


def _resolve_literal(value, matrix, environment):
    if value is None:
        return None
    def substitute(match):
        values = matrix if match.group(1) == "matrix" else environment
        resolved = values.get(match.group(2))
        if resolved is None:
            return match.group(0)
        return resolved if isinstance(resolved, str) else json.dumps(resolved)
    return LITERAL_REFERENCE.sub(substitute, value)


def _references(value, field):
    if not isinstance(value, str) or len(value) > 4096 or "${{" not in value:
        return []
    found = {(match.group(1), match.group(2)) for match in CONTEXT_REFERENCE.finditer(value)}
    return [{"context": context, "name": name, "field": field} for context, name in sorted(found) if len(name) <= 256]


def _public_matrix(matrix):
    return {key: "[redacted]" if SENSITIVE_MATRIX_KEY.search(key) else value for key, value in matrix.items()}


def _identifier(kind, *parts):
    digest = sha256(canonical([kind, *parts])).hexdigest()[:20]
    return f"{kind}-{digest}"


def _diagnostic(code, message, path, node, severity="warning"):
    return {"code": code, "severity": severity, "message": message, "location": location(path, node)}


def _permissions(node):
    if scalar(node) == "write-all":
        return {"id-token": "write"}
    if scalar(node) == "read-all":
        return {}
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
    exact = branches if all(branch and not any(character in branch for character in GLOB_CHARACTERS) and "${{" not in branch for branch in branches) else []
    return sorted(set(exact)), True


def extract_github_actions(path, root):
    diagnostics = []
    identities = []
    root_map = mapping(root)
    if root_map is None:
        return [], [], [], [_diagnostic("UNSUPPORTED_WORKFLOW_ROOT", "Workflow root must be a mapping.", path, root)]
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
        return [workflow], [], [], diagnostics

    requests = []
    expanded = _expanded_jobs(jobs, path, diagnostics)
    workflow["job_count"] = len(jobs)
    workflow["expanded_job_count"] = sum(supported for _, _, _, _, supported in expanded)
    workflow["unresolved_matrix_jobs"] = sum(not supported for _, _, _, _, supported in expanded)
    for job_id, job_node, base_job_id, matrix, matrix_supported in expanded:
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
        token_allowed = effective_permissions is not None and (effective_permissions.get("id-token") or "").lower() == "write"
        if "environment" in job:
            diagnostics.append(_diagnostic("UNSUPPORTED_ENVIRONMENT", "Environment jobs use environment-specific OIDC subjects and protection rules, outside the branch-subject profile.", path, job["environment"]))
        steps = sequence(job.get("steps")) if "steps" in job else None
        if steps is None:
            continue
        for index, step_node in enumerate(steps):
            step = mapping(step_node)
            if step is None:
                continue
            action = scalar(step.get("uses")) if "uses" in step else None
            parameters = mapping(step.get("with")) if "with" in step else None
            known_action = bool(action and "@" in action and action.split("@", 1)[0].lower() == "aws-actions/configure-aws-credentials")
            local_action = bool(action and action.startswith("./") and parameters and "role-to-assume" in parameters)
            if not known_action and not local_action:
                continue
            if len(identities) >= MAX_IDENTITY_REQUESTS:
                raise GraphError("Workflow exceeds the 512 identity-request limit.")
            role_node = parameters.get("role-to-assume") if parameters else None
            raw_role = scalar(role_node) if role_node is not None else None
            environment = _literal_environment(root_map, job, step)
            resolved_role = _resolve_literal(raw_role, matrix, environment)
            role_arn = resolved_role if resolved_role and ROLE_ARN.fullmatch(resolved_role) else None
            audience_node = parameters.get("audience") if parameters else None
            raw_audience = scalar(audience_node) if audience_node is not None else "sts.amazonaws.com"
            audience = _resolve_literal(raw_audience, matrix, environment)
            reasons = []

            def block(code, message, node):
                reasons.append(code)
                diagnostics.append(_diagnostic(code, message, path, node))

            if not matrix_supported:
                reasons.append("MATRIX_WORKFLOW_UNSUPPORTED")
            if "environment" in job:
                reasons.append("UNSUPPORTED_ENVIRONMENT")
            if local_action:
                block("LOCAL_ACTION_UNVERIFIED", "Local action accepts a role reference, but its authentication semantics are not inferred or executed.", step_node)
            unsupported_options = set(parameters or {}) & {"aws-access-key-id", "aws-secret-access-key", "web-identity-token-file", "inline-session-policy", "managed-session-policies"}
            unsupported_options.update(key for key in ("role-chaining", "force-skip-oidc") if parameters and key in parameters and scalar(parameters[key]) != "false")
            if unsupported_options:
                block("UNSUPPORTED_CREDENTIAL_OPTIONS", "Alternate credentials, chaining or session restrictions cannot be evaluated by this OIDC profile.", step_node)
            if not raw_role:
                block("ROLE_ARN_MISSING", "AWS credential configuration has no role-to-assume.", step_node)
            elif role_arn is None:
                block("DYNAMIC_ROLE_ARN", "AWS role-to-assume is unresolved or outside the supported literal ARN profile; no secret or runtime value is inferred.", role_node)
            if not token_allowed:
                block("OIDC_PERMISSION_MISSING", "The job does not grant a verified id-token write permission.", step_node)
            if not audience or "${{" in audience or len(audience) > 512:
                block("DYNAMIC_OIDC_AUDIENCE", "OIDC audience is unresolved and cannot be matched safely.", audience_node or step_node)
            references = _references(raw_role, "role-to-assume") + _references(raw_audience, "audience")
            resolution_locations = _resolution_locations(path, (raw_role, raw_audience), matrix, environment, root_map, job, step)
            identity = {
                "id": _identifier("workflow-identity", path, job_id, index), "workflow_id": workflow_id,
                "workflow_name": workflow["name"], "job_id": job_id, "base_job_id": base_job_id,
                "matrix": _public_matrix(matrix), "matrix_status": "unresolved" if not matrix_supported else "expanded" if matrix else "not-used",
                "action_reference": action, "action_kind": "local-action" if local_action else "aws-credentials",
                "role_arn": role_arn, "references": references,
                "token_permission": "write" if token_allowed else "unresolved" if effective_permissions is None else "not-granted",
                "branches": branches, "status": "unresolved" if reasons else "declared-request",
                "reason_codes": sorted(set(reasons)), "request_id": None,
                "confidence": "repository-verified", "location": location(path, role_node or step_node),
                "supporting_locations": resolution_locations,
            }
            identities.append(identity)
            if reasons:
                continue
            request_id = _identifier("oidc-request", path, job_id, index, role_arn)
            identity["request_id"] = request_id
            requests.append({
                "id": request_id,
                "workflow_id": workflow_id,
                "job_id": job_id,
                "base_job_id": base_job_id,
                "matrix": _public_matrix(matrix),
                "role_arn": role_arn,
                "audience": audience,
                "branches": branches,
                "action_reference": action,
                "confidence": "repository-verified",
                "matching_role_ids": [],
                "matching_trust_ids": [],
                "trust_match": "unresolved",
                "location": location(path, role_node),
                "supporting_locations": resolution_locations,
            })
    return [workflow], requests, identities, diagnostics
