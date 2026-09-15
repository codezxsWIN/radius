"""Deterministic repository evidence orchestration."""

from copy import deepcopy
from fnmatch import fnmatchcase
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re

from ..model import GraphError, canonical
from .acquisition import PROFILE as ACQUISITION_PROFILE, read_snapshot_file
from .aws_cloudformation import extract_cloudformation
from .github_actions import extract_github_actions
from .yaml_nodes import DocumentSyntaxError, compose_document, intrinsic_locations


PROFILE = "github-actions-aws-cfn-v0.1"
SLUG = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
WORKFLOW_SUFFIXES = (".yml", ".yaml")
CLOUDFORMATION_SUFFIXES = tuple(f".{name}.{suffix}" for name in ("template", "cfn", "cloudformation") for suffix in ("json", "yaml", "yml"))
CLOUDFORMATION_NAMES = frozenset(f"{name}.{suffix}" for name in ("template", "cloudformation") for suffix in ("json", "yaml", "yml"))
GAP_GUIDANCE = {
    "DYNAMIC_ROLE_ARN": ("Role identity unresolved", "Obtain the non-credential role ARN from an authorized configuration owner. Do not provide access keys, tokens or unrelated secret values."),
    "ROLE_ARN_MISSING": ("Role request absent", "The step does not declare a supported role. No role or permission is inferred and no permission change is recommended."),
    "ROLE_DECLARATION_NOT_FOUND": ("Matching IAM declaration missing", "Supply the matching role's trust and inline permission declarations in a supported source template. Deployment remains unverified."),
    "AMBIGUOUS_ROLE_DECLARATION": ("Role deployment ambiguous", "Disambiguate which source declaration belongs to the requested account and role path before using its permissions."),
    "GITHUB_TRUST_NOT_MATCHED": ("Trust context not established", "Review the declared OIDC subject, audience and triggering branch against the role trust. Do not broaden a trust merely to make analysis succeed."),
    "MATRIX_WORKFLOW_UNSUPPORTED": ("Matrix cannot be expanded safely", "Use a reviewed finite scalar matrix or provide the generated matrix as source evidence. Dynamic expressions and oversized products are not executed."),
    "LOCAL_ACTION_UNVERIFIED": ("Local action semantics unknown", "Review the local action's authentication behavior. Its role reference is retained, but the analyzer does not execute it or treat it as the known AWS action."),
    "UNSUPPORTED_CREDENTIAL_OPTIONS": ("Authentication or session restriction unresolved", "Inspect alternate credentials, role chaining and session policy restrictions. Values are not loaded and restrictions are not ignored."),
    "UNSUPPORTED_ENVIRONMENT": ("Environment subject outside profile", "Review the environment-specific OIDC subject and protection rules; branch-subject matching cannot establish this path."),
    "OIDC_PERMISSION_MISSING": ("OIDC start condition not established", "No verified id-token write permission is declared. Do not add permissions just to produce a finding."),
    "DYNAMIC_OIDC_AUDIENCE": ("OIDC audience unresolved", "Provide the declared audience through supported literal source context; the analyzer does not infer runtime values."),
    "MALFORMED_DOCUMENT": ("Source document could not be parsed", "Inspect the file syntax and encoding. No facts from the unparsed file contribute to access paths."),
    "CLOUDFORMATION_INTRINSICS_UNEVALUATED": ("Template expressions remain unevaluated", "Only independent literal declarations contribute to paths. Provide a reviewed resolved configuration to assess resources whose identity or permission depends on intrinsic functions."),
}


def _validate_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get("profile") != ACQUISITION_PROFILE:
        raise GraphError("Repository manifest is invalid or unsupported.")
    snapshot_hash = manifest.get("snapshot_hash")
    unsigned = deepcopy(manifest)
    unsigned.pop("snapshot_hash", None)
    if (not isinstance(snapshot_hash, str) or len(snapshot_hash) != 64
            or sha256(canonical(unsigned)).hexdigest() != snapshot_hash):
        raise GraphError("Repository manifest integrity check failed.")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise GraphError("Repository manifest contains an invalid file inventory.")
    paths = []
    for record in files:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise GraphError("Repository manifest contains an invalid file inventory.")
        path = record["path"]
        logical = PurePosixPath(path)
        if logical.is_absolute() or "\\" in path or any(part in {"", ".", ".."} for part in logical.parts):
            raise GraphError("Repository manifest contains an unsafe file path.")
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise GraphError("Repository manifest contains duplicate file paths.")
    return files, snapshot_hash


def _kind(path):
    if path.startswith(".github/workflows/"):
        remainder = path[len(".github/workflows/"):]
        if "/" not in remainder and remainder.lower().endswith(WORKFLOW_SUFFIXES):
            return "workflow"
    lower = path.lower()
    logical = PurePosixPath(lower)
    if (lower.endswith(CLOUDFORMATION_SUFFIXES) or logical.name in CLOUDFORMATION_NAMES
            or logical.suffix in {".json", ".yml", ".yaml"} and any(part in {"cloudformation", "cfn"} for part in logical.parts[:-1])):
        return "cloudformation"
    return None


