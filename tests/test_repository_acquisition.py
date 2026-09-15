from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess

import pytest

from blastradius.model import GraphError, canonical
from blastradius.repository import acquire_repository
from blastradius.repository import acquisition


def test_basic_manifest_is_deterministic_and_does_not_expose_root(tmp_path):
    root = tmp_path / "example repository"
    root.mkdir()
    (root / "z-last.txt").write_text("last\n", encoding="utf-8")
    workflow = root / ".github" / "workflows"
    workflow.mkdir(parents=True)
    payload = b"name: deploy\r\n"
    (workflow / "deploy.yml").write_bytes(payload)

    first = acquire_repository(root)
    second = acquire_repository(root)

    assert canonical(first) == canonical(second)
    assert first["format_version"] == "0.1"
    assert first["profile"] == "safe-local-v0.1"
    assert first["source"] == {"kind": "local-directory", "name": root.name}
    assert [item["path"] for item in first["files"]] == [
        ".github/workflows/deploy.yml",
        "z-last.txt",
    ]
    assert first["files"][0] == {
        "path": ".github/workflows/deploy.yml",
        "size": len(payload),
        "sha256": sha256(payload).hexdigest(),
    }
    assert first["summary"] == {"file_count": 2, "total_bytes": 20, "skipped_count": 0}
    unsigned = {key: value for key, value in first.items() if key != "snapshot_hash"}
    assert first["snapshot_hash"] == sha256(canonical(unsigned)).hexdigest()
    assert str(root.resolve()) not in json.dumps(first)


def test_empty_and_unicode_repositories_are_supported(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    manifest = acquire_repository(empty)
    assert manifest["files"] == []
    assert manifest["summary"] == {"file_count": 0, "total_bytes": 0, "skipped_count": 0}

    root = tmp_path / "unicode"
    nested = root / "文档 with spaces"
    nested.mkdir(parents=True)
    (nested / "déploy.yml").write_text("ok", encoding="utf-8")
    assert acquire_repository(root)["files"][0]["path"] == "文档 with spaces/déploy.yml"


def test_excluded_directories_and_oversized_files_are_reported(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "keep.txt").write_bytes(b"keep")
    generated = root / "node_modules"
    generated.mkdir()
    (generated / "do-not-read.js").write_text("raise danger", encoding="utf-8")
    (root / "large.bin").write_bytes(b"12345")
    monkeypatch.setattr(acquisition, "MAX_FILE_BYTES", 4)

    manifest = acquire_repository(root)

    assert [item["path"] for item in manifest["files"]] == ["keep.txt"]
    assert manifest["skipped"] == [
        {"path": "large.bin", "kind": "file", "reason": "file-too-large", "size": 5},
        {"path": "node_modules", "kind": "directory", "reason": "excluded-directory"},
    ]
    assert manifest["summary"]["skipped_count"] == 2


def test_file_count_and_total_bytes_fail_closed(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.txt").write_bytes(b"aa")
    (root / "b.txt").write_bytes(b"bb")

    monkeypatch.setattr(acquisition, "MAX_FILES", 1)
    with pytest.raises(GraphError, match="file-count limit"):
        acquire_repository(root)

    monkeypatch.setattr(acquisition, "MAX_FILES", 10)
    monkeypatch.setattr(acquisition, "MAX_TOTAL_BYTES", 3)
    with pytest.raises(GraphError, match="total-byte limit"):
        acquire_repository(root)


def test_path_length_and_depth_fail_without_echoing_absolute_root(tmp_path, monkeypatch):
    root = tmp_path / "private-root"
    nested = root / "one" / "two"
    nested.mkdir(parents=True)
    (nested / "value.txt").write_text("value", encoding="utf-8")

    monkeypatch.setattr(acquisition, "MAX_DEPTH", 1)
    with pytest.raises(GraphError) as depth:
        acquire_repository(root)
    assert str(root.resolve()) not in str(depth.value)

    monkeypatch.setattr(acquisition, "MAX_DEPTH", 40)
    monkeypatch.setattr(acquisition, "MAX_PATH_CHARACTERS", 4)
    with pytest.raises(GraphError) as length:
        acquire_repository(root)
    assert str(root.resolve()) not in str(length.value)


def test_symlink_is_not_read_or_followed(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("must-not-appear", encoding="utf-8")
    link = root / "linked-secret.txt"
    try:
        link.symlink_to(secret)
    except (NotImplementedError, OSError):
        pytest.skip("This environment cannot create file symlinks.")

    manifest = acquire_repository(root)

    assert manifest["files"] == []
    assert manifest["skipped"] == [
        {"path": "linked-secret.txt", "kind": "link", "reason": "link-not-followed"}
    ]
    assert "must-not-appear" not in json.dumps(manifest)
    assert str(secret) not in json.dumps(manifest)


def test_link_like_entry_is_skipped_before_file_read(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "link-like.txt").write_text("do-not-read", encoding="utf-8")

    monkeypatch.setattr(acquisition, "_link_or_reparse", lambda entry: True)

    def forbidden(*args, **kwargs):
        raise AssertionError("Link-like entries must not be opened.")

    monkeypatch.setattr(acquisition, "_hash_regular_file", forbidden)
    manifest = acquire_repository(root)
    assert manifest["files"] == []
    assert manifest["skipped"] == [
        {"path": "link-like.txt", "kind": "link", "reason": "link-not-followed"}
    ]


def test_missing_or_nondirectory_root_has_controlled_error(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(GraphError, match="existing local directory") as error:
        acquire_repository(missing)
    assert str(missing) not in str(error.value)

    regular = tmp_path / "regular.txt"
    regular.write_text("x", encoding="utf-8")
    with pytest.raises(GraphError, match="existing local directory") as error:
        acquire_repository(regular)
    assert str(regular) not in str(error.value)


def test_acquisition_does_not_execute_target_or_use_network(tmp_path, monkeypatch):
    root = tmp_path / "untrusted"
    root.mkdir()
    marker = tmp_path / "executed"
    (root / "setup.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Repository acquisition cannot use subprocesses or the network.")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    manifest = acquire_repository(root)
    assert manifest["files"][0]["path"] == "setup.py"
    assert not marker.exists()
