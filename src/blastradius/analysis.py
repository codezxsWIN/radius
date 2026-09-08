"""Exact metric arithmetic, explanatory witnesses and actual binding interventions."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256

from . import __version__
from .engine import Engine
from .model import GraphError, canonical, graph_hash, number, normalized


def distribution(values, threshold=Fraction(1, 4)):
    ordered = sorted(values)
    size = len(ordered)
    if not size:
        return {"count": 0, "max": None, "p95": None, "median": None, "gini": None, "share_above_threshold": None}
    total = sum(ordered)
    median = ordered[size // 2] if size % 2 else (ordered[size // 2 - 1] + ordered[size // 2]) / 2
    gini = sum((2 * index - size - 1) * value for index, value in enumerate(ordered, 1)) / (size * total) if total else Fraction()
    return {"count": size, "max": float(ordered[-1]), "p95": float(ordered[(95 * size + 99) // 100 - 1]), "median": float(median),
            "gini": float(gini), "share_above_threshold": sum(value > threshold for value in ordered) / size}


def ratio(value, denominator):
    return None if denominator == 0 else float(Fraction(value, denominator))


class Analysis:
    def __init__(self, graph, model="default", steps=1, threshold=0.25):
        graph = normalized(graph)
        if type(steps) is not int or steps < 0:
            raise GraphError("steps must be a nonnegative integer.")
        self.threshold = number(threshold)
        if not 0 <= self.threshold <= 1:
            raise GraphError("threshold must lie in [0,1].")
        self.graph, self.model, self.steps = graph, model, steps
        self.engine = Engine(graph, model)
        self.nodes = self.engine.nodes
        self.resources = {identifier: node for identifier, node in self.nodes.items() if node["kind"] == "resource"}
        self.universe = {(identifier, action) for identifier, node in self.resources.items() for action in node["actions"]}
        self.denominator = len(self.universe)
        if not self.denominator:
            raise GraphError("Empty universe has undefined radius.")
        self.sensitivity = {identifier: number(node["sensitivity"]) for identifier, node in self.resources.items()}
        self.sensitivity_total = sum(self.sensitivity[identifier] for identifier, action in self.universe)
        self.action_total = sum(graph["action_weights"][action] for identifier, action in self.universe)

    def credential(self, credential_id, explain=True):
        reach = self.engine.reach(credential_id)
        credential = self.nodes[credential_id]
        principal = self.nodes[credential["principal_id"]]
        bounded_pairs = {pair for pair, rank in reach.paths.items() if rank[0] <= self.steps}
        sensitivity_sum = sum(self.sensitivity[identifier] for identifier, action in reach.pairs)
        action_sum = sum(self.graph["action_weights"][action] for identifier, action in reach.pairs)
        explanation = None
        if explain and reach.pairs:
            target = min(reach.pairs, key=lambda pair: (-self.sensitivity[pair[0]], reach.paths[pair], pair))
            steps, hops, path_ids = reach.paths[target]
            explanation = {"resource_id": target[0], "resource_name": self.nodes[target[0]]["name"], "action": target[1], "escalation_steps": steps, "graph_hops": hops,
                           "steps": [{**self.engine.edges[edge_id], "source_name": self.nodes[self.engine.edges[edge_id]["source"]]["name"], "target_name": self.nodes[self.engine.edges[edge_id]["target"]]["name"]} for edge_id in path_ids]}
        record = {"credential_id": credential_id, "principal_id": principal["id"], "name": principal["name"], "principal_type": principal["subtype"], "credential_type": credential["subtype"],
                  "absolute_reach": len(reach.pairs), "universe_size": self.denominator,
                  "canonical_radius": len(reach.pairs) / self.denominator,
                  "sensitivity_weighted_radius": float(sensitivity_sum / self.sensitivity_total) if self.sensitivity_total else None,
                  "action_weighted_radius": action_sum / self.action_total,
                  "step_bounded_radius": len(bounded_pairs) / self.denominator,
                  "exact": {"canonical": f"{len(reach.pairs)}/{self.denominator}", "sensitivity": None if not self.sensitivity_total else str(sensitivity_sum / self.sensitivity_total), "action": str(Fraction(action_sum, self.action_total)), "bounded": f"{len(bounded_pairs)}/{self.denominator}"},
                  "explanation": explanation,
                  "blocked": [{"edge_id": item[0], "reason": item[1], "details": list(item[2])} for item in reach.blocked]}
        return record

    def run(self, recommendations=True, path_limit=100):
        credentials = [self.credential(identifier, explain=False) for identifier, node in sorted(self.nodes.items()) if node["kind"] == "credential"]
        credentials.sort(key=lambda item: (-item["canonical_radius"], item["credential_id"]))
        for record in credentials[:path_limit]:
            record["explanation"] = self.credential(record["credential_id"])["explanation"]
        statistics = {}
        for metric in ("canonical_radius", "sensitivity_weighted_radius", "action_weighted_radius", "step_bounded_radius"):
            exact_field = {"canonical_radius": "canonical", "sensitivity_weighted_radius": "sensitivity", "action_weighted_radius": "action", "step_bounded_radius": "bounded"}[metric]
            values = [Fraction(record["exact"][exact_field]) for record in credentials if record["exact"][exact_field] is not None]
            statistics[metric] = distribution(values, self.threshold)
        by_type = {}
        for subtype in sorted({item["principal_type"] for item in credentials}):
            by_type[subtype] = distribution([Fraction(record["exact"]["canonical"]) for record in credentials if record["principal_type"] == subtype], self.threshold)
        result = {"format_version": "0.1", "synthetic": True, "organization": self.graph["organization"], "snapshot_hash": graph_hash(self.graph), "schema_version": "0.1", "engine_version": __version__,
                  "constraint_model": self.model, "parameters": {"step_bound": self.steps, "threshold": str(self.threshold), "path_limit": path_limit}, "generated_at": self.graph["observed_at"],
                  "time_basis": "deterministic snapshot observed_at, not analysis wall-clock", "universe_size": self.denominator,
                  "credentials": credentials, "statistics": statistics, "by_type": by_type, "coverage": self.graph["coverage"], "recommendations": [],
                  "recommendation_status": "not requested", "snapshot": normalized(self.graph)}
        if recommendations:
            if len(credentials) > 200 or len(self.graph["edges"]) > 5000:
                result["recommendation_status"] = "Deferred: exhaustive G0 candidate evaluation is limited to 200 credentials / 5000 edges; no sampling or claimed optimum."
            else:
                result["recommendations"] = self.rank_removals(credentials, statistics)
                result["recommendation_status"] = "Every eligible allow binding evaluated; top five shown, including zero-impact candidates if fewer than five reduce p95."
        result["manifest_hash"] = sha256(canonical(result)).hexdigest()
        return result

    def rank_removals(self, baseline, statistics):
        candidates = sorted(identifier for identifier, node in self.nodes.items() if node["kind"] == "binding" and node["effect"] == "allow")
        records = []
        baseline_values = {record["credential_id"]: record for record in baseline}
        for identifier in candidates:
            changed = modify_binding(self.graph, remove=identifier)
            engine = Analysis(changed, self.model, self.steps, self.threshold)
            after_records = [engine.credential(item["credential_id"], explain=False) for item in baseline]
            after_stats = distribution([Fraction(item["exact"]["canonical"]) for item in after_records], self.threshold)
            before_p95, after_p95 = statistics["canonical_radius"]["p95"], after_stats["p95"]
            delta = 0 if before_p95 is None else after_p95 - before_p95
            records.append({"binding_id": identifier, "name": self.nodes[identifier]["name"], "before_p95": before_p95, "after_p95": after_p95, "delta_p95": delta,
                            "absolute_pairs_removed": sum(item["absolute_reach"] - after["absolute_reach"] for item, after in zip(baseline, after_records)),
                            "affected_credentials": sum(item["absolute_reach"] != baseline_values[item["credential_id"]]["absolute_reach"] for item in after_records), "evaluated_candidates": len(candidates)})
        return sorted(records, key=lambda item: (item["delta_p95"], -item["absolute_pairs_removed"], item["binding_id"]))[:5]


def modify_binding(graph, remove=None, addition=None):
    result = deepcopy(graph)
    if (remove is None) == (addition is None):
        raise GraphError("Choose exactly one binding addition or removal.")
    if remove is not None:
        target = next((node for node in result["nodes"] if node["id"] == remove), {})
        if target.get("kind") != "binding":
            raise GraphError("Removal requires an existing binding ID.")
        removed_edge_ids = {edge["id"] for edge in result["edges"] if remove in (edge["source"], edge["target"])}
        result["nodes"] = [node for node in result["nodes"] if node["id"] != remove]
        result["edges"] = [edge for edge in result["edges"] if edge["id"] not in removed_edge_ids and edge["source"] not in removed_edge_ids]
    else:
        if set(addition) != {"binding", "edges"} or addition["binding"].get("kind") != "binding" or addition["binding"].get("effect") not in {"allow", "deny"}:
            raise GraphError("Addition must contain one explicit allow/deny binding and its edges; it cannot add resources or principals.")
        identifier = addition["binding"]["id"]
        for edge in addition["edges"]:
            valid = (
                edge.get("kind") == "assigned" and edge.get("target") == identifier
                or edge.get("kind") in {"grants", "constrained_by"} and edge.get("source") == identifier
            )
            if not valid:
                raise GraphError("A binding addition may only add that binding's assignments, grants and direct constraints, not unrelated escalation edges.")
        result["nodes"].append(addition["binding"])
        result["edges"].extend(addition["edges"])
    return normalized(result)


def compare(before, after):
    if before["universe_size"] != after["universe_size"]:
        raise GraphError("The what-if universe must remain fixed.")
    originals = {item["credential_id"]: item for item in before["credentials"]}
    metrics = ("canonical_radius", "sensitivity_weighted_radius", "action_weighted_radius", "step_bounded_radius", "absolute_reach")
    deltas = []
    for item in after["credentials"]:
        changes = {metric: None if item[metric] is None else item[metric] - originals[item["credential_id"]][metric] for metric in metrics}
        present = [value for value in changes.values() if value is not None]
        deltas.append({"credential_id": item["credential_id"], "name": item["name"], "deltas": changes, "metric_divergence": any(value < 0 for value in present) and any(value > 0 for value in present)})
    stat_deltas = {metric: {name: None if value is None or before["statistics"][metric][name] is None else value - before["statistics"][metric][name] for name, value in stats.items()} for metric, stats in after["statistics"].items()}
    return {"synthetic": True, "simulation_only": True, "delta_convention": "after-minus-before", "before_hash": before["snapshot_hash"], "after_hash": after["snapshot_hash"], "credentials": sorted(deltas, key=lambda item: item["credential_id"]), "tenant_statistic_deltas": stat_deltas}
