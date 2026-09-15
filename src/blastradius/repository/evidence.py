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
from .yaml_nodes import DocumentSyntaxError, compose_document


PROFILE = "github-actions-aws-cfn-v0.1"
SLUG = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
WORKFLOW_SUFFIXES = (".yml", ".yaml")
CLOUDFORMATION_SUFFIXES = (".template.json", ".cfn.json", ".cloudformation.json")


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
    if lower.endswith(CLOUDFORMATION_SUFFIXES):
        return "cloudformation"
    return None


def _diagnostic(code, message, path=None, severity="warning"):
    result = {"code": code, "severity": severity, "message": message}
    if path is not None:
        result["location"] = {"path": path, "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 1}
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
        matching_roles = roles_by_name.get(role_name, [])
        request["matching_role_ids"] = sorted(role["id"] for role in matching_roles)
        if not matching_roles:
            diagnostics.append(_diagnostic("ROLE_DECLARATION_NOT_FOUND", "Requested AWS role has no matching literal CloudFormation declaration.", request["location"]["path"]))
            continue
        exact_subjects = {f"repo:{slug}:ref:refs/heads/{branch}" for branch in request["branches"]}
        exact, broad = [], []
        for role in matching_roles:
            for trust in trusts_by_role.get(role["id"], []):
                if request["audience"] not in trust["audience"]:
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
            diagnostics.append(_diagnostic("GITHUB_TRUST_NOT_MATCHED", "No supported declared GitHub OIDC trust matches this workflow branch and role request.", request["location"]["path"]))


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

    facts = {"workflows": [], "oidc_role_requests": [], "aws_roles": [], "aws_trusts": [], "aws_secret_grants": []}
    diagnostics = []
    selected = [(record, _kind(record["path"])) for record in files]
    selected = [(record, kind) for record, kind in selected if kind is not None]
    workflow_files = sum(kind == "workflow" for record, kind in selected)
    cloudformation_files = sum(kind == "cloudformation" for record, kind in selected)
    parsed_files = 0
    unsupported_files = 0

    for record, kind in sorted(selected, key=lambda item: item[0]["path"]):
        path = record["path"]
        payload = read_snapshot_file(source, record)
        try:
            document = compose_document(payload)
        except DocumentSyntaxError:
            unsupported_files += 1
            diagnostics.append(_diagnostic("MALFORMED_DOCUMENT", "Selected repository document is malformed or not valid UTF-8.", path, "error"))
            continue
        parsed_files += 1
        if kind == "workflow":
            workflows, requests, issues = extract_github_actions(path, document)
            facts["workflows"].extend(workflows)
            facts["oidc_role_requests"].extend(requests)
            diagnostics.extend(issues)
        else:
            roles, trusts, grants, issues = extract_cloudformation(path, document)
            facts["aws_roles"].extend(roles)
            facts["aws_trusts"].extend(trusts)
            facts["aws_secret_grants"].extend(grants)
            diagnostics.extend(issues)

    for collection in facts.values():
        collection.sort(key=lambda item: item["id"])
    _correlate(facts["oidc_role_requests"], facts["aws_roles"], facts["aws_trusts"], repository_slug, diagnostics)
    diagnostics.sort(key=lambda item: (
        item.get("location", {}).get("path", ""),
        item.get("location", {}).get("start_line", 0),
        item["code"],
    ))
    result = {
        "format_version": "0.1",
        "profile": PROFILE,
        "repository": {"slug": repository_slug, "snapshot_hash": snapshot_hash},
        "facts": facts,
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
