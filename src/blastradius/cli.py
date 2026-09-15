"""Command-line entry points for synthetic generation, analysis and reporting."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

from . import __version__
from .analysis import Analysis, compare, modify_binding
from .model import GraphError, MODELS, canonical, read_graph, validate
from .oracle import expected
from .reports import render
from .signing import load_key, sign, verify
from .synthetic import synth, classic


def emit(path, contents, force=False, inputs=()):
    if path is None:
        sys.stdout.write(contents.decode("utf-8") if isinstance(contents, bytes) else contents)
        return
    destination = Path(path)
    for source in inputs:
        source = Path(source)
        if source.resolve() == destination.resolve() or (source.exists() and destination.exists() and source.samefile(destination)):
            raise GraphError("Output cannot overwrite an input file, even with --force.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = ("w" if force else "x") + ("b" if isinstance(contents, bytes) else "")
    with destination.open(mode, **({} if isinstance(contents, bytes) else {"encoding": "utf-8", "newline": "\n"})) as stream:
        stream.write(contents)


def load_result(path, key_path=None):
    with Path(path).open(encoding="utf-8") as stream:
        result = json.load(stream)
    if not isinstance(result, dict) or result.get("synthetic") is not True:
        raise GraphError("Only synthetic signed result files are supported.")
    verify(result, load_key(key_path))
    return result


def reject_internal_output(root, output_path):
    if output_path is None:
        return
    destination = output_path.resolve(strict=False)
    try:
        destination.relative_to(root)
    except ValueError:
        return
    raise GraphError("Repository-derived output must be outside the analyzed repository.")


def parser():
    root = argparse.ArgumentParser(prog="blastradius", description="Source-backed repository path analysis and synthetic identity blast-radius research tools.")
    root.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = root.add_subparsers(dest="command", required=True)

    def output(command):
        command.add_argument("--out", type=Path)
        command.add_argument("--force", action="store_true")

    def analysis_args(command):
        command.add_argument("--constraint-model", choices=tuple(MODELS), default="default")
        command.add_argument("--steps", type=int, default=1)
        command.add_argument("--threshold", type=str, default="0.25")

    generate = commands.add_parser("synth", help="Generate deterministic, fictional tenant JSON and small-graph independent expected results.")
    generate.add_argument("--principals", type=int, default=80)
    generate.add_argument("--resources", type=int, default=40)
    generate.add_argument("--seed", type=int, default=7)
    generate.add_argument("--classic", action="store_true")
    output(generate)
    analyze = commands.add_parser("analyze", help="Validate, compute all metrics and sign the result with an external local key.")
    analyze.add_argument("tenant", type=Path)
    analysis_args(analyze)
    analyze.add_argument("--no-recommendations", action="store_true")
    analyze.add_argument("--path-limit", type=int, default=100)
    analyze.add_argument("--signing-key", type=Path)
    output(analyze)
    report = commands.add_parser("report", help="Verify a result and export JSON, SARIF, Markdown or the self-contained dashboard.")
    report.add_argument("result", type=Path)
    report.add_argument("--format", choices=("json", "sarif", "html", "md"), default="md")
    report.add_argument("--signing-key", type=Path)
    output(report)
    explain = commands.add_parser("explain", help="Explain a named credential using its signed source snapshot and model.")
    explain.add_argument("result", type=Path)
    explain.add_argument("--credential", required=True)
    explain.add_argument("--signing-key", type=Path)
    output(explain)
    whatif = commands.add_parser("whatif", help="Simulate one binding removal or addition without changing the input; deny changes can increase reach.")
    whatif.add_argument("tenant", type=Path)
    selection = whatif.add_mutually_exclusive_group(required=True)
    selection.add_argument("--remove-binding")
    selection.add_argument("--add-binding", type=Path)
    analysis_args(whatif)
    output(whatif)
    check = commands.add_parser("verify-manifest", help="Verify both HMAC and content hash against an external trusted local key.")
    check.add_argument("result", type=Path)
    check.add_argument("--signing-key", type=Path)
    collect = commands.add_parser("collect-entra-azure", help="Normalize a fully materialized synthetic Graph/ARM export bundle; no live collection flag.")
    collect.add_argument("--exports", type=Path, required=True)
    output(collect)
    aws = commands.add_parser("collect-aws-iam", help="Normalize the explicitly bounded synthetic IAM export profile; no AWS account calls.")
    aws.add_argument("--exports", type=Path, required=True)
    output(aws)
    kubernetes = commands.add_parser("collect-kubernetes-rbac", help="Normalize the synthetic read-only Kubernetes RBAC profile; no kubeconfig or cluster calls.")
    kubernetes.add_argument("--exports", type=Path, required=True)
    output(kubernetes)
    inspect = commands.add_parser("inspect-repo", help="Safely inventory an untrusted local repository without executing or parsing its contents.")
    inspect.add_argument("repository", type=Path)
    output(inspect)
    evidence = commands.add_parser("inspect-repo-evidence", help="Extract bounded GitHub Actions and declared AWS CloudFormation OIDC evidence from a local repository.")
    evidence.add_argument("repository", type=Path)
    evidence.add_argument("--repository-slug", required=True)
    output(evidence)
    repository_analysis = commands.add_parser("analyze-repo", help="Find supported GitHub Actions-to-AWS secret paths in repository declarations and simulate a trust remediation.")
    repository_analysis.add_argument("repository", type=Path)
    repository_analysis.add_argument("--repository-slug", required=True)
    repository_analysis.add_argument("--format", choices=("json", "md", "sarif", "html"), default="json")
    repository_analysis.add_argument("--fail-on-findings", action="store_true", help="Exit 1 for supported declared paths; exit 0 means completed, not safe.")
    output(repository_analysis)
    github_analysis = commands.add_parser("analyze-github", help="Download and locally analyze one immutable commit from a public GitHub repository without Git or an access token.")
    github_analysis.add_argument("url")
    github_analysis.add_argument("--ref")
    github_analysis.add_argument("--format", choices=("json", "md", "sarif", "html"), default="json")
    github_analysis.add_argument("--fail-on-findings", action="store_true", help="Exit 1 for supported declared paths; exit 0 means completed, not safe.")
    output(github_analysis)
    repository_report = commands.add_parser("render-repo", help="Check a saved repository result's content hash and export it without rescanning source.")
    repository_report.add_argument("result", type=Path)
    repository_report.add_argument("--format", choices=("json", "md", "sarif", "html"), default="md")
    output(repository_report)
    review = commands.add_parser("review", help="Open the loopback-only repository review interface; source is never executed.")
    review.add_argument("--port", type=int, default=8765)
    review.add_argument("--no-open", action="store_true", help="Do not launch a browser automatically.")
    submit = commands.add_parser("submit", help="Print a local structural preview only; not anonymized or approved for publication.")
    submit.add_argument("result", type=Path)
    submit.add_argument("--dry-run", action="store_true", required=True)
    submit.add_argument("--signing-key", type=Path)
    conformance = commands.add_parser("conformance", help="Public standard conformance tools; no certification fees or network access.")
    operations = conformance.add_subparsers(dest="conformance_action", required=True)
    operations.add_parser("adapter", help="Reference JSON stdin/stdout adapter.")
    run = operations.add_parser("run", help="Execute an operator-supplied tool command against frozen fixtures.")
    run.add_argument("--tool", required=True)
    run.add_argument("--suite", type=Path, default=Path("conformance"))
    run.add_argument("--out", type=Path, default=Path("conformance/reports/reference"))
    run.add_argument("--timeout", type=float, default=10)
    return root


def main(argv=None):
    arguments = parser().parse_args(argv)
    try:
        command = arguments.command
        if command == "conformance":
            from .conformance import reference_response, run_suite
            if arguments.conformance_action == "adapter":
                from .model import read_json
                try:
                    response = reference_response(read_json(sys.stdin))
                except (GraphError, ValueError, RecursionError):
                    response = {"contract_version": "1.0-draft", "status": "error", "error": "INVALID_GRAPH_OR_PARAMETERS"}
                sys.stdout.write(canonical(response).decode("ascii") + "\n")
                return 0
            report = run_suite(arguments.tool, arguments.suite, arguments.out, arguments.timeout)
            print(json.dumps({"passed": report["passed"], "failed": report["failed"], "cases": report["case_count"], "suite_hash": report["suite_hash"]}, sort_keys=True))
            return 0 if report["failed"] == 0 else 1
        elif command == "collect-entra-azure":
            from .connectors.entra_azure import ingest
            graph = ingest(arguments.exports)
            emit(arguments.out, canonical(graph) + b"\n", arguments.force, tuple(arguments.exports.glob("*.json")))
        elif command == "collect-aws-iam":
            from .connectors.aws_iam import ingest
            graph = ingest(arguments.exports)
            emit(arguments.out, canonical(graph) + b"\n", arguments.force, tuple(arguments.exports.glob("*.json")))
        elif command == "collect-kubernetes-rbac":
            from .connectors.kubernetes_rbac import ingest
            graph = ingest(arguments.exports)
            emit(arguments.out, canonical(graph) + b"\n", arguments.force, (arguments.exports,))
        elif command == "inspect-repo":
            from .repository import acquire_repository
            repository = arguments.repository.resolve(strict=True)
            reject_internal_output(repository, arguments.out)
            manifest = acquire_repository(repository)
            emit(arguments.out, canonical(manifest) + b"\n", arguments.force)
        elif command == "inspect-repo-evidence":
            from .repository import acquire_repository, collect_repository_evidence
            repository = arguments.repository.resolve(strict=True)
            reject_internal_output(repository, arguments.out)
            manifest = acquire_repository(repository)
            evidence = collect_repository_evidence(repository, manifest, arguments.repository_slug)
            emit(arguments.out, canonical(evidence) + b"\n", arguments.force)
        elif command == "analyze-repo":
            from .repository import analyze_repository, render_repository_result
            repository = arguments.repository.resolve(strict=True)
            reject_internal_output(repository, arguments.out)
            result = analyze_repository(repository, arguments.repository_slug)
            payload = render_repository_result(result, arguments.format)
            emit(arguments.out, payload, arguments.force)
            if arguments.fail_on_findings and result["findings"]:
                return 1
        elif command == "analyze-github":
            from .repository import analyze_public_github_repository, render_repository_result
            result = analyze_public_github_repository(arguments.url, arguments.ref)
            payload = render_repository_result(result, arguments.format)
            emit(arguments.out, payload, arguments.force)
            if arguments.fail_on_findings and result["findings"]:
                return 1
        elif command == "render-repo":
            from .repository import read_repository_result, render_repository_result
            result = read_repository_result(arguments.result)
            emit(arguments.out, render_repository_result(result, arguments.format), arguments.force, (arguments.result,))
        elif command == "review":
            from .repository.server import serve_review
            serve_review(arguments.port, not arguments.no_open)
        elif command == "synth":
            graph = validate(classic() if arguments.classic else synth(arguments.principals, arguments.resources, arguments.seed))
            payload = canonical(graph) + b"\n"
            ground_truth = None
            if not arguments.classic and arguments.principals <= 40 and arguments.resources <= 40:
                ground_truth = expected(graph)
            emit(arguments.out, payload, arguments.force)
            if ground_truth is not None and arguments.out:
                emit(arguments.out.with_suffix(".expected.json"), canonical(ground_truth) + b"\n", arguments.force)
        elif command == "analyze":
            graph = read_graph(arguments.tenant)
            if not 0 <= arguments.path_limit <= 10000:
                raise GraphError("path-limit must be between zero and 10000.")
            result = Analysis(graph, arguments.constraint_model, arguments.steps, Fraction(arguments.threshold)).run(not arguments.no_recommendations, arguments.path_limit)
            signed = sign(result, load_key(arguments.signing_key, create=True))
            emit(arguments.out, canonical(signed) + b"\n", arguments.force, (arguments.tenant,))
        elif command in {"report", "explain", "verify-manifest", "submit"}:
            result = load_result(arguments.result, arguments.signing_key)
            if command == "submit":
                from .summary import structural_preview
                sys.stdout.write(canonical(structural_preview(result)).decode("ascii") + "\n")
            elif command == "verify-manifest":
                print(json.dumps({"verified": True, "algorithm": "HMAC-SHA256", "manifest_hash": result["manifest_hash"], "synthetic": True}, sort_keys=True))
            elif command == "report":
                emit(arguments.out, render(result, arguments.format), arguments.force, (arguments.result,))
            else:
                validate(result["snapshot"])
                detail = Analysis(result["snapshot"], result["constraint_model"], result["parameters"]["step_bound"], Fraction(result["parameters"]["threshold"])).credential(arguments.credential)
                emit(arguments.out, canonical(detail) + b"\n", arguments.force, (arguments.result,))
        elif command == "whatif":
            graph = read_graph(arguments.tenant)
            addition = json.loads(arguments.add_binding.read_text(encoding="utf-8")) if arguments.add_binding else None
            changed = validate(modify_binding(graph, remove=arguments.remove_binding, addition=addition))
            before = Analysis(graph, arguments.constraint_model, arguments.steps, Fraction(arguments.threshold)).run(False)
            after = Analysis(changed, arguments.constraint_model, arguments.steps, Fraction(arguments.threshold)).run(False)
            inputs = (arguments.tenant,) + ((arguments.add_binding,) if arguments.add_binding else ())
            emit(arguments.out, canonical(compare(before, after)) + b"\n", arguments.force, inputs)
        return 0
    except BrokenPipeError:
        return 0
    except FileExistsError:
        print("blastradius: Output already exists; choose another path or explicitly use --force.", file=sys.stderr)
        return 2
    except GraphError as error:
        print(f"blastradius: {error}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print("blastradius: Invalid input, unavailable signing key, or file operation failed. Check the synthetic contract and local paths; input values are not echoed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
