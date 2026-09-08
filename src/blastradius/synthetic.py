"""Invented organizations and metadata; reproducible without ambient timestamps."""

from copy import deepcopy

from .model import GraphError, normalized

OBSERVED_AT = "2026-09-09T00:00:00Z"


class Builder:
    def __init__(self, name="Fictional Lumen Orchard"):
        self.graph = {"schema_version": "0.1", "synthetic": True, "organization": name, "observed_at": OBSERVED_AT,
                      "action_weights": {"read": 1, "write": 3, "administer": 5, "read_metadata": 1, "read_secret": 1},
                      "nodes": [], "edges": [], "coverage": ["Synthetic modeled capabilities only; no real cloud authorization claim."]}

    def provenance(self, identifier):
        return {"connector": "synthetic-v0.1", "source_api": "invented-fixture", "observed_at": OBSERVED_AT, "evidence_ref": identifier}

    def node(self, identifier, kind, subtype, name=None, **attributes):
        node = {"id": identifier, "kind": kind, "subtype": subtype, "name": name or f"Fictional {identifier}", "provenance": self.provenance(identifier), **attributes}
        if kind == "binding":
            node = {"effect": "allow", "eligible": False, "constraints": [], **node}
        self.graph["nodes"].append(node)
        return identifier

    def edge(self, identifier, kind, source, target, **attributes):
        self.graph["edges"].append({"id": identifier, "kind": kind, "source": source, "target": target, "provenance": self.provenance(identifier), **attributes})

    def identity(self, identifier, subtype="human_user", name=None, credential_type="key"):
        self.node(identifier, "principal", subtype, name, provisioned_at="2026-08-01T00:00:00Z")
        credential = self.node(f"credential-{identifier}", "credential", credential_type, f"{name or 'Fictional '+identifier} metadata", principal_id=identifier)
        self.edge(f"auth-{identifier}", "authenticates_as", credential, identifier)
        return credential

    def binding(self, identifier, subject, resource_actions, constraints=(), eligible=False, effect="allow"):
        self.node(identifier, "binding", "role_assignment", effect=effect, eligible=eligible, constraints=list(constraints))
        self.edge(f"assigned-{identifier}", "assigned", subject, identifier)
        for index, (resource, actions) in enumerate(resource_actions):
            self.edge(f"grant-{identifier}-{index}", "grants", identifier, resource, actions=list(actions))


def synth(principals=80, resources=40, seed=7):
    if type(principals) is not int or not 8 <= principals <= 50000 or type(resources) is not int or not 8 <= resources <= 10000:
        raise GraphError("The feature-complete generator needs 8-50000 principals and 8-10000 resources.")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise GraphError("seed must be a nonnegative 32-bit integer.")
    builder = Builder()
    names = ["Fictional Mira Vale", "Fictional Build Loom", "Fictional Legacy Ledger", "Fictional Copilot Fern", "Fictional Agent Indigo", "Fictional Managed Quartz", "Fictional Workload Prism", "Fictional Rowan Pike"]
    subtypes = ["human_user", "service_principal", "service_principal", "ai_agent", "ai_agent", "managed_identity", "workload_identity", "human_user"]
    for index in range(principals):
        subtype = subtypes[index % len(subtypes)]
        name = names[index] if index < len(names) else f"Fictional {subtype.replace('_', ' ').title()} {index:05d}"
        builder.identity(f"principal-{index:05d}", subtype, name, "password" if subtype == "human_user" else "federated_trust")
    for index in range(resources):
        builder.node(f"resource-{index:05d}", "resource", "secret_store" if index == 0 else "database" if index % 3 == 0 else "storage_account",
                     actions=["read_metadata", "read_secret"] if index == 0 else ["read", "write", "administer"],
                     sensitivity=[0.0, 0.2, 0.5, 0.8, 1.0][index % 5] if index else 1.0)
    for kind in ("device_required", "approval_required", "network_restriction", "time_window", "pim_eligible"):
        builder.node(kind, "constraint", kind)
    for index in range(principals):
        target = 1 + ((seed + index * 13) % (resources - 1))
        actions = ["read", "write"] if index % 3 == 0 else ["read"]
        constraints = ["network_restriction", "time_window"] if index % 7 == 0 else []
        if index == 7:
            constraints = ["device_required"]
        builder.binding(f"private-{index:05d}", f"principal-{index:05d}", [(f"resource-{target:05d}", actions)], constraints)
    for level in range(3):
        builder.node(f"group-{level}", "principal", "group", f"Fictional Orchard Group {level}")
    for index in range(min(principals, 80)):
        builder.edge(f"membership-{index}", "member_of", f"principal-{index:05d}", "group-0")
    builder.edge("nested-0-1", "member_of", "group-0", "group-1")
    builder.edge("nested-1-2", "member_of", "group-1", "group-2")
    builder.edge("group-cycle", "member_of", "group-2", "group-0")
    for role in range(5):
        resource_actions = [(f"resource-{index:05d}", ["read"]) for index in range(1, resources) if index % 5 == role]
        builder.binding(f"shared-{role}", "group-2", resource_actions)
    builder.binding("vault-eligible", "principal-00001", [("resource-00000", ["read_secret"])], ["pim_eligible"], True)
    builder.binding("vault-approval", "principal-00000", [("resource-00000", ["read_secret"])], ["pim_eligible", "approval_required"], True)
    builder.binding("vault-metadata", "principal-00000", [("resource-00000", ["read_metadata"])])
    builder.binding("legacy-admin", "principal-00002", [(f"resource-{index:05d}", ["read", "write", "administer"]) for index in range(1, min(resources, 12))])
    builder.edge("vault-acquire-legacy", "can_read_secret", "principal-00001", "credential-principal-00002", requires={"resource_id": "resource-00000", "action": "read_secret"})
    builder.edge("agent-assume-build", "can_assume", "principal-00003", "principal-00001")
    builder.edge("build-assume-agent", "can_assume", "principal-00001", "principal-00003")
    builder.binding("agent-write", "principal-00004", [(f"resource-{index:05d}", ["write"]) for index in range(1, min(resources, 8))])
    builder.binding("legacy-deny", "principal-00002", [("resource-00001", ["administer"])], effect="deny")
    builder.edge("metadata-time", "constrained_by", "vault-metadata", "time_window")
    return normalized(builder.graph)


