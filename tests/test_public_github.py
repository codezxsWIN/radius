from io import BytesIO
from hashlib import sha256
import json
from pathlib import Path
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from blastradius.model import GraphError, canonical
import blastradius.repository.github as github


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "repositories" / "aws-oidc-path"
COMMIT = "1" * 40


def archive(files=None, entries=None):
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as bundle:
        for name, payload in sorted((files or {}).items()):
            info = ZipInfo(name, date_time=(2026, 9, 17, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            bundle.writestr(info, payload)
        for info, payload in entries or []:
            bundle.writestr(info, payload)
    return stream.getvalue()


def fixture_archive():
    return archive({
        "acme-payments-pinned/" + path.relative_to(FIXTURE).as_posix(): path.read_bytes()
        for path in FIXTURE.rglob("*") if path.is_file()
    })


class FakeTransport:
    def __init__(self, payload=None, redirect=f"https://codeload.github.com/acme/payments/legacy.zip/{COMMIT}"):
        self.payload = payload or fixture_archive()
        self.redirect = redirect
        self.calls = []

    def __call__(self, host, path, limit):
        self.calls.append((host, path, limit))
        if host == "api.github.com" and "/commits/" in path:
            return 200, {"content-type": "application/json"}, json.dumps({"sha": COMMIT}).encode()
        if host == "api.github.com" and "/zipball/" in path:
            return 302, {"location": self.redirect}, b""
        if host == "codeload.github.com":
            return 200, {"content-type": "application/zip"}, self.payload
        raise AssertionError((host, path, limit))


@pytest.mark.parametrize("value", [
    "http://github.com/acme/payments",
    "https://evil.example/acme/payments",
    "https://user@github.com/acme/payments",
    "https://github.com:443/acme/payments",
    "https://github.com/acme/payments/issues",
    "https://github.com/acme/payments?tab=readme",
    "https://github.com/acme/payments#readme",
    "https://github.com/acme/%2e%2e",
])
def test_public_github_url_rejects_confused_authorities_and_paths(value):
    with pytest.raises(GraphError):
        github.parse_public_github_url(value)


def test_public_github_url_is_normalized():
    assert github.parse_public_github_url("https://github.com/acme/payments.git/") == (
        "acme", "payments", "https://github.com/acme/payments"
    )


def test_fixture_archive_is_independent_of_wall_clock(monkeypatch):
    first = fixture_archive()
    monkeypatch.setattr("zipfile.time.localtime", lambda *args: (2030, 1, 1, 12, 0, 0, 1, 1, -1))
    assert fixture_archive() == first


def test_public_github_analysis_pins_commit_runs_locally_and_cleans_up(monkeypatch):
    transport = FakeTransport()
    analyzed = []
    original = github.analyze_repository

    def observe(path, slug):
        analyzed.append(Path(path))
        assert analyzed[-1].is_dir()
        return original(path, slug)

    monkeypatch.setattr(github, "analyze_repository", observe)
    first = github.analyze_public_github_repository(
        "https://github.com/acme/payments.git", ref="heads/feature/test", transport=transport
    )
    second = github.analyze_public_github_repository(
        "https://github.com/acme/payments.git", ref="heads/feature/test", transport=FakeTransport()
    )

    assert canonical(first) == canonical(second)
    assert first["summary"]["finding_count"] == 1
    assert first["repository"]["input"]["kind"] == "public-github-url"
    assert first["repository"]["input"]["url"] == "https://github.com/acme/payments"
    assert first["repository"]["input"]["requested_ref"] == "heads/feature/test"
    assert first["repository"]["input"]["commit_sha"] == COMMIT
    assert len(first["repository"]["input"]["archive_sha256"]) == 64
    unsigned = {key: value for key, value in first.items() if key != "analysis_hash"}
    assert first["analysis_hash"] == sha256(canonical(unsigned)).hexdigest()
    assert any(path.endswith("/commits/heads%2Ffeature%2Ftest") for _, path, _ in transport.calls)
    assert all(not path.exists() for path in analyzed)


def test_public_review_retains_only_model_for_post_cleanup_simulation(monkeypatch):
    from blastradius.repository.scenarios import simulate_repository_review
    acquired = []
    original = github.analyze_repository

    def observe(path, slug, *, review_context=None):
        acquired.append(Path(path))
        return original(path, slug, review_context=review_context)

    monkeypatch.setattr(github, "analyze_repository", observe)
    transport = FakeTransport()
    context = {}
    result = github.analyze_public_github_repository("https://github.com/acme/payments", transport=transport, review_context=context)
    assert all(not path.exists() for path in acquired)
    assert set(context) == {"graph", "evidence_index"}
    assert all(str(path) not in canonical(context).decode("ascii") for path in acquired)
    requests_before = len(transport.calls)
    comparison = simulate_repository_review(result, context, [control["id"] for control in result["controls"]])
    assert comparison["base_analysis_hash"] == result["analysis_hash"]
    assert comparison["after"]["reachable_findings"] == 0
    assert comparison["after"]["reachable_secrets"] == 0
    assert len(transport.calls) == requests_before


def test_public_github_analysis_rejects_unapproved_redirect():
    transport = FakeTransport(redirect="https://attacker.example/archive.zip")
    with pytest.raises(GraphError, match="redirect"):
        github.analyze_public_github_repository("https://github.com/acme/payments", transport=transport)
    assert all(host != "attacker.example" for host, _, _ in transport.calls)


@pytest.mark.parametrize("name", [
    "root/../escape.txt",
    "/absolute.txt",
    "root/NUL.txt",
    "root/trailing. ",
])
def test_archive_rejects_unsafe_paths(tmp_path, name):
    with pytest.raises(GraphError):
        github.extract_public_github_archive(archive({name: b"bad"}), tmp_path / "repository")


def test_archive_path_profile_rejects_backslashes_before_platform_normalization():
    with pytest.raises(GraphError):
        github._safe_segments("root/folder\\escape.txt")


def test_archive_rejects_links_duplicates_multiple_roots_and_limits(tmp_path, monkeypatch):
    link = ZipInfo("root/link")
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(GraphError):
        github.extract_public_github_archive(archive(entries=[(link, b"target")]), tmp_path / "links")

    with pytest.raises(GraphError):
        github.extract_public_github_archive(
            archive({"root/README.md": b"a", "root/readme.md": b"b"}), tmp_path / "duplicates"
        )
    with pytest.raises(GraphError):
        github.extract_public_github_archive(
            archive({"first/a": b"a", "second/b": b"b"}), tmp_path / "roots"
        )

    monkeypatch.setattr(github, "MAX_FILE_BYTES", 4)
    extracted, report = github.extract_public_github_archive(archive({"root/large": b"12345"}), tmp_path / "large")
    assert extracted.is_dir()
    assert list(extracted.iterdir()) == []
    assert report["skipped"] == [{"path": "large", "reason": "file-too-large", "size": 5}]
