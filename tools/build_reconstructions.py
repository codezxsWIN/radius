"""Generate only explicitly assumed minimal graphs for cited public mechanisms."""

from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from blastradius.conformance import PROFILE, REQUIRED_MODELS, reference_response
from blastradius.model import canonical, validate
from blastradius.synthetic import Builder

CASES = [
    {"id":"snowflake-2024","title":"Snowflake 2024 customer-account campaign","grade":"A: primary incident-response account","sources":["SNOWFLAKE-PRIMARY"],"kind":"password","resource":"database-export","action":"read","control":"device_required",
     "narrative":"Mandiant traced the incidents it investigated to compromised customer credentials, often from historical infostealer infections, and reported that the impacted accounts lacked MFA. The approximately 165 organizations were notified as potentially exposed; that number is not treated here as a confirmed compromise count or graph denominator.",
     "assumptions":["A single fictional customer account is the starting credential, not a representation of every notified organization.","One database-export resource/read operation abstracts the supported table access; real table/action inventory is unknown.","Sensitivity=1 and absence of other principals in the minimal graph are assumptions, not observed tenant properties.","A hypothetical independently possessed authentication device is assumed unavailable to the attacker; generic MFA presence alone is not equated with this guarantee."],
     "boundary":"The infostealer compromise precedes the model; platform vulnerabilities are not required for the modeled credential-use segment."},
    {"id":"beacon-crm-2026","title":"Beacon CRM 2026 AWS key incident","grade":"A: primary final report, commissioned independent attestation and regulator corroboration","sources":["BEACON-PRIMARY","BEACON-FINAL","BEACON-REGULATOR"],"kind":"key","resource":"backup-collection","action":"read","control":"revoke",
     "narrative":"Beacon's September final report preserves the assessment of a probable compromised AWS access key, potentially exposed in public JavaScript build artifacts. Pages5/17 describe a database copy and transfer-volume evidence suggesting a broad download, while retaining uncertainty about exact objects and definitive exfiltration. The commissioned CYFOR attestation on page21 confirms that the credential was disabled July29 and its account subsequently deleted; it expressly does not prove whether the copies ultimately left. The report supplies no complete preincident authorization inventory.",
     "assumptions":["One fictional backup-collection/read unit represents the assessed exposed collection; it is not 1000 independently enumerated databases.","The key is assumed to authorize that abstract read. Actual IAM role, bucket policy, KMS permissions and account inventory are unavailable.","Sensitivity=1 is an investigator choice; no claim is made about records, subjects or bytes.","Revocation removes this key's authentication transition; rotation latency and alternate persistence are not modeled."],
     "boundary":"Authorization-level backup access is modeled after acquisition of the key; the probable JavaScript exposure mechanism is not independently reenacted."},
    {"id":"mlflow-cve-2026-64849","title":"MLflow CVE-2026-64849 post-acquisition scenario","grade":"B: vulnerability capability, not an identified victim incident","sources":["MLFLOW-CVE","MLFLOW-ADVISORY"],"kind":"token","resource":"assumed-workload-data","action":"read","control":"remove-grant",
     "narrative":"The CVE record and project advisory describe unauthenticated full-read SSRF capable of reaching internal or cloud metadata endpoints. The advisory's original proof used a local simulated secret service and explicitly did not have a cloud deployment. Known-exploitation enrichment does not supply a named victim's credential privileges, so this dossier is a conditional post-acquisition example rather than proof of observed cloud credential harvesting.",
     "assumptions":["Assume a workload credential was obtainable after SSRF and could read one invented resource; neither fact is established for a named victim by the reviewed record.","A token metadata node represents this hypothetical acquired authority without token material.","The single grant and sensitivity=1 are scenario parameters, not empirical observations.","Removing that assumed grant is a least-privilege counterfactual. Patching SSRF or blocking metadata protects acquisition, which is outside the core authorization metric."],
     "boundary":"The unauthenticated vulnerability step is out of scope; this case MUST NOT be counted as a validated real incident or preincident ranking result."},
    {"id":"huggingface-2026","title":"Hugging Face 2026 publicly exposed credential pivot","grade":"A: primary incident account; credential-use segment only","sources":["HF-PRIMARY"],"kind":"token","resource":"hosted-project","action":"write","control":"revoke",
     "narrative":"OpenAI's August 26 account reports recovery and sharing of publicly exposed write-capable Hugging Face credentials on July 10, followed by several software exploits and production-worker credential compromise. This minimal graph includes only a representative leaked token's declared write authority; it does not convert zero-days into legitimate privilege-escalation grants.",
     "assumptions":["One representative fictional write token and one hosted-project/write operation abstract the disclosed credential category.","The report's 14 recovered credentials do not establish a complete credential population, resource inventory or uniform scope; they are not a ranking denominator.","Sensitivity=1 and exact target scope are assumptions.","Revocation of this representative token cuts its modeled write path; it is not claimed to prevent every later exploit or every agent's access."],
     "boundary":"The reported zero-day chain, arbitrary code execution and multi-agent collaboration exceed the single-credential authorization-only model. That is an explicit limit of the metric, not evidence that it predicted all impact."},
    {"id":"circleci-2023","title":"CircleCI 2023 2FA-backed session theft","grade":"A: primary organization incident report; additional supported case","sources":["CIRCLECI-PRIMARY"],"kind":"token","resource":"production-secret-collection","action":"read_secret","control":"approval_required",
     "narrative":"CircleCI reported malware theft of a valid 2FA-backed SSO session, impersonation of an engineer and use of the engineer's production-access privileges to exfiltrate a subset of stores containing customer variables, tokens and keys. It subsequently added production step-up controls, making this a supported counterexample to treating all MFA-gated identities as blocked after session theft.",
     "assumptions":["The completed second factor is represented by an explicit completed device factor on a token authenticator, an abstraction rather than a claim about CircleCI's exact MFA technology.","One production-secret-collection/read_secret unit abstracts the disclosed subset; its full storage inventory is unknown.","The already-authorized employee production path is collapsed into one binding; real token-minting and session details are not reconstructed.","A hypothetical fresh independent approval on production access is not satisfiable by the stolen session; no claim is made that this exact historical control existed."],
     "boundary":"Initial malware execution is outside scope. The contrast between default and session-aware models illustrates why the credential starting context must be declared."},
]