def fixture(name):
    builder = Builder("Fictional Conformance Garden")
    builder.identity("alpha", name="Fictional Alba Rune")
    for index in range(2):
        builder.node(f"r{index}", "resource", "database", actions=["read", "write"], sensitivity=[0.2, 0.8][index])
    builder.binding("allow", "alpha", [("r0", ["read"])])
    if name == "duplicate":
        builder.binding("duplicate-allow", "alpha", [("r0", ["read"])])
    elif name == "nested":
        for index in range(3):
            builder.node(f"group{index}", "principal", "group")
        builder.edge("member0", "member_of", "alpha", "group0")
        builder.edge("member1", "member_of", "group0", "group1")
        builder.edge("member2", "member_of", "group1", "group2")
        builder.graph["edges"] = [edge for edge in builder.graph["edges"] if edge["id"] != "assigned-allow"]
        builder.edge("assigned-group", "assigned", "group2", "allow")
    elif name in ("pim", "approval", "device", "network", "time"):
        types = {"pim": ["pim_eligible"], "approval": ["pim_eligible", "approval_required"], "device": ["device_required"], "network": ["network_restriction"], "time": ["time_window"]}[name]
        for kind in types:
            builder.node(kind, "constraint", kind)
        binding = next(node for node in builder.graph["nodes"] if node["id"] == "allow")
        binding.update(constraints=types, eligible=name in {"pim", "approval"})
    elif name == "deny":
        builder.binding("deny", "alpha", [("r0", ["read"])], effect="deny")
    elif name == "cycle":
        builder.identity("beta", "service_principal")
        builder.binding("beta-write", "beta", [("r1", ["write"])])
        builder.edge("assume-beta", "can_assume", "alpha", "beta")
        builder.edge("assume-alpha", "can_assume", "beta", "alpha")
    elif name in ("secret", "metadata"):
        resource = next(node for node in builder.graph["nodes"] if node["id"] == "r0")
        resource.update(subtype="secret_store", actions=["read_metadata", "read_secret"])
        grant = next(edge for edge in builder.graph["edges"] if edge["kind"] == "grants")
        grant["actions"] = ["read_metadata", "read_secret"] if name == "secret" else ["read_metadata"]
        builder.identity("beta", "service_principal")
        builder.binding("beta-write", "beta", [("r1", ["write"])])
        builder.edge("acquire-beta", "can_read_secret", "alpha", "credential-beta", requires={"resource_id": "r0", "action": "read_secret"})
    elif name == "zero-sensitivity":
        for node in builder.graph["nodes"]:
            if node["kind"] == "resource": node["sensitivity"] = 0
    elif name != "direct":
        raise GraphError("Unknown conformance fixture.")
    return normalized(builder.graph)


FIXTURE_COUNTS = {"direct": 1, "duplicate": 1, "nested": 1, "pim": 1, "approval": 0, "device": 0, "network": 1, "time": 1, "deny": 0, "cycle": 2, "secret": 3, "metadata": 1, "zero-sensitivity": 1}


def classic():
    builder = Builder("Fictional Charter Illustration")
    builder.graph["coverage"].append("Canonical cardinalities reproduce the charter illustration. No source graph was supplied; weighted values are computed from this constructed graph, not claimed to match the charter's illustrative weights.")
    for index in range(16000):
        builder.node(f"classic-resource-{index:05d}", "resource", "storage_account", actions=["read", "write", "administer"], sensitivity=[0.2, 0.5, 0.8, 1.0][index % 4])
    entries = (("finance", "human_user", "Fictional Finance Analyst", 1240), ("cicd", "service_principal", "Fictional CI CD Service", 9600), ("legacy", "human_user", "Fictional Legacy Synchronisation", 31200), ("copilot", "ai_agent", "Fictional Copilot Agent", 14400))
    for identifier, subtype, name, count in entries:
        builder.identity(identifier, subtype, name, "token" if identifier == "finance" else "key")
        grants = []
        for resource_index in range((count + 2) // 3):
            grants.append((f"classic-resource-{resource_index:05d}", ["read", "write", "administer"][:min(3, count - resource_index * 3)]))
        builder.binding(f"classic-{identifier}", identifier, grants)
    return normalized(builder.graph)
