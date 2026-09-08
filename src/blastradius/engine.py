"""Actor-scoped fixed-point traversal with subtractive denies and guarded escalation."""

from collections import defaultdict, deque
from dataclasses import dataclass
from heapq import heappop, heappush

from .model import GraphError, MODELS


@dataclass(frozen=True)
class Reach:
    credential_id: str
    paths: dict
    blocked: tuple

    @property
    def pairs(self):
        return frozenset(self.paths)


class Engine:
    def __init__(self, graph, model="default"):
        if model not in MODELS:
            raise GraphError("Unknown constraint model.")
        self.graph = graph
        self.model = model
        self.nodes = {node["id"]: node for node in graph["nodes"]}
        self.edges = {edge["id"]: edge for edge in graph["edges"]}
        self.out = defaultdict(list)
        self.attached = defaultdict(list)
        self.secret_edges = defaultdict(list)
        self._groups = {}
        self._denials = {}
        for edge in sorted(graph["edges"], key=lambda item: item["id"]):
            if edge["kind"] == "constrained_by":
                self.attached[edge["source"]].append(edge["target"])
            elif edge["kind"] == "can_read_secret":
                self.secret_edges[(edge["requires"]["resource_id"], "read_secret")].append(edge)
            else:
                self.out[edge["source"]].append(edge)

    def constraints(self, item):
        return tuple(sorted(set(item.get("constraints", [])) | set(self.attached.get(item["id"], []))))

    def blocked_constraints(self, item):
        satisfied = set()
        if self.model == "session-theft-aware" and item.get("kind") == "authenticates_as":
            credential = self.nodes[item["source"]]
            if credential["subtype"] == "token":
                satisfied.update(credential.get("session_satisfied_constraints", []))
        return tuple(identifier for identifier in self.constraints(item) if self.nodes[identifier]["subtype"] in MODELS[self.model] and self.nodes[identifier]["subtype"] not in satisfied)

    def groups(self, actor, access_qualified=False):
        cache_key = (actor, access_qualified)
        if cache_key not in self._groups:
            found, queue = {actor}, deque([actor])
            while queue:
                current = queue.popleft()
                for edge in self.out.get(current, ()):
                    if edge["kind"] == "member_of" and edge.get("actor_id", actor) == actor and edge["target"] not in found and not (access_qualified and self.blocked_constraints(edge)):
                        found.add(edge["target"])
                        queue.append(edge["target"])
            self._groups[cache_key] = frozenset(found)
        return self._groups[cache_key]

    def denials(self, actor):
        if actor not in self._denials:
            denied = set()
            for subject in self.groups(actor):
                for assignment in self.out.get(subject, ()):
                    if assignment["kind"] != "assigned" or assignment.get("actor_id", actor) != actor:
                        continue
                    binding = self.nodes[assignment["target"]]
                    if binding["effect"] != "deny":
                        continue
                    for grant in self.out.get(binding["id"], ()):
                        if grant["kind"] == "grants" and grant.get("actor_id", actor) == actor:
                            denied.update((grant["target"], action) for action in grant["actions"])
            self._denials[actor] = frozenset(denied)
        return self._denials[actor]

    def reach(self, credential_id, max_steps=None):
        credential = self.nodes.get(credential_id, {})
        if credential.get("kind") != "credential":
            raise GraphError("Select an existing credential metadata ID.")
        if max_steps is not None and (type(max_steps) is not int or max_steps < 0):
            raise GraphError("Escalation budget must be a nonnegative integer.")
        actor = credential["principal_id"]
        initial = (credential_id, "", actor)
        labels = {initial: (0, 0, ())}
        queue = [((0, 0, ()), initial)]
        paths, blocked = {}, set()
        while queue:
            rank, state = heappop(queue)
            if labels[state] != rank:
                continue
            node_id, action, actor = state
            node = self.nodes[node_id]
            if node["kind"] == "resource":
                pair = (node_id, action)
                if pair not in paths or rank < paths[pair]:
                    paths[pair] = rank
                successors = self.secret_edges.get(pair, ())
            else:
                successors = self.out.get(node_id, ())
            for edge in successors:
                if edge.get("actor_id", actor) != actor:
                    continue
                if edge["kind"] == "can_read_secret" and edge["source"] not in self.groups(actor, access_qualified=True):
                    continue
                failed = self.blocked_constraints(edge)
                target = self.nodes[edge["target"]]
                if target["kind"] == "binding":
                    failed += self.blocked_constraints(target)
                    if target["effect"] == "deny":
                        continue
                if failed:
                    blocked.add((edge["id"], "constraint", tuple(sorted(set(failed)))))
                    continue
                cost = int(edge["kind"] in {"can_assume", "can_read_secret"})
                if edge["kind"] == "assigned":
                    eligible = target["eligible"] or any(self.nodes[item]["subtype"] == "pim_eligible" for item in self.constraints(target))
                    cost += int(eligible)
                new_rank = (rank[0] + cost, rank[1] + 1, rank[2] + (edge["id"],))
                if max_steps is not None and new_rank[0] > max_steps:
                    continue
                next_actor = target["principal_id"] if target["kind"] == "credential" else target["id"] if edge["kind"] == "can_assume" else actor
                actions = edge.get("actions", [""])
                for target_action in actions:
                    if target["kind"] == "resource" and (target["id"], target_action) in self.denials(actor):
                        blocked.add((edge["id"], "deny", (target_action,)))
                        continue
                    next_state = (target["id"], target_action, next_actor)
                    if next_state not in labels or new_rank < labels[next_state]:
                        labels[next_state] = new_rank
                        heappush(queue, (new_rank, next_state))
        return Reach(credential_id, dict(sorted(paths.items())), tuple(sorted(blocked)))

    def principal_reach(self, principal_id, max_steps=None):
        principal = self.nodes.get(principal_id, {})
        if principal.get("kind") != "principal" or principal.get("subtype") == "group":
            raise GraphError("Principal reach requires a non-group principal.")
        result = set()
        for identifier, node in sorted(self.nodes.items()):
            if node["kind"] == "credential" and node["principal_id"] == principal_id:
                result.update(self.reach(identifier, max_steps).pairs)
        return frozenset(result)
