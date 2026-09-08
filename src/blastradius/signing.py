"""Local HMAC signing; keys never enter fixtures, artifacts or report bodies."""

from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets

from .model import GraphError, canonical


def default_key_path():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "BlastRadius" / "v0.1" / "manifest-hmac.key"


def load_key(path=None, create=False):
    path = Path(path) if path else default_key_path()
    if not path.exists() and create:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(secrets.token_bytes(32))
    key = path.read_bytes()
    if len(key) != 32:
        raise GraphError("Signing requires an external 32-byte local key; key contents are never printed.")
    return key


def sign(result, key):
    if not isinstance(key, bytes) or len(key) != 32:
        raise GraphError("HMAC signing requires a 32-byte key.")
    if "signature" in result:
        raise GraphError("Refusing to sign a payload that already has a signature.")
    return {**result, "signature": {"algorithm": "HMAC-SHA256", "key_id": sha256(key).hexdigest()[:16], "value": hmac.new(key, canonical(result), "sha256").hexdigest()}}


def verify(result, key):
    if not isinstance(key, bytes) or len(key) != 32:
        raise GraphError("HMAC verification requires a 32-byte key.")
    if not isinstance(result, dict) or not isinstance(result.get("signature"), dict):
        raise GraphError("A manifest must contain a structured HMAC signature object.")
    signature = result.get("signature", {})
    payload = {field: value for field, value in result.items() if field != "signature"}
    if signature.get("algorithm") != "HMAC-SHA256" or signature.get("key_id") != sha256(key).hexdigest()[:16]:
        raise GraphError("Signature algorithm or key identifier does not match.")
    expected = hmac.new(key, canonical(payload), "sha256").hexdigest()
    if not isinstance(signature.get("value"), str) or not hmac.compare_digest(expected, signature["value"]):
        raise GraphError("Manifest signature verification failed; payload may have changed.")
    declared = payload.get("manifest_hash")
    content = {field: value for field, value in payload.items() if field != "manifest_hash"}
    if declared != sha256(canonical(content)).hexdigest():
        raise GraphError("Manifest content hash is inconsistent.")
    return True
