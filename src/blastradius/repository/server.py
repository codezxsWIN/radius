"""Loopback-only, non-executing repository review service."""

from hashlib import sha256
from hmac import compare_digest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
import secrets
import threading
import webbrowser

from ..model import GraphError, canonical, read_json
from .findings import analyze_repository
from .github import analyze_public_github_repository
from .report import render_repository_result
from .scenarios import simulate_repository_review, render_change_request
from .view import ASSETS, render_repository_workbench


MAX_REQUEST_BYTES = 8192
FORMATS = {"json": "application/json", "sarif": "application/sarif+json", "md": "text/markdown", "html": "text/html"}


def _analyze(payload, review_context=None):
    source = payload.get("source")
    options = {"review_context": review_context} if review_context is not None else {}
    if source == "example" and set(payload) <= {"source", "example"}:
        examples = {"single": ("repository-example", "acme/payments"), "shared": ("repository-shared-example", "acme/release-platform")}
        example = payload.get("example", "single")
        if not isinstance(example, str) or example not in examples:
            raise GraphError("Choose a known bundled example.")
        directory, slug = examples[example]
        result = analyze_repository(ASSETS / directory, slug, **options)
        result["repository"]["is_example"] = True
        result["analysis_hash"] = sha256(canonical({key: value for key, value in result.items() if key != "analysis_hash"})).hexdigest()
        return result
    if source == "local" and set(payload) == {"source", "path", "slug"}:
        path, slug = payload["path"], payload["slug"]
        if (not isinstance(path, str) or not isinstance(slug, str) or not path.strip()
                or path.startswith(("\\\\", "//")) or len(path) > 4096 or len(slug) > 201
                or any(ord(character) < 32 for character in path)):
            raise GraphError("Choose a local directory and an owner/repository slug; network paths are not supported.")
        return analyze_repository(Path(path).expanduser(), slug, **options)
    if source == "github" and set(payload) <= {"source", "url", "ref"} and "url" in payload:
        url, reference = payload["url"], payload.get("ref")
        if not isinstance(url, str) or len(url) > 2048 or (reference is not None and (not isinstance(reference, str) or len(reference) > 1024)):
            raise GraphError("A public GitHub URL and an optional literal ref are required.")
        return analyze_public_github_repository(url, reference, **options)
    raise GraphError("Unsupported repository request.")


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, port=8765):
        if type(port) is not int or not 0 <= port <= 65535:
            raise GraphError("Review port must be between 0 and 65535.")
        self.token = secrets.token_urlsafe(32)
        self.analysis_lock = threading.Lock()
        self.last_result = None
        self.review_context = {}
        super().__init__(("127.0.0.1", port), ReviewHandler)
        self.origin = f"http://127.0.0.1:{self.server_address[1]}"
        self.authority = f"127.0.0.1:{self.server_address[1]}"

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address


class ReviewHandler(BaseHTTPRequestHandler):
    server: ReviewServer
    server_version = "BlastRadiusReview"
    sys_version = ""

    def log_message(self, format, *args):
        pass

    def _respond(self, status, body, content_type="application/json", filename=None):
        encoded = canonical(body) if isinstance(body, dict) else body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Connection", "close")
        if filename is not None:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def _valid_host(self):
        return self.headers.get_all("Host", []) == [self.server.authority]

    def do_GET(self):
        if not self._valid_host():
            self._respond(403, {"error": "Invalid local host."})
        elif self.path != "/":
            self._respond(404, {"error": "Route not found."})
        else:
            self._respond(200, render_repository_workbench(self.server.token), "text/html")

    def do_OPTIONS(self):
        self._respond(403, {"error": "Cross-origin requests are not supported."})

    def do_POST(self):
        supplied_token = self.headers.get("X-BlastRadius-Token", "")
        if (not self._valid_host() or self.headers.get_all("Origin", []) != [self.server.origin]
                or not supplied_token.isascii() or not compare_digest(supplied_token, self.server.token)):
            self._respond(403, {"error": "This request does not belong to the local review session."})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if (self.headers.get("Transfer-Encoding") is not None or len(lengths) != 1
            or len(lengths[0]) > 8 or not lengths[0].isascii() or not lengths[0].isdigit()):
            self._respond(400, {"error": "A single bounded request body is required."})
            return
        length = int(lengths[0])
        if length > MAX_REQUEST_BYTES:
            self._respond(413, {"error": "Request exceeds the 8 KiB limit."})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            self._respond(415, {"error": "Only JSON requests are accepted."})
            return
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise GraphError("Incomplete request body.")
            payload = read_json(StringIO(raw.decode("utf-8")))
            if not isinstance(payload, dict):
                raise GraphError("Request must be a JSON object.")
        except (GraphError, UnicodeError, ValueError, TimeoutError, RecursionError):
            self._respond(400, {"error": "Invalid JSON request."})
            return
        if not self.server.analysis_lock.acquire(blocking=False):
            self._respond(409, {"error": "An analysis or export is already in progress."})
            return
        try:
            if self.path == "/api/analyze":
                self.server.last_result = None
                self.server.review_context.clear()
                result = _analyze(payload, self.server.review_context)
                self.server.last_result = result
                self._respond(200, result)
            elif self.path in {"/api/simulate", "/api/export-plan"}:
                keys = {"analysis_hash", "controls"} | ({"format"} if self.path == "/api/export-plan" else set())
                if set(payload) != keys:
                    raise GraphError("Select trust controls from the current analysis.")
                result = self.server.last_result
                if result is None or result["analysis_hash"] != payload["analysis_hash"]:
                    self._respond(409, {"error": "The baseline changed or was cleared. Analyze the repository again."})
                else:
                    comparison = simulate_repository_review(result, self.server.review_context, payload["controls"])
                    if self.path == "/api/simulate":
                        self._respond(200, comparison)
                    elif payload["format"] == "json":
                        self._respond(200, canonical(comparison) + b"\n", "application/json", "blast-radius-change-request.json")
                    elif payload["format"] == "md":
                        self._respond(200, render_change_request(comparison), "text/markdown", "blast-radius-change-request.md")
                    else:
                        raise GraphError("Change requests support Markdown or JSON.")
            elif self.path == "/api/export":
                if set(payload) != {"format", "analysis_hash"} or not isinstance(payload["format"], str) or payload["format"] not in FORMATS:
                    raise GraphError("Unsupported report export request.")
                result = self.server.last_result
                if result is None or payload["analysis_hash"] != result["analysis_hash"]:
                    self._respond(409, {"error": "The analysis changed or was cleared. Run the analysis again before exporting."})
                else:
                    format = payload["format"]
                    self._respond(200, render_repository_result(result, format), FORMATS[format], "blast-radius-report." + format)
            elif self.path == "/api/clear" and not payload:
                self.server.last_result = None
                self.server.review_context.clear()
                self._respond(200, {"cleared": True})
            else:
                self._respond(404, {"error": "Route not found."})
        except GraphError as failure:
            self._respond(400, {"error": str(failure)})
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            self._respond(400, {"error": "Input could not be analyzed. Check the supported source profile and local paths."})
        finally:
            self.server.analysis_lock.release()


def serve_review(port=8765, open_browser=True):
    with ReviewServer(port) as server:
        print(f"Blast Radius repository review: {server.origin}/", flush=True)
        print("Loopback only. Source is not executed. Press Ctrl+C to stop.", flush=True)
        if open_browser:
            webbrowser.open(server.origin + "/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass