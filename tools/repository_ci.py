"""Run an installed trusted analyzer against a separate untrusted checkout."""

import argparse
from hashlib import sha256
from pathlib import Path
import re
import sys

from blastradius import __version__
from blastradius.cli import emit, reject_internal_output
from blastradius.model import GraphError, canonical
from blastradius.repository import analyze_repository, render_repository_result


FORMATS = ("json", "md", "sarif", "html")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--repository-slug", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--analyzer-ref")
    parser.add_argument("--target-ref")
    parser.add_argument("--fail-on-findings", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        for revision in (arguments.analyzer_ref, arguments.target_ref):
            if revision is not None and re.fullmatch(r"[a-fA-F0-9]{40}", revision) is None:
                raise GraphError("Revision identifiers must be full Git commit hashes.")
        repository = arguments.repository.resolve(strict=True)
        destination = arguments.out.resolve()
        reject_internal_output(repository, destination)
        outputs = [destination / f"analysis.{format}" for format in FORMATS] + [destination / "context.json"]
        if any(output.exists() for output in outputs):
            raise GraphError("Review output already exists; choose a fresh output directory.")
        result = analyze_repository(repository, arguments.repository_slug)
        checksums = {}
        for format in FORMATS:
            payload = render_repository_result(result, format)
            encoded = payload.encode("utf-8") if isinstance(payload, str) else payload
            filename = f"analysis.{format}"
            emit(destination / filename, encoded)
            checksums[filename] = sha256(encoded).hexdigest()
        context = {
            "analyzer_version": __version__, "analyzer_revision": arguments.analyzer_ref,
            "target_revision": arguments.target_ref, "logical_repository": arguments.repository_slug,
            "analysis_hash": result["analysis_hash"], "report_sha256": checksums,
            "source_executed": False, "deployed_aws_state": "unverified",
            "scope": "Declared branch-based GitHub OIDC configuration at this source revision, not proof of pull-request execution or deployed access.",
            "completion_is_not_security_assurance": True,
        }
        emit(destination / "context.json", canonical(context) + b"\n")
        print(f"Review completed: {result['summary']['finding_count']} declared path(s), {len(result['diagnostics'])} diagnostic(s). Deployment remains unverified.")
        return 1 if arguments.fail_on_findings and result["findings"] else 0
    except (GraphError, OSError, ValueError) as failure:
        message = str(failure) if isinstance(failure, GraphError) else "A local source or report file could not be accessed."
        print("Repository review failed: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())