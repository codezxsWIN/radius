"""Fresh engine-backed large inputs for a scoped rendering performance test."""

import json
from pathlib import Path
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from blastradius.analysis import Analysis
from blastradius.model import canonical, validate
from blastradius.synthetic import synth


def main():
    folder=ROOT/"ui/performance"
    folder.mkdir(parents=True,exist_ok=True)
    records=[]
    for count in (10000,50000):
        start=perf_counter()
        graph=validate(synth(count,80,31))
        result=Analysis(graph).run(False,1)
        payload=canonical(result)+b"\n"
        (folder/f"result-{count}.json").write_bytes(payload)
        records.append({"credentials":len(result["credentials"]),"nodes":len(graph["nodes"]),"edges":len(graph["edges"]),"universe":result["universe_size"],"engine_pipeline_seconds":perf_counter()-start,"result_bytes":len(payload),"snapshot_hash":result["snapshot_hash"],"synthetic":True})
        print(json.dumps(records[-1]),flush=True)
    (folder/"generation.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":main()