"""Independent small-graph ground truth via repeated whole-edge set iteration."""

from .model import GraphError, MODELS, number


def expected(graph, model="default", budget=None):
    nodes = {node["id"]: node for node in graph["nodes"]}
    if len(nodes) > 2500:
        raise GraphError("Independent exhaustive oracle is limited to small fixtures.")
    constraints = {node["id"] for node in nodes.values() if node["kind"] == "constraint" and node["subtype"] in MODELS[model]}
    attached = {}
    for edge in graph["edges"]:
        if edge["kind"] == "constrained_by": attached.setdefault(edge["source"], set()).add(edge["target"])

    def blocked(item):
        relevant = (set(item.get("constraints", [])) | attached.get(item["id"], set())) & constraints
        if model == "session-theft-aware" and item.get("kind") == "authenticates_as":
            credential = nodes[item["source"]]
            if credential["subtype"] == "token":
                completed = set(credential.get("session_satisfied_constraints", []))
                relevant = {identifier for identifier in relevant if nodes[identifier]["subtype"] not in completed}
        return bool(relevant)

    def membership(actor, access_qualified=False):
        group_set = {actor}
        while True:
            new_set = group_set | {edge["target"] for edge in graph["edges"] if edge["kind"] == "member_of" and edge["source"] in group_set and edge.get("actor_id", actor) == actor and not (access_qualified and blocked(edge))}
            if new_set == group_set: return group_set
            group_set = new_set

    def deny_set(actor):
        subjects = membership(actor)
        bindings = {edge["target"] for edge in graph["edges"] if edge["kind"] == "assigned" and edge["source"] in subjects and edge.get("actor_id", actor) == actor and nodes[edge["target"]]["effect"] == "deny"}
        return {(edge["target"], action) for edge in graph["edges"] if edge["source"] in bindings and edge["kind"] == "grants" and edge.get("actor_id", actor) == actor for action in edge["actions"]}

    universe = {(node["id"], action) for node in nodes.values() if node["kind"] == "resource" for action in node["actions"]}
    result = {}
    for credential in sorted((node for node in nodes.values() if node["kind"] == "credential"), key=lambda item: item["id"]):
        distances = {(credential["id"], "", credential["principal_id"]): 0}
        witnesses = {(credential["id"], "", credential["principal_id"]): (0, 0, ())}
        changed = True
        while changed:
            changed = False
            for edge in graph["edges"]:
                if edge["kind"] == "constrained_by" or blocked(edge): continue
                target = nodes[edge["target"]]
                if target["kind"] == "binding" and (blocked(target) or target["effect"] == "deny"): continue
                for (source_id, action, actor), distance in list(distances.items()):
                    if edge.get("actor_id", actor) != actor: continue
                    if edge["kind"] == "can_read_secret":
                        required = edge["requires"]
                        if (source_id, action) != (required["resource_id"], required["action"]) or edge["source"] not in membership(actor, access_qualified=True): continue
                    elif edge["source"] != source_id: continue
                    cost = int(edge["kind"] in {"can_assume", "can_read_secret"})
                    if edge["kind"] == "assigned":
                        cost += int(target["eligible"] or any(nodes[identifier]["subtype"] == "pim_eligible" for identifier in set(target["constraints"]) | attached.get(target["id"], set())))
                    total = distance + cost
                    if budget is not None and total > budget: continue
                    new_actor = target["principal_id"] if target["kind"] == "credential" else target["id"] if edge["kind"] == "can_assume" else actor
                    for next_action in edge.get("actions", [""]):
                        if target["kind"] == "resource" and (target["id"], next_action) in deny_set(actor): continue
                        state = (target["id"], next_action, new_actor)
                        prior = witnesses[(source_id, action, actor)]
                        candidate = (total, prior[1] + 1, prior[2] + (edge["id"],))
                        if state not in witnesses or candidate < witnesses[state]:
                            distances[state] = total
                            witnesses[state] = candidate
                            changed = True
        pairs = {(identifier, action) for identifier, action, actor in distances if nodes[identifier]["kind"] == "resource"}
        sensitivity_total = sum(number(nodes[identifier]["sensitivity"]) for identifier, action in universe)
        sensitivity_reach = sum(number(nodes[identifier]["sensitivity"]) for identifier, action in pairs)
        action_total = sum(graph["action_weights"][action] for identifier, action in universe)
        action_reach = sum(graph["action_weights"][action] for identifier, action in pairs)
        witness = None
        if pairs:
            state = min((state for state in witnesses if nodes[state[0]]["kind"] == "resource"), key=lambda state: (-number(nodes[state[0]]["sensitivity"]), witnesses[state], state[:2]))
            rank = witnesses[state]
            witness = {"resource_id": state[0], "action": state[1], "escalation_steps": rank[0], "graph_hops": rank[1], "edge_ids": list(rank[2])}
        result[credential["id"]] = {"pairs": [list(pair) for pair in sorted(pairs)], "absolute_reach": len(pairs), "canonical_radius": len(pairs) / len(universe), "sensitivity_weighted_radius": float(sensitivity_reach / sensitivity_total) if sensitivity_total else None, "action_weighted_radius": action_reach / action_total, "witness": witness}
    return result
