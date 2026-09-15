"""Bounded public GitHub archive acquisition without Git or repository execution."""

from hashlib import sha256
import http.client
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
import re
import stat
from urllib.parse import quote, urlsplit
from zipfile import BadZipFile, LargeZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile

from ..model import GraphError, canonical
from .acquisition import MAX_DEPTH, MAX_FILE_BYTES, MAX_FILES, MAX_PATH_CHARACTERS, MAX_TOTAL_BYTES
from .evidence import SLUG
from .findings import analyze_repository


MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_API_BYTES = 1024 * 1024
MAX_ARCHIVE_ENTRIES = MAX_FILES * 2
DOWNLOAD_CHUNK_BYTES = 64 * 1024
TIMEOUT_SECONDS = 20
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_COMPRESSION = frozenset({ZIP_STORED, ZIP_DEFLATED})
WINDOWS_RESERVED = frozenset({"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))})


def parse_public_github_url(value: str) -> tuple[str, str, str]:
    """Return owner, repository and canonical URL for the strict public profile."""
    if not isinstance(value, str) or len(value) > 500:
        raise GraphError("GitHub input must be a supported public repository URL.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise GraphError("GitHub input must be a supported public repository URL.") from None
    if (parsed.scheme != "https" or parsed.hostname != "github.com" or port is not None
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        raise GraphError("GitHub input must be an HTTPS github.com repository URL without credentials, ports, query or fragment.")
    parts = parsed.path.split("/")
    if parts and parts[-1] == "":
        parts.pop()
    if len(parts) != 3 or parts[0] != "" or not parts[1] or not parts[2]:
        raise GraphError("GitHub URL must contain exactly owner/repository.")
    owner, repository = parts[1], parts[2]
    if repository.endswith(".git"):
        repository = repository[:-4]
    slug = f"{owner}/{repository}"
    if not repository or not SLUG.fullmatch(slug):
        raise GraphError("GitHub URL contains an unsupported owner or repository name.")
    return owner, repository, f"https://github.com/{slug}"


def _validate_ref(ref):
    if ref is None:
        return "HEAD"
    if (not isinstance(ref, str) or not ref or ref != ref.strip() or len(ref) > 255
            or "\\" in ref or any(ord(character) < 32 or ord(character) == 127 for character in ref)):
        raise GraphError("GitHub ref is invalid or exceeds the supported profile.")
    return ref


def _https_transport(host, path, limit):
    connection = http.client.HTTPSConnection(host, timeout=TIMEOUT_SECONDS)
    headers = {
        "Accept": "application/vnd.github+json",
        "Accept-Encoding": "identity",
        "User-Agent": "blastradius-public-repository-v0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        declared = response.getheader("Content-Length")
        if declared is not None:
            try:
                if int(declared) > limit:
                    raise GraphError("GitHub response exceeds the bounded download profile.")
            except ValueError:
                raise GraphError("GitHub returned an invalid response length.") from None
        payload = response.read(limit + 1)
        if len(payload) > limit:
            raise GraphError("GitHub response exceeds the bounded download profile.")
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        return response.status, response_headers, payload
    except GraphError:
        raise
    except (OSError, http.client.HTTPException):
        raise GraphError("GitHub could not be reached within the public repository profile.") from None
    finally:
        connection.close()


def _request(transport, host, path, limit, expected_status):
    try:
        status, headers, payload = transport(host, path, limit)
    except GraphError:
        raise
    except Exception:
        raise GraphError("GitHub transport failed within the public repository profile.") from None
    if type(status) is not int or not isinstance(headers, dict) or not isinstance(payload, bytes):
        raise GraphError("GitHub transport returned an invalid response.")
    if len(payload) > limit:
        raise GraphError("GitHub response exceeds the bounded download profile.")
    normalized_headers = {str(key).lower(): str(value) for key, value in headers.items()}
    if status != expected_status:
        if status in {401, 403, 429}:
            raise GraphError("GitHub rejected the unauthenticated request or its public rate limit was exceeded.")
        if status == 404:
            raise GraphError("GitHub repository or ref was not found in the public profile.")
        raise GraphError("GitHub returned an unsupported response status.")
    return normalized_headers, payload


def _commit_sha(payload):
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise GraphError("GitHub commit metadata is malformed.") from None
    value = document.get("sha") if isinstance(document, dict) else None
    if not isinstance(value, str) or not COMMIT_SHA.fullmatch(value):
        raise GraphError("GitHub commit metadata has no supported immutable SHA.")
    return value


def _archive_redirect(value, owner, repository, commit_sha):
    if not isinstance(value, str) or len(value) > 2_048:
        raise GraphError("GitHub archive redirect is missing or invalid.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise GraphError("GitHub archive redirect is missing or invalid.") from None
    if (parsed.scheme != "https" or parsed.hostname != "codeload.github.com" or port is not None
            or parsed.username is not None or parsed.password is not None or parsed.fragment):
        raise GraphError("GitHub archive redirect left the approved codeload host.")
    path_parts = [part for part in parsed.path.split("/") if part]
    if (len(path_parts) < 4 or path_parts[0].casefold() != owner.casefold()
            or path_parts[1].casefold() != repository.casefold() or path_parts[-1] != commit_sha):
        raise GraphError("GitHub archive redirect does not match the pinned repository commit.")
    return parsed.path + (("?" + parsed.query) if parsed.query else "")


def _safe_segments(name):
    if (not isinstance(name, str) or not name or "\x00" in name or "\\" in name
            or name.startswith("/") or any(ord(character) < 32 or ord(character) == 127 for character in name)):
        raise GraphError("GitHub archive contains an unsafe path.")
    parts = name.split("/")
    if parts[-1] == "":
        parts.pop()
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise GraphError("GitHub archive contains an unsafe path.")
    for part in parts:
        if ":" in part or part.endswith((".", " ")) or part.split(".", 1)[0].upper() in WINDOWS_RESERVED:
            raise GraphError("GitHub archive contains a path unsupported on safe target filesystems.")
    return parts


def extract_public_github_archive(payload: bytes, destination: Path) -> Path:
    """Validate and stream-extract one bounded GitHub source ZIP."""
    if not isinstance(payload, bytes) or len(payload) > MAX_ARCHIVE_BYTES:
        raise GraphError("GitHub archive exceeds the bounded compressed-size profile.")
    target = Path(destination)
    if target.exists():
        raise GraphError("GitHub archive extraction target must not already exist.")
    try:
        with ZipFile(BytesIO(payload)) as bundle:
            if len(bundle.infolist()) > MAX_ARCHIVE_ENTRIES:
                raise GraphError("GitHub archive exceeds the safe entry-count limit.")
            records = []
            skipped = []
            root_name = None
            path_types = {}
            file_count = 0
            total_size = 0
            for info in bundle.infolist():
                parts = _safe_segments(info.filename)
                if root_name is None:
                    root_name = parts[0]
                elif parts[0] != root_name:
                    raise GraphError("GitHub archive contains multiple top-level roots.")
                relative_parts = parts[1:]
                if not relative_parts:
                    if not info.is_dir():
                        raise GraphError("GitHub archive root must be a directory.")
                    continue
                relative = PurePosixPath(*relative_parts).as_posix()
                if len(relative) > MAX_PATH_CHARACTERS or len(relative_parts) > MAX_DEPTH:
                    raise GraphError("GitHub archive contains a path outside acquisition limits.")
                key = relative.casefold()
                if key in path_types:
                    raise GraphError("GitHub archive contains duplicate or case-colliding paths.")
                mode_type = stat.S_IFMT(info.external_attr >> 16)
                is_directory = info.is_dir()
                expected_type = stat.S_IFDIR if is_directory else stat.S_IFREG
                if mode_type not in {0, expected_type}:
                    raise GraphError("GitHub archive contains a link or unsupported entry type.")
                if info.flag_bits & 1:
                    raise GraphError("Encrypted GitHub archive entries are unsupported.")
                if info.compress_type not in ALLOWED_COMPRESSION:
                    raise GraphError("GitHub archive uses unsupported compression.")
                if not is_directory:
                    file_count += 1
                    if file_count > MAX_FILES:
                        raise GraphError("GitHub archive exceeds the safe file-count limit.")
                    if info.file_size > MAX_FILE_BYTES:
                        skipped.append({"path": relative, "reason": "file-too-large", "size": info.file_size})
                        continue
                    total_size += info.file_size
                    if total_size > MAX_TOTAL_BYTES:
                        raise GraphError("GitHub archive exceeds the safe total-byte limit.")
                    if info.file_size > 1024 * 1024 and info.file_size > max(1, info.compress_size) * 200:
                        raise GraphError("GitHub archive contains an excessive compression ratio.")
                path_types[key] = "directory" if is_directory else "file"
                records.append((relative_parts, info, is_directory))
            if root_name is None:
                raise GraphError("GitHub archive is empty.")

            for parts, _, _ in records:
                for index in range(1, len(parts)):
                    parent = PurePosixPath(*parts[:index]).as_posix().casefold()
                    if path_types.get(parent) == "file":
                        raise GraphError("GitHub archive path structure conflicts with a file.")

            target.mkdir(parents=True)
            extracted_total = 0
            for parts, info, is_directory in sorted(records, key=lambda item: (len(item[0]), tuple(part.casefold() for part in item[0]))):
                output = target.joinpath(*parts)
                if is_directory:
                    output.mkdir(parents=True, exist_ok=True)
                    continue
                output.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with bundle.open(info, "r") as source, output.open("xb") as stream:
                    while chunk := source.read(DOWNLOAD_CHUNK_BYTES):
                        written += len(chunk)
                        extracted_total += len(chunk)
                        if written > info.file_size or written > MAX_FILE_BYTES or extracted_total > MAX_TOTAL_BYTES:
                            raise GraphError("GitHub archive expanded beyond its declared safe limits.")
                        stream.write(chunk)
                if written != info.file_size:
                    raise GraphError("GitHub archive entry size did not match its declaration.")
    except GraphError:
        raise
    except (BadZipFile, LargeZipFile, RuntimeError, OSError, EOFError):
        raise GraphError("GitHub archive is malformed or could not be extracted safely.") from None
    return target, {
        "entry_count": len(records) + len(skipped),
        "extracted_file_count": sum(not is_directory for _, _, is_directory in records),
        "skipped": sorted(skipped, key=lambda item: item["path"]),
    }


def analyze_public_github_repository(url: str, ref: str | None = None, transport=None, *, review_context=None) -> dict:
    """Resolve, download and locally analyze one public GitHub repository commit."""
    owner, repository, normalized_url = parse_public_github_url(url)
    requested_ref = _validate_ref(ref)
    fetch = transport or _https_transport
    encoded_owner, encoded_repository = quote(owner, safe=""), quote(repository, safe="")
    commit_path = f"/repos/{encoded_owner}/{encoded_repository}/commits/{quote(requested_ref, safe='')}"
    _, commit_payload = _request(fetch, "api.github.com", commit_path, MAX_API_BYTES, 200)
    commit_sha = _commit_sha(commit_payload)
    archive_path = f"/repos/{encoded_owner}/{encoded_repository}/zipball/{commit_sha}"
    archive_headers, _ = _request(fetch, "api.github.com", archive_path, MAX_API_BYTES, 302)
    codeload_path = _archive_redirect(archive_headers.get("location"), owner, repository, commit_sha)
    _, archive_payload = _request(fetch, "codeload.github.com", codeload_path, MAX_ARCHIVE_BYTES, 200)

    with TemporaryDirectory(prefix="blastradius-public-github-") as temporary:
        source, extraction = extract_public_github_archive(archive_payload, Path(temporary) / "repository")
        options = {"review_context": review_context} if review_context is not None else {}
        result = analyze_repository(source, f"{owner}/{repository}", **options)
    result.pop("analysis_hash", None)
    result["repository"]["input"] = {
        "kind": "public-github-url",
        "url": normalized_url,
        "requested_ref": requested_ref,
        "commit_sha": commit_sha,
        "archive_sha256": sha256(archive_payload).hexdigest(),
        "archive_extraction": extraction,
    }
    result["coverage"]["archive_skipped_files"] = len(extraction["skipped"])
    result["analysis_hash"] = sha256(canonical(result)).hexdigest()
    return result