def request(graph,model):return {"contract_version":PROFILE,"input":graph,"parameters":{"constraint_model":model,"step_bound":1,"threshold":"1/4"}}


def make_graph(case):
    builder=Builder("Fictional reconstruction "+case["id"])
    builder.identity("subject","service_principal" if case["kind"]=="key" else "human_user", "Fictional disclosed-credential role",case["kind"])
    builder.node(case["resource"],"resource","secret_store" if case["action"]=="read_secret" else "collection",actions=[case["action"]],sensitivity=1)
    builder.binding("reported-capability","subject",[(case["resource"],[case["action"]])])
    if case["id"]=="circleci-2023":
        credential=next(node for node in builder.graph["nodes"] if node["kind"]=="credential");credential["session_satisfied_constraints"]=["device_required"]
        builder.node("completed-authentication","constraint","device_required")
        next(edge for edge in builder.graph["edges"] if edge["kind"]=="authenticates_as")["constraints"]=["completed-authentication"]
    builder.graph["coverage"]=["Minimal public-record mechanism model; all unreported topology is explicitly assumed.",case["boundary"]]
    for item in builder.graph["nodes"]+builder.graph["edges"]:
        item["provenance"]={"connector":"public-reconstruction-v1","source_api":"no API called; cited public narrative","observed_at":"2026-09-09T00:00:00Z","evidence_ref":case["id"]+":assumption-mapping"}
    return validate(builder.graph)


def rank_completions(graph, folder):
    results = {}
    target_id = next(node["id"] for node in graph["nodes"] if node["kind"] == "credential")
    for completion in ("nine-zero-reach", "nine-broader-reach"):
        builder = Builder();builder.graph = deepcopy(graph)
        builder.node("unreported-background-resource", "resource", "collection", actions=["read"], sensitivity=1)
        for index in range(9):
            principal = f"background-{index}"
            builder.identity(principal, "service_principal")
            if completion == "nine-broader-reach":
                builder.binding(f"background-grant-{index}", principal, [(node["id"], node["actions"]) for node in builder.graph["nodes"] if node["kind"] == "resource"])
        changed = validate(builder.graph)
        response = reference_response(request(changed, "session-theft-aware"))
        from fractions import Fraction
        target = next(record for record in response["credentials"] if record["credential_id"] == target_id)
        score = Fraction(target["canonical_radius"])
        higher = sum(Fraction(record["canonical_radius"]) > score for record in response["credentials"])
        at_least = sum(Fraction(record["canonical_radius"]) >= score for record in response["credentials"])
        results[completion] = {"target_best_rank": higher + 1, "target_worst_rank": at_least, "population": len(response["credentials"]), "absolute_reach": target["absolute_reach"], "universe_size": target["universe_size"], "canonical_radius": target["canonical_radius"], "model": "session-theft-aware"}
        (folder / f"rank-{completion}-input.json").write_bytes(canonical(changed) + b"\n")
        (folder / f"rank-{completion}-output.json").write_bytes(canonical(response) + b"\n")
    assert results["nine-zero-reach"]["target_best_rank"] == results["nine-zero-reach"]["target_worst_rank"] == 1
    assert results["nine-broader-reach"]["target_best_rank"] == results["nine-broader-reach"]["target_worst_rank"] == 10
    return results


