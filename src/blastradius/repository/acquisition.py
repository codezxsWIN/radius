"""Bounded, deterministic inventory of an untrusted local repository."""

from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import stat

from ..model import GraphError, canonical


PROFILE = "safe-local-v0.1"
MAX_FILES = 10_000
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_PATH_CHARACTERS = 1_024
MAX_DEPTH = 40
HASH_CHUNK_BYTES = 64 * 1024
EXCLUDED_DIRECTORIES = frozenset({
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
})
EXCLUDED_DIRECTORY_KEYS = frozenset(value.casefold() for value in EXCLUDED_DIRECTORIES)


def _normalized_relative(root, path):
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise GraphError("A repository entry escaped the selected root.") from None
    value = relative.as_posix()
    if not value or value == "." or len(value) > MAX_PATH_CHARACTERS:
        raise GraphError("A repository entry exceeds the safe path profile.")
    if len(relative.parts) > MAX_DEPTH:
        raise GraphError("A repository entry exceeds the safe depth profile.")
    return value


def _path_key(relative):
    return relative.casefold() if os.name == "nt" else relative


def _excluded(name):
    return name.casefold() in EXCLUDED_DIRECTORY_KEYS if os.name == "nt" else name in EXCLUDED_DIRECTORIES


def _link_or_reparse(entry):
    try:
        if entry.is_symlink():
            return True
        metadata = entry.stat(follow_symlinks=False)
    except OSError:
        raise GraphError("A repository entry could not be inspected safely.") from None
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _hash_regular_file(path, expected_size):
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    digest = sha256()
    total = 0
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise GraphError("A repository entry changed type during acquisition.")
            attributes = getattr(metadata, "st_file_attributes", 0)
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if reparse_flag and attributes & reparse_flag:
                raise GraphError("A repository entry changed type during acquisition.")
            while chunk := stream.read(HASH_CHUNK_BYTES):
                total += len(chunk)
                if total > expected_size or total > MAX_FILE_BYTES:
                    raise GraphError("A repository file changed during acquisition.")
                digest.update(chunk)
    except GraphError:
        raise
    except OSError:
        raise GraphError("A repository file could not be read safely.") from None
    if total != expected_size:
        raise GraphError("A repository file changed during acquisition.")
    return digest.hexdigest()


def read_snapshot_file(root: Path, record: dict) -> bytes:
    """Read one manifest-listed file after containment, type, size and hash checks."""
    if not isinstance(record, dict) or set(record) != {"path", "size", "sha256"}:
        raise GraphError("Repository manifest contains an invalid file record.")
    relative, expected_size, expected_hash = record["path"], record["size"], record["sha256"]
    if (not isinstance(relative, str) or "\\" in relative or not isinstance(expected_size, int)
            or expected_size < 0 or expected_size > MAX_FILE_BYTES or not isinstance(expected_hash, str)
            or len(expected_hash) != 64 or any(character not in "0123456789abcdef" for character in expected_hash)):
        raise GraphError("Repository manifest contains an invalid file record.")
    logical = PurePosixPath(relative)
    if logical.is_absolute() or not logical.parts or any(part in {"", ".", ".."} for part in logical.parts):
        raise GraphError("Repository manifest contains an unsafe relative path.")
    try:
        source = Path(root).resolve(strict=True)
        if not source.is_dir():
            raise OSError
    except (OSError, RuntimeError):
        raise GraphError("Repository input must be an existing local directory.") from None
    current = source
    try:
        for index, part in enumerate(logical.parts):
            current = current / part
            metadata = os.lstat(current)
            attributes = getattr(metadata, "st_file_attributes", 0)
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if stat.S_ISLNK(metadata.st_mode) or reparse_flag and attributes & reparse_flag:
                raise GraphError("Repository snapshot changed since acquisition.")
            if index < len(logical.parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
                raise GraphError("Repository snapshot changed since acquisition.")
            if index == len(logical.parts) - 1 and not stat.S_ISREG(metadata.st_mode):
                raise GraphError("Repository snapshot changed since acquisition.")
    except GraphError:
        raise
    except OSError:
        raise GraphError("Repository snapshot changed since acquisition.") from None

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(current, flags)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            attributes = getattr(metadata, "st_file_attributes", 0)
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_size != expected_size
                    or reparse_flag and attributes & reparse_flag):
                raise GraphError("Repository snapshot changed since acquisition.")
            payload = stream.read(expected_size + 1)
    except GraphError:
        raise
    except OSError:
        raise GraphError("Repository snapshot changed since acquisition.") from None
    if len(payload) != expected_size or sha256(payload).hexdigest() != expected_hash:
        raise GraphError("Repository snapshot changed since acquisition.")
    return payload


def acquire_repository(root: Path) -> dict:
    """Return a deterministic safe-local-v0.1 repository manifest."""
    try:
        source = Path(root).resolve(strict=True)
        if not source.is_dir():
            raise GraphError("Repository input must be an existing local directory.")
    except GraphError:
        raise
    except (OSError, RuntimeError):
        raise GraphError("Repository input must be an existing local directory.") from None

    files = []
    skipped = []
    seen_paths = set()
    encountered_files = 0
    total_bytes = 0

    def register(relative):
        key = _path_key(relative)
        if key in seen_paths:
            raise GraphError("Repository paths collide under the safe path profile.")
        seen_paths.add(key)

    def visit(directory):
        nonlocal encountered_files, total_bytes
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError:
            raise GraphError("A repository directory could not be read safely.") from None
        for entry in entries:
            path = Path(entry.path)
            relative = _normalized_relative(source, path)
            register(relative)
            if _link_or_reparse(entry):
                skipped.append({"path": relative, "kind": "link", "reason": "link-not-followed"})
                continue
            try:
                is_directory = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError:
                raise GraphError("A repository entry could not be inspected safely.") from None
            if is_directory:
                if _excluded(entry.name):
                    skipped.append({"path": relative, "kind": "directory", "reason": "excluded-directory"})
                else:
                    visit(path)
                continue
            if not is_file:
                skipped.append({"path": relative, "kind": "other", "reason": "unsupported-entry"})
                continue
            encountered_files += 1
            if encountered_files > MAX_FILES:
                raise GraphError("Repository exceeds the safe file-count limit.")
            try:
                size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                raise GraphError("A repository entry could not be inspected safely.") from None
            if size > MAX_FILE_BYTES:
                skipped.append({"path": relative, "kind": "file", "reason": "file-too-large", "size": size})
                continue
            if total_bytes + size > MAX_TOTAL_BYTES:
                raise GraphError("Repository exceeds the safe total-byte limit.")
            record = {"path": relative, "size": size, "sha256": _hash_regular_file(path, size)}
            files.append(record)
            total_bytes += size

    visit(source)
    files.sort(key=lambda item: item["path"])
    skipped.sort(key=lambda item: item["path"])
    manifest = {
        "format_version": "0.1",
        "profile": PROFILE,
        "source": {"kind": "local-directory", "name": source.name},
        "limits": {
            "max_files": MAX_FILES,
            "max_file_bytes": MAX_FILE_BYTES,
            "max_total_bytes": MAX_TOTAL_BYTES,
            "max_path_characters": MAX_PATH_CHARACTERS,
            "max_depth": MAX_DEPTH,
        },
        "files": files,
        "skipped": skipped,
        "summary": {"file_count": len(files), "total_bytes": total_bytes, "skipped_count": len(skipped)},
    }
    manifest["snapshot_hash"] = sha256(canonical(manifest)).hexdigest()
    return manifest