def _diagnostic(code, message, path=None, severity="warning"):
    result = {"code": code, "severity": severity, "message": message}
    if path is not None:
        result["location"] = deepcopy(path) if isinstance(path, dict) else {"path": path, "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 1}
    return result


def _correlate(requests, roles, trusts, slug, diagnostics):
    roles_by_name = {}
    for role in roles:
        roles_by_name.setdefault(role["role_name"], []).append(role)
    trusts_by_role = {}
    for trust in trusts:
        trusts_by_role.setdefault(trust["role_id"], []).append(trust)
    for request in requests:
        role_name = request["role_arn"].rsplit("/", 1)[-1]
        role_account = request["role_arn"].split(":")[4]
        role_path = "/" + request["role_arn"].split(":role/", 1)[1].rsplit(role_name, 1)[0]
        matching_roles = [role for role in roles_by_name.get(role_name, []) if role.get("role_path", "/") == role_path]
        request["matching_role_ids"] = sorted(role["id"] for role in matching_roles)
        if not matching_roles:
            request["correlation_issue"] = "ROLE_DECLARATION_NOT_FOUND"
            diagnostics.append(_diagnostic("ROLE_DECLARATION_NOT_FOUND", "Requested AWS role has no matching literal CloudFormation declaration.", request["location"]))
            continue
        if len(matching_roles) != 1:
            request["matching_role_ids"] = []
            request["correlation_issue"] = "AMBIGUOUS_ROLE_DECLARATION"
            diagnostics.append(_diagnostic("AMBIGUOUS_ROLE_DECLARATION", "Multiple declarations share the requested role name; this profile cannot select a deployment.", request["location"]))
            continue
        exact_subjects = {f"repo:{slug}:ref:refs/heads/{branch}" for branch in request["branches"]}
        exact, broad = [], []
        for role in matching_roles:
            for trust in trusts_by_role.get(role["id"], []):
                if request["audience"] not in trust["audience"] or role_account not in trust.get("provider_accounts", []):
                    continue
                if not trust["broad"] and exact_subjects & set(trust["subjects"]):
                    exact.append(trust["id"])
                elif trust["broad"] and any(fnmatchcase(subject, pattern) for subject in exact_subjects for pattern in trust["subjects"]):
                    broad.append(trust["id"])
        if exact:
            request["matching_trust_ids"] = sorted(exact)
            request["trust_match"] = "exact-declared-configuration"
        elif broad:
            request["matching_trust_ids"] = sorted(broad)
            request["trust_match"] = "broad-potential"
        else:
            request["correlation_issue"] = "GITHUB_TRUST_NOT_MATCHED"
            diagnostics.append(_diagnostic("GITHUB_TRUST_NOT_MATCHED", "No supported declared GitHub OIDC trust matches this workflow branch and role request.", request["location"]))


def summarize_evidence_gaps(evidence):
    gaps = {}
    for diagnostic in evidence["diagnostics"]:
        code = diagnostic["code"]
        title, needed = GAP_GUIDANCE.get(code, ("Source-profile limitation", "Review the declaration and diagnostic at the listed source locations. Unsupported evidence is not a permission grant or a security verdict."))
        gap = gaps.setdefault(code, {"code": code, "title": title, "evidence_needed": needed, "occurrences": 0, "locations": [], "references": []})
        gap["occurrences"] += 1
        source = diagnostic.get("location")
        if source and source not in gap["locations"]:
            gap["locations"].append(deepcopy(source))
    identities = evidence["facts"]["workflow_identities"]
    if identities and not evidence["facts"]["aws_roles"]:
        gaps["IAM_DECLARATIONS_REQUIRED"] = {
            "code": "IAM_DECLARATIONS_REQUIRED", "title": "No supported IAM role declarations",
            "evidence_needed": "Include the corresponding role trust and permission source templates. Workflow role references alone cannot establish cloud-resource access.",
            "occurrences": len(identities), "locations": [], "references": [],
        }
    for identity in identities:
        for code in identity["reason_codes"]:
            if code not in gaps:
                continue
            for reference in identity["references"]:
                if reference not in gaps[code]["references"]:
                    gaps[code]["references"].append(deepcopy(reference))
    for gap in gaps.values():
        gap["references"].sort(key=lambda reference: (reference["context"], reference["name"], reference["field"]))
        gap["locations"].sort(key=lambda source: (source["path"], source["start_line"], source["start_column"]))
    return [gaps[code] for code in sorted(gaps)]


def collect_repository_evidence(root: Path, manifest: dict, repository_slug: str) -> dict:
    """Collect bounded source facts from a verified local repository snapshot."""
    if not isinstance(repository_slug, str) or not SLUG.fullmatch(repository_slug):
        raise GraphError("Repository slug must have the supported owner/repository form.")
    files, snapshot_hash = _validate_manifest(manifest)
    try:
        source = Path(root).resolve(strict=True)
        if not source.is_dir() or manifest.get("source", {}).get("name") != source.name:
            raise GraphError("Repository manifest does not match the selected repository.")
    except GraphError:
        raise
    except (OSError, RuntimeError):
        raise GraphError("Repository input must be an existing local directory.") from None

    facts = {"workflows": [], "oidc_role_requests": [], "workflow_identities": [], "aws_roles": [], "aws_trusts": [], "aws_secret_grants": []}
    diagnostics = []
    selected = [(record, _kind(record["path"])) for record in files]
    selected = [(record, kind) for record, kind in selected if kind is not None]
    workflow_files = sum(kind == "workflow" for record, kind in selected)
    cloudformation_files = sum(kind == "cloudformation" for record, kind in selected)
    parsed_files = 0
    unsupported_files = 0
    source_files = []

    for record, kind in sorted(selected, key=lambda item: item[0]["path"]):
        path = record["path"]
        file_status = {"path": path, "kind": kind, "sha256": record["sha256"], "size": record["size"], "status": "parsed"}
        source_files.append(file_status)
        payload = read_snapshot_file(source, record)
        try:
            document = compose_document(payload, allow_cloudformation_tags=kind == "cloudformation")
        except DocumentSyntaxError:
            unsupported_files += 1
            file_status["status"] = "unparsed"
            diagnostics.append(_diagnostic("MALFORMED_DOCUMENT", "Selected repository document is malformed or not valid UTF-8.", path, "error"))
            continue
        parsed_files += 1
        if kind == "workflow":
            workflows, requests, identities, issues = extract_github_actions(path, document)
            facts["workflows"].extend(workflows)
            facts["oidc_role_requests"].extend(requests)
            facts["workflow_identities"].extend(identities)
            diagnostics.extend(issues)
        else:
            intrinsics = intrinsic_locations(path, document)
            if intrinsics:
                diagnostics.append(_diagnostic("CLOUDFORMATION_INTRINSICS_UNEVALUATED", f"{len(intrinsics)} intrinsic expression(s) are retained as opaque source; only independent literal declarations can contribute to paths.", intrinsics[0]))
            roles, trusts, grants, issues = extract_cloudformation(path, document)
            facts["aws_roles"].extend(roles)
            facts["aws_trusts"].extend(trusts)
            facts["aws_secret_grants"].extend(grants)
            diagnostics.extend(issues)

    for collection in facts.values():
        collection.sort(key=lambda item: item["id"])
    _correlate(facts["oidc_role_requests"], facts["aws_roles"], facts["aws_trusts"], repository_slug, diagnostics)
    requests_by_id = {request["id"]: request for request in facts["oidc_role_requests"]}
    for identity in facts["workflow_identities"]:
        request = requests_by_id.get(identity["request_id"])
        if request is not None:
            identity["trust_match"] = request["trust_match"]
            identity["status"] = "matched-trust" if request["trust_match"] == "exact-declared-configuration" else "declared-request"
            if request.get("correlation_issue"):
                identity["reason_codes"].append(request["correlation_issue"])
            elif request["trust_match"] != "exact-declared-configuration":
                identity["reason_codes"].append("GITHUB_TRUST_NOT_MATCHED")
    diagnostics = list({canonical(issue): issue for issue in diagnostics}.values())
    diagnostics.sort(key=lambda item: (
        item.get("location", {}).get("path", ""),
        item.get("location", {}).get("start_line", 0),
        item["code"],
    ))
    for record in source_files:
        record["diagnostic_count"] = sum(issue.get("location", {}).get("path") == record["path"] for issue in diagnostics)
        record["fact_count"] = sum(fact.get("location", {}).get("path") == record["path"] for collection in facts.values() for fact in collection)
        if record["status"] == "parsed" and record["diagnostic_count"]:
            record["status"] = "partial"
    result = {
        "format_version": "0.1",
        "profile": PROFILE,
        "repository": {"slug": repository_slug, "snapshot_hash": snapshot_hash},
        "facts": facts,
        "source_files": source_files,
        "identity_summary": {
            "workflow_jobs": sum(workflow.get("job_count", 0) for workflow in facts["workflows"]),
            "expanded_job_variants": sum(workflow.get("expanded_job_count", 0) for workflow in facts["workflows"]),
            "unresolved_matrix_jobs": sum(workflow.get("unresolved_matrix_jobs", 0) for workflow in facts["workflows"]),
            "identity_requests": len(facts["workflow_identities"]),
            "unresolved_requests": sum(identity["status"] == "unresolved" for identity in facts["workflow_identities"]),
            "matched_trust_requests": sum(identity["status"] == "matched-trust" for identity in facts["workflow_identities"]),
        },
        "diagnostics": diagnostics,
        "coverage": {
            "selected_files": len(selected),
            "parsed_files": parsed_files,
            "unsupported_files": unsupported_files,
            "workflow_files": workflow_files,
            "cloudformation_files": cloudformation_files,
            "deployed_aws_state": "unverified",
        },
    }
    result["evidence_hash"] = sha256(canonical(result)).hexdigest()
    return result
