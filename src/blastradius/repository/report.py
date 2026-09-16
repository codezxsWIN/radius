"""Deterministic, evidence-first Markdown for repository attack-path results."""

from hashlib import sha256
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from .. import __version__
from ..model import GraphError, canonical, read_json
from .findings import PROFILE


MARKDOWN = frozenset("\\`*_{}[]()#|<>")
PATH_KINDS = frozenset({"authenticates_as", "can_assume", "assigned", "grants"})
COVERAGE_LABELS = {
    "inventory_files": "Inventoried files",
    "selected_files": "Selected files",
    "parsed_files": "Parsed files",
    "unsupported_files": "Unsupported files",
    "workflow_files": "Workflow files",
    "cloudformation_files": "CloudFormation files",
    "terraform_files": "Terraform JSON files",
    "terraform_relevant_files": "Terraform JSON files with IAM/module declarations",
    "terraform_hcl_files": "Terraform HCL files (not assessed)",
    "archive_skipped_files": "Archive skipped files",
    "out_of_profile_files": "Outside source profile",
    "skipped_entries": "Skipped entries",
}


def _safe(value):
    text = str(value)
    rendered = []
    for character in text:
        code = ord(character)
        if code < 32 or code == 127:
            rendered.append(f"\\u{code:04x}")
        elif character in MARKDOWN:
            rendered.append("\\" + character)
        else:
            rendered.append(character)
    return "".join(rendered)


def _yes(value):
    return "yes" if value else "no"


def _location(location):
    if not isinstance(location, dict) or not isinstance(location.get("path"), str):
        raise GraphError("Repository finding evidence has no source location.")
    line = location.get("start_line")
    column = location.get("start_column")
    if type(line) is not int or type(column) is not int:
        raise GraphError("Repository finding evidence has an invalid source location.")
    return f"{_safe(location['path'])}:{line}:{column}"


def _evidence_locations(evidence):
    locations = [_location(evidence.get("location"))]
    for supporting in evidence.get("supporting_locations", []):
        candidate = _location(supporting)
        if candidate not in locations:
            locations.append(candidate)
    return ", ".join(locations)