def main():
    sources=json.loads((ROOT/"reconstructions/sources.json").read_text())["sources"]
    source_map={item["id"]:item for item in sources}
    overview=[]
    for case in CASES:
        folder=ROOT/"reconstructions"/case["id"];folder.mkdir(parents=True,exist_ok=True)
        graph=make_graph(case);changed=deepcopy(graph)
        if case["control"]=="revoke":changed["edges"]=[edge for edge in changed["edges"] if edge["kind"]!="authenticates_as"]
        elif case["control"]=="remove-grant":changed["edges"]=[edge for edge in changed["edges"] if edge["kind"]!="grants"]
        else:
            builder=Builder();builder.graph=changed;builder.node("hypothetical-control","constraint",case["control"])
            if case["id"]=="circleci-2023":next(node for node in changed["nodes"] if node["kind"]=="binding")["constraints"]=["hypothetical-control"]
            else:next(edge for edge in changed["edges"] if edge["kind"]=="authenticates_as")["constraints"]=["hypothetical-control"]
        validate(changed)
        outputs={model:reference_response(request(graph,model)) for model in REQUIRED_MODELS}
        controls={model:reference_response(request(changed,model)) for model in REQUIRED_MODELS}
        for value in (*outputs.values(),*controls.values()):
            if value["status"]!="ok":raise AssertionError("Reconstruction graph failed core analysis")
        ranking={"preincident_top_decile":"not_identifiable","reason":"No reviewed source supplies the full preincident credential population and action universe; rank1/1 in a minimal graph has no decile evidentiary value.","assumed_completion_stress_test":rank_completions(graph,folder),"stress_test_status":"executed assumption-only countermodels, not estimates of the actual tenant; both add the same one unreported resource and nine credentials"}
        evidence={**case,"sources":[source_map[identifier] for identifier in case["sources"]],"ranking":ranking,"executed":True}
        for name,value in (("input.json",graph),("engine-output.json",outputs),("control-input.json",changed),("control-output.json",controls),("evidence.json",evidence)):(folder/name).write_bytes(canonical(value)+b"\n")
        lines=[f"# {case['title']}","",f"Evidence grade: **{case['grade']}**. All graphs are fictional and were executed by the reference engine.","","## Public Record","",case["narrative"],"","## Explicit Assumptions",""]
        lines.extend(f"{index}. {assumption}" for index,assumption in enumerate(case["assumptions"],1))
        lines.extend(["","## Modeled Boundary","",case["boundary"],"","## Executed Outcomes","","| Model | Absolute / Universe | Canonical | Sensitivity | Action | Bounded | Control Reach |","| --- | --- | --- | --- | --- | --- | --- |"])
        for model,response in outputs.items():
            record=response["credentials"][0];control=controls[model]["credentials"][0]
            lines.append(f"| {model} | {record['absolute_reach']}/{record['universe_size']} | {record['canonical_radius']} | {record['sensitivity_weighted_radius']} | {record['action_weighted_radius']} | {record['step_bounded_radius']} | {control['absolute_reach']} |")
        lines.extend(["",f"Control class: `{case['control']}`. Every control graph is a hypothetical intervention, not proof of historical prevention.","","## Ranking Assessment","",ranking["reason"],"","Two executed assumed completions add the SAME one unreported resource and nine credentials, holding the completed universe fixed at two pairs. Under session-theft-aware the target remains1/2. Nine zero-reach credentials put it uniquely rank1/10; nine credentials granted both pairs put it uniquely rank10/10. Input/output files for both completions are saved. Neither completion is observed; they demonstrate nonidentifiability rather than historical ranking.","","## Sources",""])
        lines.extend(f"- [{source_map[identifier]['title']}]({source_map[identifier]['url']}) ({source_map[identifier]['date']}; accessed2026-09-09)." for identifier in case["sources"])
        lines.extend(["","See ../../RECONSTRUCTION_METHOD.md for the challenge and exclusion protocol.",""])
        (folder/"narrative.md").write_text("\n".join(lines),encoding="utf-8")
        overview.append({"id":case["id"],"evidence_grade":case["grade"],"top_decile":"not_identifiable","model_reach":{model:response["credentials"][0]["absolute_reach"] for model,response in outputs.items()},"control_reach":{model:response["credentials"][0]["absolute_reach"] for model,response in controls.items()}})
    (ROOT/"reconstructions/results.json").write_bytes(canonical({"cases":overview,"observed_tenant_count":0,"supported_incident_dossiers":4,"vulnerability_scenarios":1})+b"\n")
    print(json.dumps(overview,indent=2))


if __name__=="__main__":main()
