"""Write a talk track from the actual verified result, never illustrative KPI constants."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / "results" / "result.json").read_text(encoding="utf-8"))
    stats = result["statistics"]["canonical_radius"]
    first = result["credentials"][0]
    agent = next(item for item in result["credentials"] if item["name"] == "Fictional Copilot Fern")
    percent = lambda value: f"{100 * value:.2f}%"
    changes = result["recommendations"]
    lines = ["# Five-Minute Demo Script", "", "Open demo/index.html directly in a browser. This file is generated from results/result.json; all numbers below are computed, not illustrative.", "",
             "## 0:00-0:45 - Establish Scope", "", f"Say: This is {result['organization']}, an entirely synthetic tenant. The scanner models {stats['count']} credential metadata records against {result['universe_size']} declared resource-action pairs. It contacts no cloud tenant and contains no secret values.", "",
             "## 0:45-1:30 - Read the Headline", "", f"Point to the five KPIs: {stats['count']} credentials, {percent(stats['max'])} maximum, {percent(stats['p95'])} p95, {stats['gini']:.3f} Gini, and {percent(stats['share_above_threshold'])} above the configured 25% threshold.", "",
             f"Click the widest-credential name, **{first['name']}**. The selected detail must show {percent(first['canonical_radius'])} and {first['absolute_reach']} resource-action pairs. Canonical radius is reach divided by the declared universe, not a probability of breach.", "",
             "## 1:30-2:30 - Follow Evidence", "", "Click Credentials in the top navigation. Enter `Copilot Fern` in Search credentials. One row remains. Click **Fictional Copilot Fern**.", "",
             f"The detail must show {percent(agent['canonical_radius'])} and {agent['absolute_reach']} pairs. The path panel shows the shortest-escalation witness to the highest-sensitivity reachable resource. Open Evidence and constraints to reveal edge evidence identifiers and blocked transitions.", "",
             "This selected witness does not purport to be every path. The agent also has an explicit assumed-identity path into the build identity, whose PIM-eligible secret-store access can obtain another credential in the modeled graph. The engine tests separately prove that metadata-only reads cannot make that transition.", "",
             "## 2:30-3:15 - Compare Populations", "", "Clear search. Choose **AI agent** in All identity types: 20 rows remain. Click the Pairs header twice to demonstrate numeric ascending/descending order. Return to All identity types.", "",
             f"Under Identity comparison, agent median is {percent(result['by_type']['ai_agent']['median'])} and agent p95 is {percent(result['by_type']['ai_agent']['p95'])}; human median is {percent(result['by_type']['human_user']['median'])} and human p95 is {percent(result['by_type']['human_user']['p95'])}. These describe this constructed tenant, not real-world prevalence.", "",
             "## 3:15-4:15 - Evaluate One Change", "", "Click What-if analysis in the top navigation. The five rows are independent, precomputed binding removals; do not add their effects together.", ""]
    for index, change in enumerate(changes, 1):
        lines.append(f"{index}. Select `{change['binding_id']}`: before {percent(change['before_p95'])}, after {percent(change['after_p95'])}, change {100 * change['delta_p95']:.2f} percentage points; {change['affected_credentials']} credentials affected, {change['absolute_pairs_removed']} credential-pair exposures removed.")
    lines.extend(["", f"Say: {changes[0]['evaluated_candidates'] if changes else 0} candidate removals were actually evaluated. This identifies the best modeled permission removal, not whether the business can safely remove it. The input graph is unchanged.", "",
                  "## 4:15-5:00 - Reproducibility and Limits", "", f"Point to the footer: engine {result['engine_version']}, model {result['constraint_model']}, snapshot time {result['generated_at']}, and SHA-256 `{result['snapshot_hash']}`.", "",
                  "Say: Re-analysis with the same graph, parameters and external signing key is byte-identical. The report exporter checked the HMAC; this HTML is not itself a signature-verification tool. The source result is portable, but independent HMAC verification needs the separately held local key. Live tenant collection and production assurance are not demonstrated here.", ""])
    destination = ROOT / "demo" / "DEMO_SCRIPT.md"
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated talk track from manifest {result['manifest_hash']}")


if __name__ == "__main__":
    main()