def render_repository_markdown(result: dict) -> str:
    """Render repository-attack-path-v0.1 as inert, deterministic Markdown."""
    if not isinstance(result, dict) or result.get("profile") != PROFILE:
        raise GraphError("Only repository attack-path results can use this report.")
    try:
        repository = result["repository"]
        summary = result["summary"]
        findings = result["findings"]
        coverage = result["coverage"]
        diagnostics = result["diagnostics"]
        if (not isinstance(repository, dict) or not isinstance(summary, dict)
                or not isinstance(findings, list) or not isinstance(coverage, dict)
                or not isinstance(diagnostics, list)):
            raise GraphError("Repository analysis result is malformed.")

        lines = [
            "# Blast Radius Repository Analysis",
            "",
            f"Repository: {_safe(repository['slug'])}",
        ]
        if repository.get("is_example"):
            lines.extend(["", "Dataset: bundled example, not a live repository."])
        source = repository.get("input")
        if source:
            lines.extend([
                f"Source: {_safe(source['url'])}",
                f"Requested ref: {_safe(source['requested_ref'])}",
                f"Resolved commit: {_safe(source['commit_sha'])}",
            ])
        lines.extend([
            "",
            "## Result",
            "",
            f"Findings: {summary['finding_count']}",
            f"Declared reachable secrets: {summary['declared_reachable_secrets']}",
        ])
        if findings:
            lines.extend(["", f"{len(findings)} declared capabilities. Necessity, exploitability and policy violations have not been assessed."])
        else:
            lines.extend(["", _safe(result["conclusion"])])

        for index, finding in enumerate(findings, 1):
            kinds = [step["kind"] for step in finding["path"]]
            if any(kind not in PATH_KINDS for kind in kinds):
                raise GraphError("Repository finding contains an unsupported path kind.")
            path_kinds = " -> ".join(kinds)
            lines.extend([
                "",
                f"## Finding {index} - {_safe(finding['priority']).upper()}",
                "",
                f"Title: {_safe(finding['title'])}",
                f"Confidence: {_safe(finding['confidence'])}",
                f"Assumption: {_safe(finding['start_condition'])}",
                f"Impact: {_safe(finding['impact']['action'])} on {_safe(finding['impact']['resource_arn'])}",
                f"Path: {path_kinds}",
                "",
                "### Evidence path",
                "",
            ])
            for step_index, step in enumerate(finding["path"], 1):
                lines.extend([
                    f"{step_index}. {step['kind']}: {_safe(step['source']['name'])} -> {_safe(step['target']['name'])}",
                    f"   Evidence: {_evidence_locations(step['evidence'])}",
                ])
            authorization = finding.get("authorization")
            if authorization is not None:
                workflow, trust, permission = authorization["workflow"], authorization["trust"], authorization["permission"]
                lines.extend([
                    "", "### Matched declarations", "",
                    f"Workflow job: {_safe(workflow['name'])} / {_safe(workflow['job_id'])}",
                    f"Requested role: {_safe(workflow['role_arn'])}",
                    f"Trust subjects ({_safe(trust['operator'])}): {_safe(', '.join(trust['subjects']))}",
                    f"Trust audience: {_safe(', '.join(trust['audience']))}",
                    f"Provider accounts: {_safe(', '.join(trust['provider_accounts']))}",
                    f"Trust source: {_location(trust['location'])}",
                    f"Permission source: {_location(permission['location'])}",
                ])
            remediation = finding["remediation"]
            lines.extend([
                "",
                "### Remediation simulation",
                "",
                _safe(remediation["description"]),
                f"Applied automatically: {_yes(remediation['applied'])}",
                f"Before: {remediation['before_absolute_reach']} | After: {remediation['after_absolute_reach']} | Path broken: {_yes(remediation['path_broken'])}",
                f"Deployed AWS state: {_safe(finding['deployed_aws_state'])}",
                _safe(remediation.get("scope", "Modeled routes only; remaining deployed access is unverified.")),
            ])
            for alternative in finding.get("unmodeled_alternatives", []):
                lines.append(f"Unmodeled alternative: {_safe(', '.join(alternative.get('subjects', [])))} at {_location(alternative['location'])}")

        identities = result.get("identity_requests", [])
        if identities:
            summary = result.get("identity_summary", {})
            lines.extend(["", "## Workflow identity evidence", "",
                          f"Identity request variants: {len(identities)}",
                          f"Expanded job variants: {summary.get('expanded_job_variants', 0)}",
                          f"Unresolved requests: {summary.get('unresolved_requests', 0)}",
                          "", "These are source observations, not additional vulnerability findings or verified deployed access.", ""])
            for identity in identities:
                role = identity.get("role_arn") or ", ".join(f"{reference['context']}.{reference['name']}" for reference in identity["references"]) or "No supported role value"
                matrix = ", ".join(f"{key}={value}" for key, value in sorted(identity.get("matrix", {}).items())) or "none"
                lines.extend([
                    f"- {_safe(identity['workflow_name'])} / {_safe(identity['base_job_id'])}: {_safe(identity['status'])}",
                    f"  Role/reference: {_safe(role)} | id-token: {_safe(identity['token_permission'])}",
                    f"  Matrix: {_safe(matrix)} | Action: {_safe(identity['action_reference'])}",
                    f"  Source: {_evidence_locations(identity)}",
                ])
                if identity["reason_codes"]:
                    lines.append(f"  Blocking evidence: {_safe(', '.join(identity['reason_codes']))}")
        if result.get("evidence_gaps"):
            lines.extend(["", "## Evidence needed to continue", ""])
            for gap in result["evidence_gaps"]:
                lines.extend([f"### {_safe(gap['title'])}", "", _safe(gap["evidence_needed"]), ""])
                if gap["references"]:
                    references = sorted({f"{reference['context']}.{reference['name']}" for reference in gap["references"]})
                    lines.extend([f"References: {_safe(', '.join(references))}", ""])

        lines.extend(["", "## Coverage and limitations", ""])
        for key in COVERAGE_LABELS:
            if key in coverage:
                lines.append(f"- {COVERAGE_LABELS[key]}: {coverage[key]}")
        lines.append(f"- Deployed AWS state: {_safe(coverage['deployed_aws_state'])}")
        if source and source.get("archive_extraction", {}).get("skipped"):
            lines.append("- Skipped archive inputs:")
            for skipped in source["archive_extraction"]["skipped"]:
                lines.append(f"  - {_safe(skipped['path'])}: {_safe(skipped['reason'])} ({skipped['size']} bytes)")
        if result.get("source_files"):
            lines.extend(["", "### Selected source files", ""])
            for record in result["source_files"]:
                lines.append(f"- {_safe(record['path'])}: {_safe(record['status'])}, {record['fact_count']} facts, {record['diagnostic_count']} diagnostics; SHA-256 {_safe(record['sha256'])}")
        if result.get("skipped_inputs"):
            lines.extend(["", "### Skipped local inputs", ""])
            for record in result["skipped_inputs"]:
                lines.append(f"- {_safe(record['path'])}: {_safe(record['reason'])}")

        lines.extend(["", "## Diagnostics", ""])
        if diagnostics:
            for diagnostic in diagnostics:
                location = diagnostic.get("location")
                where = f" at {_location(location)}" if location else ""
                lines.append(f"- {_safe(diagnostic['severity']).upper()} {_safe(diagnostic['code'])}{where}: {_safe(diagnostic['message'])}")
        else:
            lines.append("No parser diagnostics were emitted within the supported profile.")
        lines.extend([
            "",
            "Repository declarations are not proof of effective deployed access. Unsupported or absent evidence is not a safety verdict.",
            "",
            f"Analysis hash: {_safe(result['analysis_hash'])}",
            "",
        ])
        return "\n".join(lines)
    except GraphError:
        raise
    except (KeyError, TypeError, ValueError):
        raise GraphError("Repository analysis result is malformed.") from None


