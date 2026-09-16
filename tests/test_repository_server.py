from http.client import HTTPConnection
import json
from threading import Thread

import pytest

from blastradius.repository.report import render_repository_result
from blastradius.repository.server import MAX_REQUEST_BYTES, ReviewServer


@pytest.fixture
def server():
    with ReviewServer(0) as application:
        thread = Thread(target=application.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        yield application
        application.shutdown()
        thread.join(timeout=5)


def request(server, path="/api/analyze", payload=None, headers=None, method="POST", raw=None):
    connection = HTTPConnection(*server.server_address, timeout=10)
    supplied = {"Origin": server.origin, "X-BlastRadius-Token": server.token, "Content-Type": "application/json"}
    supplied.update(headers or {})
    body = json.dumps(payload if payload is not None else {"source": "example"}) if raw is None else raw
    connection.request(method, path, body=body if method == "POST" else None, headers=supplied)
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return result


def test_server_is_loopback_only_with_protected_page(server):
    assert server.server_address[0] == "127.0.0.1"
    status, headers, document = request(server, path="/", method="GET")
    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Frame-Options"] == "DENY"
    assert b"script-src 'sha256-" in document
    assert b'"result":' not in document


@pytest.mark.parametrize("headers", [{"Origin": "https://attacker.example"}, {"Origin": "null"}, {"X-BlastRadius-Token": "wrong"}, {"Host": "attacker.example"}, {"Host": "localhost"}])
def test_cross_origin_and_rebinding_requests_do_not_analyze(server, headers):
    status, returned, _ = request(server, headers=headers)
    assert status == 403
    assert "Access-Control-Allow-Origin" not in returned
    assert server.last_result is None


def test_server_analysis_exports_and_clear_use_one_unchanged_result(server):
    status, _, body = request(server)
    assert status == 200
    result = json.loads(body)
    assert result["repository"]["is_example"] is True
    assert result["summary"]["finding_count"] == 1
    assert result["findings"][0]["remediation"]["after_absolute_reach"] == 0
    for format in ("json", "md", "sarif", "html"):
        status, headers, exported = request(server, "/api/export", {"format": format, "analysis_hash": result["analysis_hash"]})
        expected = render_repository_result(result, format)
        assert status == 200
        assert exported == (expected.encode("utf-8") if isinstance(expected, str) else expected)
        assert "attachment" in headers["Content-Disposition"]
        assert server.token.encode() not in exported
    assert request(server, "/api/export", {"format": "json", "analysis_hash": "stale"})[0] == 409
    assert request(server, "/api/clear", {})[0] == 200
    assert server.last_result is None
    assert request(server, "/api/export", {"format": "json", "analysis_hash": result["analysis_hash"]})[0] == 409


def test_local_no_proof_and_invalid_inputs(server, tmp_path):
    status, _, body = request(server, payload={"source": "local", "path": str(tmp_path), "slug": "acme/empty"})
    assert status == 200
    assert "not evidence" in json.loads(body)["conclusion"]
    assert str(tmp_path).encode() not in body
    assert request(server, payload={"source": "local", "path": "//network/share", "slug": "acme/repo"})[0] == 400
    assert request(server, payload={"source": "local", "path": str(tmp_path), "slug": []})[0] == 400
    assert request(server, payload={"source": "example", "command": "ignored-command"})[0] == 400
    assert request(server, payload={"source": "github", "url": "http://127.0.0.1/private"})[0] == 400


def test_server_rejects_large_malformed_and_concurrent_requests(server):
    assert request(server, raw=" " * (MAX_REQUEST_BYTES + 1))[0] == 413
    assert request(server, raw='{"source":"example","source":"local"}')[0] == 400
    assert request(server, headers={"Content-Type": "text/plain"})[0] == 415
    assert request(server, headers={"Transfer-Encoding": "chunked"})[0] == 400
    assert request(server, headers={"Content-Length": "9" * 5000}, raw="")[0] == 400
    with server.analysis_lock:
        assert request(server)[0] == 409
    assert server.last_result is None


def test_server_does_not_expose_file_routes_or_cross_origin_preflight(server):
    assert request(server, "/../pyproject.toml", method="GET")[0] == 404
    assert request(server, "/api/analyze", method="GET")[0] == 404
    status, headers, _ = request(server, method="OPTIONS")
    assert status == 403
    assert "Access-Control-Allow-Origin" not in headers


def test_public_input_uses_only_existing_safe_acquisition(server, monkeypatch):
    from blastradius.repository import server as implementation
    calls = []
    def capture(url, reference, *, review_context=None):
        calls.append((url, reference))
        assert isinstance(review_context, dict)
        return {"accepted": True}
    monkeypatch.setattr(implementation, "analyze_public_github_repository", capture)
    status, _, body = request(server, payload={"source": "github", "url": "https://github.com/acme/payments", "ref": "main"})
    assert status == 200
    assert calls == [("https://github.com/acme/payments", "main")]
    assert json.loads(body) == {"accepted": True}


def test_change_set_api_recomputes_and_exports_without_mutating_baseline(server):
    status, _, body = request(server)
    assert status == 200
    result = json.loads(body)
    selected = [result["controls"][0]["id"]]
    payload = {"analysis_hash": result["analysis_hash"], "controls": selected}
    status, _, response = request(server, "/api/simulate", payload)
    assert status == 200
    comparison = json.loads(response)
    assert comparison["blocked_findings"] == 1
    assert comparison["after"]["reachable_secrets"] == 0
    assert server.last_result == result
    for format in ("md", "json"):
        status, headers, exported = request(server, "/api/export-plan", {**payload, "format": format})
        assert status == 200
        assert "attachment" in headers["Content-Disposition"]
        assert b"simulation" in exported
        assert server.token.encode() not in exported
    assert request(server, "/api/simulate", {**payload, "controls": ["not-a-control"]})[0] == 400
    assert request(server, "/api/simulate", {**payload, "analysis_hash": "old"})[0] == 409
    assert request(server, "/api/clear", {})[0] == 200
    assert server.review_context == {}
    assert request(server, "/api/simulate", payload)[0] == 409


def test_shared_example_has_real_alternate_and_cross_job_paths(server):
    status, _, body = request(server, payload={"source": "example", "example": "shared"})
    assert status == 200
    result = json.loads(body)
    assert result["repository"]["is_example"] is True
    assert result["summary"] == {"finding_count": 5, "declared_reachable_secrets": 3}
    assert len(result["controls"]) == 3
    production = [control["id"] for control in result["controls"] if control["role_name"] == "github-production"]
    def compare(controls):
        status, _, body = request(server, "/api/simulate", {"analysis_hash": result["analysis_hash"], "controls": controls})
        assert status == 200
        return json.loads(body)
    assert compare(production[:1])["blocked_findings"] == 0
    full = compare(production)
    assert full["blocked_findings"] == 4
    assert full["after"] == {"reachable_findings": 1, "reachable_secrets": 1, "reachable_jobs": 1}
    assert compare([control["id"] for control in result["controls"]])["blocked_findings"] == 5


def test_cancellation_is_guarded_and_never_publishes_partial_analysis(server, monkeypatch):
    from threading import Event
    from blastradius.repository import server as implementation
    from blastradius.repository.operation import checkpoint
    started, release = Event(), Event()
    responses = []

    def controlled(payload, review_context=None):
        checkpoint("Parsing source declarations")
        started.set()
        assert release.wait(5)
        checkpoint("Completing analysis")
        return {"partial": True}

    monkeypatch.setattr(implementation, "_analyze", controlled)
    thread = Thread(target=lambda: responses.append(request(server, payload={"source": "example", "operation_id": "abc123"})))
    thread.start()
    try:
        assert started.wait(5)
        status, _, body = request(server, "/api/status", {"operation_id": "abc123"})
        assert status == 200 and json.loads(body)["stage"] == "Parsing source declarations"
        assert request(server, "/api/cancel", {"operation_id": "stale"})[0] == 409
        assert request(server, "/api/cancel", {"operation_id": "abc123"})[0] == 202
    finally:
        release.set()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert responses[0][0] == 409
    assert json.loads(responses[0][2])["cancelled"] is True
    assert server.last_result is None and server.review_context == {}


def test_analysis_deadline_fails_closed():
    from blastradius.repository.operation import AnalysisCancelled, AnalysisOperation, checkpoint, operation_scope
    with operation_scope(AnalysisOperation("deadline", seconds=0)):
        with pytest.raises(AnalysisCancelled, match="deadline"):
            checkpoint("Starting")