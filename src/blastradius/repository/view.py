"""Self-contained repository review views with pinned inline content policies."""

from base64 import b64encode
from hashlib import sha256
from pathlib import Path
import re

from ..model import canonical
from .report import render_repository_markdown, render_repository_sarif


ASSETS = Path(__file__).resolve().parents[1] / "assets"


def _page(configuration):
    stylesheet = (ASSETS / "review.css").read_text(encoding="utf-8")
    for marker, filename in (("ATKINSON", "AtkinsonHyperlegible-Regular.ttf"), ("PLEX", "IBMPlexSerif-Regular.ttf")):
        stylesheet = stylesheet.replace(f"__{marker}_FONT__", b64encode((ASSETS / filename).read_bytes()).decode("ascii"))
    script = (ASSETS / "review.js").read_text(encoding="utf-8")
    script_hash = b64encode(sha256(script.encode("utf-8")).digest()).decode("ascii")
    style_hash = b64encode(sha256(stylesheet.encode("utf-8")).digest()).decode("ascii")
    policy = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; font-src data:; img-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'"
    data = canonical(configuration).decode("ascii").replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    replacements = {
        "__REVIEW_STYLE__": stylesheet, "__REVIEW_SCRIPT__": script,
        "__REVIEW_ICONS__": (ASSETS / "review-icons.svg").read_text(encoding="utf-8"),
        "__REVIEW_DATA__": data, "__REVIEW_CSP__": policy,
    }
    template = (ASSETS / "review.html").read_text(encoding="utf-8")
    return re.sub(r"__REVIEW_(?:STYLE|SCRIPT|ICONS|DATA|CSP)__", lambda match: replacements[match.group()], template)


def render_repository_html(result):
    exports = {
        "json": canonical(result).decode("ascii") + "\n",
        "md": render_repository_markdown(result),
        "sarif": canonical(render_repository_sarif(result)).decode("ascii") + "\n",
    }
    return _page({"mode": "snapshot", "result": result, "exports": exports})


def render_repository_workbench(token):
    return _page({"mode": "live", "token": token})