def _display(value):
    return "".join(character if ord(character) >= 32 and ord(character) != 127 else " " for character in str(value))


def read_repository_result(path):
    source = Path(path)
    if source.stat().st_size > 32 * 1024 * 1024:
        raise GraphError("Repository result exceeds the 32 MiB import limit.")
    with source.open(encoding="utf-8") as stream:
        result = read_json(stream)
    if not isinstance(result, dict) or result.get("profile") != PROFILE:
        raise GraphError("Only repository attack-path results can use this report.")
    unsigned = {key: value for key, value in result.items() if key != "analysis_hash"}
    if sha256(canonical(unsigned)).hexdigest() != result.get("analysis_hash"):
        raise GraphError("Repository result content hash does not match. This check is integrity, not source authentication.")
    render_repository_markdown(result)
    render_repository_sarif(result)
    return result


def render_repository_result(result, format="json"):
    if format == "json":
        return canonical(result) + b"\n"
    if format == "md":
        return render_repository_markdown(result)
    if format == "sarif":
        return canonical(render_repository_sarif(result)) + b"\n"
    if format == "html":
        from .view import render_repository_html
        return render_repository_html(result)
    raise GraphError("Unsupported repository report format.")


def _sarif_location(location, message=None):
    if not isinstance(location, dict) or not isinstance(location.get("path"), str):
        raise GraphError("Source location is missing from the repository finding.")
    relative = location["path"]
    if (not relative or "\\" in relative or ":" in relative or relative.startswith("/")
            or any(part in {"", ".", ".."} for part in relative.split("/"))
            or any(ord(character) < 32 or ord(character) == 127 for character in relative)):
        raise GraphError("Source location must be a safe repository-relative path.")
    line, column = location.get("start_line"), location.get("start_column")
    if type(line) is not int or type(column) is not int or line < 1 or column < 1:
        raise GraphError("Source location must use positive one-based positions.")
    result = {"physicalLocation": {"artifactLocation": {"uri": quote(PurePosixPath(relative).as_posix(), safe="/"), "uriBaseId": "%SRCROOT%"}, "region": {"startLine": line, "startColumn": column}}}
    if message is not None:
        result["message"] = {"text": _display(message)}
    return result


