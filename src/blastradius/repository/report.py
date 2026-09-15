"""Deterministic, evidence-first Markdown for repository attack-path results."""

from ..model import GraphError
from .findings import PROFILE


MARKDOWN = frozenset("\\`*_{}[]()#|<>")
PATH_KINDS = frozenset({"authenticates_as", "can_assume", "assigned", "grants"})
COVERAGE_LABELS = {
    "selected_files": "Selected files",
    "parsed_files": "Parsed files",
    "unsupported_files": "Unsupported files",
    "workflow_files": "Workflow files",
    "cloudformation_files": "CloudFormation files",
    "archive_skipped_files": "Archive skipped files",
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
            high = sum(finding.get("priority") == "high" for finding in findings)
            noun = "path" if high == 1 else "paths"
            lines.extend(["", f"{high} high-priority declared {noun}."])
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
            remediation = finding["remediation"]
            lines.extend([
                "",
                "### Remediation simulation",
                "",
                _safe(remediation["description"]),
                f"Applied automatically: {_yes(remediation['applied'])}",
                f"Before: {remediation['before_absolute_reach']} | After: {remediation['after_absolute_reach']} | Path broken: {_yes(remediation['path_broken'])}",
                f"Deployed AWS state: {_safe(finding['deployed_aws_state'])}",
            ])

        lines.extend(["", "## Coverage and limitations", ""])
        for key in ("selected_files", "parsed_files", "unsupported_files", "workflow_files", "cloudformation_files", "archive_skipped_files"):
            if key in coverage:
                lines.append(f"- {COVERAGE_LABELS[key]}: {coverage[key]}")
        lines.append(f"- Deployed AWS state: {_safe(coverage['deployed_aws_state'])}")
        if source and source.get("archive_extraction", {}).get("skipped"):
            lines.append("- Skipped archive inputs:")
            for skipped in source["archive_extraction"]["skipped"]:
                lines.append(f"  - {_safe(skipped['path'])}: {_safe(skipped['reason'])} ({skipped['size']} bytes)")

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
