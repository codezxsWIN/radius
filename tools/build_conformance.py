"""Freeze independently computed expectations and human derivations for core fixtures."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blastradius.conformance import PROFILE, REQUIRED_MODELS
from blastradius.model import canonical, graph_hash, normalized, number, validate
from blastradius.oracle import expected
from blastradius.synthetic import Builder, FIXTURE_COUNTS, fixture


def independent_statistics(values):
    ordered = sorted(values)
    count = len(ordered)
    if not count: return {"credential_count": 0, "maximum": None, "p95": None, "gini": None, "share_above_threshold": None}
    mean = sum(ordered) / count
    gini = sum(abs(first-second) for first in ordered for second in ordered) / (2 * count * count * mean) if mean else Fraction()
    return {"credential_count": count, "maximum": str(max(ordered)), "p95": str(ordered[-(-95 * count // 100)-1]), "gini": str(gini), "share_above_threshold": str(Fraction(sum(value > Fraction(1,4) for value in ordered), count))}


def independent_response(graph, model, budget):
    full, bounded = expected(graph, model), expected(graph, model, budget)
    resources = {node["id"]: node for node in graph["nodes"] if node["kind"] == "resource"}
    universe_count = sum(len(node["actions"]) for node in resources.values())
    sensitivity_total = sum(number(node["sensitivity"]) * len(node["actions"]) for node in resources.values())
    action_total = sum(graph["action_weights"][action] for node in resources.values() for action in node["actions"])
    credentials = []
    for identifier, record in sorted(full.items()):
        pairs = record["pairs"]
        weighted = sum(number(resources[resource]["sensitivity"]) for resource, action in pairs)
        actions = sum(graph["action_weights"][action] for resource, action in pairs)
        credentials.append({"credential_id": identifier, "absolute_reach": len(pairs), "universe_size": universe_count, "canonical_radius": str(Fraction(len(pairs), universe_count)),
                            "sensitivity_weighted_radius": str(weighted/sensitivity_total) if sensitivity_total else None,
                            "action_weighted_radius": str(Fraction(actions, action_total)), "step_bounded_radius": str(Fraction(len(bounded[identifier]["pairs"]), universe_count)),
                            "reachable_pairs": pairs, "bounded_pairs": bounded[identifier]["pairs"], "witness": record["witness"]})
    response = {"contract_version": PROFILE, "status": "ok", "snapshot_hash": graph_hash(graph), "parameters": {"constraint_model": model, "step_bound": budget, "threshold": "1/4"},
                "credentials": credentials, "statistics": {field: independent_statistics([Fraction(record[field]) for record in credentials if record[field] is not None]) for field in ("canonical_radius", "sensitivity_weighted_radius", "action_weighted_radius", "step_bounded_radius")}}
    response["manifest_hash"] = sha256(canonical(response)).hexdigest()
    return response


def cases():
    requirements = [("direct",["BR-R01","BR-R07","BR-R09","BR-R20","BR-R26"]),("duplicate",["BR-R04"]),("nested",["BR-R08"]),("pim",["BR-R14"]),("approval",["BR-R14","BR-R15"]),("device",["BR-R15"]),("network",["BR-R16"]),("time",["BR-R16"]),("deny",["BR-R10"]),("cycle",["BR-R08","BR-R11","BR-R13","BR-R19"]),("secret",["BR-R12"]),("metadata",["BR-R12"]),("zero-sensitivity",["BR-R21"])]
    result = [(fixture(name),name,ids,1,False,f"Hand-derived alpha reach under default: {FIXTURE_COUNTS[name]}/4; see tests/fixtures/README.md for the path and weight arithmetic.") for name,ids in requirements]
    graph = fixture("direct"); graph["edges"] = []
    result.append((graph,"no-grants",["BR-R05","BR-R26"],1,False,"No transitions exist; all radii are zero, universe remains four."))
    graph = fixture("direct"); next(edge for edge in graph["edges"] if edge["kind"]=="grants")["actions"]=["read","write"]
    result.append((graph,"two-actions",["BR-R09"],1,False,"r0/read and r0/write are distinct; alpha reaches 2/4, sensitivity 0.4/2 and action 4/8."))
    builder=Builder();builder.graph=fixture("direct");builder.node("ungranted","resource","storage_account",actions=["read"],sensitivity=1)
    result.append((builder.graph,"fixed-universe",["BR-R03","BR-R06","BR-R20"],1,False,"Add an ungranted declared resource/action: alpha remains one pair but denominator becomes five; absolute reach prevents hiding this dilution."))
    graph=fixture("direct");next(node for node in graph["nodes"] if node["id"]=="r0")["sensitivity"]=0.8;next(node for node in graph["nodes"] if node["id"]=="r1")["sensitivity"]=0.2
    result.append((graph,"sensitivity-profile",["BR-R21","BR-R24"],1,False,"Alpha reaches r0/read, weight0.8; full sensitivity2*(0.8+0.2)=2, radius2/5."))
    graph=fixture("direct");graph["action_weights"].update(read=2,write=9)
    result.append((graph,"action-profile",["BR-R22","BR-R24"],1,False,"Alpha read weight2; universe action total22; action radius1/11, canonical1/4."))
    for name,budget,description in [("pim",0,"Eligible but not activated at k=0; unbounded1/4, bounded0."),("cycle",1,"One assumption adds beta's r1/write; alpha bounded/unbounded2/4."),("secret",0,"Metadata and secret read cost zero; credential acquisition costs one. Alpha unbounded3/4, bounded2/4.")]:
        result.append((fixture(name),name+f"-k{budget}",["BR-R23"],budget,False,description))
    result.append((fixture("direct"),"active-k0",["BR-R09","BR-R14","BR-R23"],0,False,"An active assignment needs no elevation: both bounded and unbounded1/4 at k=0."))
    builder=Builder();builder.graph=fixture("direct");builder.node("credential-alpha-2","credential","token",principal_id="alpha");builder.edge("auth-second","authenticates_as","credential-alpha-2","alpha")
    result.append((builder.graph,"two-credentials",["BR-R25","BR-R28"],1,False,"Both independent authenticators reach the same one pair; each1/4, principal union1/4, Gini0, share strictly above1/4 is0."))
    for mode in ("completed","unclaimed","approval","access"):
        builder=Builder();builder.graph=fixture("direct")
        credential=next(node for node in builder.graph["nodes"] if node["kind"]=="credential");credential.update(subtype="token",session_satisfied_constraints=["device_required"] if mode!="unclaimed" else [])
        builder.node("factor","constraint","approval_required" if mode=="approval" else "device_required")
        auth=next(edge for edge in builder.graph["edges"] if edge["kind"]=="authenticates_as");auth["constraints"]=["factor"]
        if mode=="access":next(node for node in builder.graph["nodes"] if node["kind"]=="binding")["constraints"]=["factor"]
        result.append((builder.graph,"session-"+mode,["BR-R17","BR-R18"],1,False,"Default/strict block. Session-aware reaches1/4 only for an explicit completed device factor on authentication; missing claim, fresh approval and access gates remain0."))
    builder=Builder();builder.graph=fixture("direct");builder.identity("beta");next(edge for edge in builder.graph["edges"] if edge["kind"]=="grants")["actor_id"]="beta"
    result.append((builder.graph,"actor-restriction",["BR-R11","BR-R28"],1,False,"Alpha reaches a binding restricted to beta but cannot act as beta; beta has no assignment. Both zero."))
    builder=Builder();builder.graph=fixture("direct");builder.node("group","principal","group");builder.edge("group-link","member_of","alpha","group");builder.binding("group-deny","group",[("r0",["read"])],effect="deny")
    result.append((builder.graph,"inherited-deny",["BR-R10"],1,False,"Static group deny subtracts the actor's only allowed pair; zero reach."))
    graph=fixture("direct");graph["nodes"].reverse();graph["edges"].reverse()
    for item in graph["nodes"]+graph["edges"]:item["provenance"]["connector"]="other-platform-reference"
    result.append((graph,"order-and-platform",["BR-R27","BR-R29"],1,False,"Order and connector label do not change1/4 metric; normalized input and result hashes are stable for this evidence content."))
    graph=fixture("direct");graph["nodes"]=[node for node in graph["nodes"] if node["kind"]!="credential"];graph["edges"]=[edge for edge in graph["edges"] if edge["kind"]!="authenticates_as"]
    result.append((graph,"empty-population",["BR-R05","BR-R25"],1,False,"Universe remains four, but zero credentials means null max/p95/Gini/share, not healthy zero."))
    builder=Builder();builder.graph=fixture("direct");builder.node("network","constraint","network_restriction");builder.edge("annotate","constrained_by","allow","network")
    result.append((builder.graph,"constraint-annotation",["BR-R06","BR-R13","BR-R16"],1,False,"Annotation constrains the binding, never grants resources; default/session1/4, strict0."))
    for name in ("unknown-type","dangling","negative-weight","empty-universe","duplicate-id","password-session","unknown-extension","unknown-constraint"):
        graph=fixture("direct")
        if name=="unknown-type":graph["nodes"][0]["subtype"]="x-unknown"
        if name=="dangling":graph["edges"][0]["target"]="absent"
        if name=="negative-weight":next(node for node in graph["nodes"] if node["kind"]=="resource")["sensitivity"]=-1
        if name=="empty-universe":graph["nodes"]=[node for node in graph["nodes"] if node["kind"]!="resource"];graph["edges"]=[]
        if name=="duplicate-id":graph["nodes"].append(deepcopy(graph["nodes"][0]))
        if name=="password-session":next(node for node in graph["nodes"] if node["kind"]=="credential").update(subtype="password",session_satisfied_constraints=["device_required"])
        if name=="unknown-extension":graph["required_extensions"]=["x-unknown"]
        if name=="unknown-constraint":next(node for node in graph["nodes"] if node["kind"]=="binding")["constraints"]=["absent"]
        result.append((graph,name,["BR-R01","BR-R02","BR-R05","BR-R18","BR-R21","BR-R30"],1,True,"Invalid input must be rejected with INVALID_GRAPH_OR_PARAMETERS; no metric is defined or fabricated."))
    return result


def main():
    folder=ROOT/"conformance"/"fixtures";folder.mkdir(parents=True,exist_ok=True)
    entries=[]
    for index,(graph,name,requirements,budget,invalid,derivation) in enumerate(cases(),1):
        identifier=f"BR-{index:03d}"
        if not invalid:validate(graph)
        expectations={model: {"contract_version":PROFILE,"status":"error","error":"INVALID_GRAPH_OR_PARAMETERS"} if invalid else independent_response(graph,model,budget) for model in REQUIRED_MODELS}
        record={"id":identifier,"revision":2,"name":name,"requirements":requirements,"step_bound":budget,"derivation":derivation,"input":graph,"expected":expectations}
        payload=canonical(record)+b"\n";(folder/f"{identifier}.json").write_bytes(payload)
        entries.append({"id":identifier,"file":f"fixtures/{identifier}.json","sha256":sha256(payload).hexdigest(),"requirements":requirements})
        lines=[f"# {identifier}: {name}","",derivation,"", "Expected outputs are frozen from the independent whole-edge oracle, with pairwise-difference Gini rather than the production rank formula.",""]
        for model,response in expectations.items():
            lines.extend([f"## {model}",""])
            if invalid:lines.append("Reject input; no metric is defined.")
            else:
                for item in response["credentials"]:
                    lines.append(f"- {item['credential_id']}: pairs={item['reachable_pairs']}; absolute={item['absolute_reach']}; universe={item['universe_size']}; canonical={item['canonical_radius']}; sensitivity={item['sensitivity_weighted_radius']}; action={item['action_weighted_radius']}; k={budget} bounded={item['step_bounded_radius']}.")
            lines.append("")
        (folder/f"{identifier}.md").write_text("\n".join(lines),encoding="utf-8")
    manifest={"profile":PROFILE,"fixture_revision":2,"revision_reason":"Include BR-R26 witness evidence in the executable contract; verify fixture byte hashes before execution.","required_models":list(REQUIRED_MODELS),"fixtures":entries}
    (ROOT/"conformance"/"manifest.json").write_bytes(canonical(manifest)+b"\n")
    print(json.dumps({"fixtures":len(entries),"model_cases":len(entries)*len(REQUIRED_MODELS),"suite_hash":sha256(canonical(manifest)).hexdigest()}))


if __name__=="__main__":main()