def render_repository_sarif(result: dict) -> dict:
    """Render declared paths as review findings, never a deployed-access verdict."""
    if not isinstance(result, dict) or result.get("profile") != PROFILE:
        raise GraphError("Only repository attack-path results can use this report.")
    try:
        results = []
        for finding in result["findings"]:
            path = finding["path"]
            if not path or any(step["kind"] not in PATH_KINDS for step in path):
                raise GraphError("Repository finding contains an unsupported path.")
            remediation = finding["remediation"]
            message = (
                f"{finding['start_condition']} Declared capability: {finding['impact']['action']} on "
                f"{finding['impact']['resource_arn']}. Deployed AWS state: {finding['deployed_aws_state']}. "
                f"Simulation only: {remediation['description']} "
                f"Reach {remediation['before_absolute_reach']} -> {remediation['after_absolute_reach']}; "
                f"modeled path broken: {_yes(remediation['path_broken'])}. No change was applied. "
                f"{remediation.get('scope', 'Deployed access remains unverified.')}"
            )
            locations, flow, seen = [], [], set()
            for step in path:
                evidence = step["evidence"]
                source_locations = [evidence["location"], *evidence.get("supporting_locations", [])]
                for source in source_locations:
                    location = _sarif_location(source, f"{step['kind']}: {step['source']['name']} -> {step['target']['name']}")
                    flow.append({"location": location, "executionOrder": len(flow) + 1})
                    identity = canonical(location["physicalLocation"])
                    if identity not in seen:
                        seen.add(identity)
                        locations.append({"id": len(locations) + 1, **location})
            fingerprint = sha256(canonical([result["repository"]["slug"], path[0]["evidence"]["location"]["path"], finding["start_condition"], finding["impact"]])).hexdigest()
            results.append({
                "ruleId": "BR-REPO-001", "level": "note", "kind": "review",
                "message": {"text": _display(message)}, "locations": [locations[0]],
                "relatedLocations": locations[1:], "codeFlows": [{"threadFlows": [{"locations": flow}]}],
                "partialFingerprints": {"declaredPath/v1": fingerprint},
                "properties": {"findingId": finding["id"], "confidence": finding["confidence"],
                               "deployedAwsState": finding["deployed_aws_state"], "remediationApplied": False,
                               "beforeAbsoluteReach": remediation["before_absolute_reach"],
                               "afterAbsoluteReach": remediation["after_absolute_reach"], "pathBroken": remediation["path_broken"]},
            })
        notifications = [{"descriptor": {"id": _display(item["code"])}, "level": "warning" if item.get("severity") in {"warning", "error"} else "note", "message": {"text": _display(item["message"])}} for item in result["diagnostics"]]
        if not results:
            notifications.insert(0, {"descriptor": {"id": "NO_COMPLETE_PATH_PROVEN"}, "level": "note", "message": {"text": _display(result["conclusion"])}})
        return {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "Blast Radius Repository Review", "version": __version__,
                      "rules": [{"id": "BR-REPO-001", "shortDescription": {"text": "Declared workflow identity can read a declared secret"},
                                 "fullDescription": {"text": "Review a source-backed GitHub Actions OIDC to declared AWS Secrets Manager path under an assumed job compromise. This is a capability, not proof of excessive access, exploitability or deployed AWS access."},
                                 "defaultConfiguration": {"level": "note"}, "properties": {"tags": ["security", "configuration", "review"]}}]}},
                      "results": results, "invocations": [{"executionSuccessful": True, "toolExecutionNotifications": notifications}],
                      "properties": {"profile": PROFILE, "repository": result["repository"], "coverage": result["coverage"],
                                     "identitySummary": result.get("identity_summary", {}), "evidenceGaps": result.get("evidence_gaps", []),
                                     "conclusion": result["conclusion"], "analysisHash": result["analysis_hash"], "zeroFindingsIsNotSafety": True}}],
        }
    except GraphError:
        raise
    except (KeyError, TypeError, ValueError):
        raise GraphError("Repository analysis result is malformed.") from None
