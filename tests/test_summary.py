from contextlib import redirect_stdout
from io import StringIO
import json
import secrets

import pytest

from blastradius.analysis import Analysis
from blastradius.cli import main
from blastradius.model import GraphError, canonical
from blastradius.signing import sign
from blastradius.summary import structural_preview
from blastradius.synthetic import fixture


def test_structural_preview_has_no_identifiers_or_false_anonymity_claim():
    result = Analysis(fixture("secret")).run()
    preview = structural_preview(result)
    encoded = canonical(preview).decode()
    assert "credential-alpha" not in encoded
    assert "Fictional" not in encoded
    assert result["snapshot_hash"] not in encoded
    assert preview["anonymous"] is False
    assert preview["submission_enabled"] is False
    assert sum(bucket["count"] for bucket in preview["canonical_radius_histogram"]) == 2
    with pytest.raises(GraphError): structural_preview({"synthetic": False})


def test_submit_is_verified_dry_run_only_and_never_connects(tmp_path, monkeypatch):
    key = secrets.token_bytes(32)
    key_path = tmp_path / "external.key"
    key_path.write_bytes(key)
    result_path = tmp_path / "result.json"
    result_path.write_bytes(canonical(sign(Analysis(fixture("direct")).run(), key)))
    def forbidden(*args, **kwargs): raise AssertionError("No submission network operation is permitted")
    monkeypatch.setattr("socket.socket", forbidden)
    output = StringIO()
    with redirect_stdout(output):
        assert main(["submit", str(result_path), "--dry-run", "--signing-key", str(key_path)]) == 0
    assert json.loads(output.getvalue())["submission_enabled"] is False
    with pytest.raises(SystemExit): main(["submit", str(result_path)])
