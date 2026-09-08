import json
from pathlib import Path
import secrets

from jsonschema import Draft7Validator

from blastradius.analysis import Analysis
from blastradius.reports import render, sarif
from blastradius.signing import sign
from blastradius.synthetic import fixture


def result():
    return sign(Analysis(fixture("secret")).run(), secrets.token_bytes(32))


def test_sarif_matches_published_schema():
    schema = json.loads((Path(__file__).resolve().parents[1] / "schema" / "sarif-2.1.0.schema.json").read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(sarif(result()))


def test_markdown_rank_paths_and_real_recommendation():
    text = render(result(), "md")
    assert "Top Ten Explanations" in text
    assert "acquire-beta" in text
    assert "Best Single Modeled Change" in text
    assert "candidates were actually evaluated" in text


def test_html_self_contained_data_and_xss_escaping():
    payload = result()
    payload["organization"] = "Fictional </script><img src=x onerror=alert(1)>"
    html = render(payload, "html")
    assert '<script src=' not in html
    assert 'fetch(' not in html
    assert "<img src=x" not in html
    assert "\\u003c/script\\u003e" in html
    assert "__DATA__" not in html
    assert 'id="ranked-body"' in html
    assert 'id="histogram"' in html
    assert payload["snapshot_hash"] in html
    assert render(payload, "html") == html
