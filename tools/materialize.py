"""Generate schema copies, examples and independently documented fixture artifacts."""

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blastradius.model import SCHEMA_PATH, canonical, validate
from blastradius.oracle import expected
from blastradius.synthetic import FIXTURE_COUNTS, fixture, synth


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value) + b"\n")


def main():
    schema = ROOT / "schema"
    schema.mkdir(exist_ok=True)
    shutil.copyfile(SCHEMA_PATH, schema / SCHEMA_PATH.name)
    small = validate(synth(8, 8, 7))
    write(schema / "example.json", small)
    write(schema / "example.expected.json", expected(small))
    for name in FIXTURE_COUNTS:
        write(ROOT / "tests" / "fixtures" / f"{name}.json", validate(fixture(name)))
    print(json.dumps({"generated_schema_example": True, "hand_computed_fixture_count": len(FIXTURE_COUNTS), "small_example_oracle_credentials": 8}))


if __name__ == "__main__":
    main()
