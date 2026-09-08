"""Offline synthetic read-only RBAC profile; never reads kubeconfig or a cluster."""

from hashlib import sha256
import json
from pathlib import Path

from ..model import GraphError, canonical, normalized, validate
from ..synthetic import Builder

PROFILE = "kubernetes-rbac-readonly-1"
KINDS = ("pods", "configmaps", "secrets")
ALLOWED_CONTEXT = {"authorizer": "RBAC-only", "inventory": "complete-declared-namespaces", "token_context": "valid-api-audience-unexpired", "privileged_bypass": False}


def require(condition, message):
    if not condition:
        raise GraphError(message)


def identifier(category, *parts):
    return category + "-" + sha256(canonical(list(parts))).hexdigest()[:24]


def ingest_data(data):
    require(isinstance(data, dict) and set(data) == {"metadata", "service_accounts", "roles", "bindings"}, "Use the closed synthetic Kubernetes export profile.")
    metadata = data["metadata"]
    require(isinstance(metadata, dict) and set(metadata) == {"synthetic", "organization", "observed_at", "profile", "context", "namespaces", "credential_inventory", "stored_credentials"}, "Kubernetes sidecar fields are incomplete or contain unsupported data.")
    require(metadata["synthetic"] is True and metadata["organization"].startswith("Fictional ") and metadata["profile"] == PROFILE, "Only the synthetic Kubernetes profile is supported.")
    require(metadata["context"] == ALLOWED_CONTEXT, "Unknown authorizers, token validity or privileged bypass make this RBAC profile incomplete.")
    namespaces = metadata["namespaces"]
    require(isinstance(namespaces, list) and namespaces and all(isinstance(name, str) and name for name in namespaces) and len(set(namespaces)) == len(namespaces), "A unique finite namespace inventory is required.")
    builder = Builder(metadata["organization"])
    builder.graph["observed_at"] = metadata["observed_at"]
    builder.graph["coverage"] = [
        "Synthetic Kubernetes RBAC read-only profile: one collection/action per declared namespace and pods/configmaps/secrets kind; not whole-cluster radius.",
        "get/list/watch map to read, except Secrets map to read_secret; no secret values are imported.",
        "Only explicit valid API-audience credential metadata and stored-credential sidecars are accepted; no automatic token existence or vulnerability inference.",
        "Other authorizers, system:masters, wildcard/aggregated roles, resourceNames, writes, subresources, impersonation and workload privilege pivots are rejected.",
    ]
    resources = {}
    for namespace in sorted(namespaces):
        for kind in KINDS:
            resource_id = identifier("collection", namespace, kind)
            resources[namespace, kind] = resource_id
            builder.node(resource_id, "resource", "secret_store" if kind == "secrets" else "collection", actions=["read_secret" if kind == "secrets" else "read"], sensitivity=1 if kind == "secrets" else 0.5)
    principals, group_nodes = {}, {}
    for record in data["service_accounts"]:
        require(set(record) == {"apiVersion", "kind", "metadata"} and record["apiVersion"] == "v1" and record["kind"] == "ServiceAccount", "ServiceAccounts must be metadata-only v1 objects.")
        info = record["metadata"]
        require(set(info) == {"name", "namespace"} and info["namespace"] in namespaces and isinstance(info["name"], str) and info["name"], "Invalid ServiceAccount metadata.")
        key = (info["namespace"], info["name"])
        require(key not in principals, "Duplicate ServiceAccount identity.")
        principal = identifier("serviceaccount", *key)
        principals[key] = principal
        builder.node(principal, "principal", "workload_identity")
        for group in ("system:authenticated", "system:serviceaccounts", "system:serviceaccounts:" + key[0]):
            if group not in group_nodes:
                group_nodes[group] = builder.node(identifier("group", group), "principal", "group")
            builder.edge(identifier("membership", *key, group), "member_of", principal, group_nodes[group])
    credentials = {}
    for record in metadata["credential_inventory"]:
        require(set(record) == {"id", "namespace", "service_account", "type"} and record["type"] == "token", "Credential inventory permits explicit token metadata, never token values.")
        owner = principals.get((record["namespace"], record["service_account"]))
        require(owner is not None and isinstance(record["id"], str) and record["id"] not in credentials, "Credential metadata has an unknown owner or duplicate ID.")
        credential = identifier("credential", record["id"])
        credentials[record["id"]] = credential
        builder.node(credential, "credential", "token", principal_id=owner)
        builder.edge(identifier("authentication", record["id"]), "authenticates_as", credential, owner)
    roles = {}
    for role in data["roles"]:
        require(set(role) == {"apiVersion", "kind", "metadata", "rules"} and role["apiVersion"] == "rbac.authorization.k8s.io/v1" and role["kind"] in {"Role", "ClusterRole"}, "Only explicit materialized nonaggregated Role/ClusterRole rules are supported.")
        namespaced = role["kind"] == "Role"
        expected_fields = {"name", "namespace"} if namespaced else {"name"}
        require(set(role["metadata"]) == expected_fields, "Role scope metadata is invalid.")
        namespace = role["metadata"].get("namespace")
        require(not namespaced or namespace in namespaces, "Role namespace is outside the inventory.")
        key = (role["kind"], namespace, role["metadata"]["name"])
        require(key not in roles, "Duplicate role.")
        for rule in role["rules"]:
            require(set(rule) == {"apiGroups", "resources", "verbs"} and rule["apiGroups"] == [""], "Named resources, nonresource URLs, aggregation and noncore APIs require another profile.")
            require(isinstance(rule["resources"], list) and rule["resources"] and set(rule["resources"]) <= set(KINDS), "Unsupported resource or wildcard in read-only profile.")
            require(isinstance(rule["verbs"], list) and rule["verbs"] and set(rule["verbs"]) <= {"get", "list", "watch"}, "Writes, impersonation, bind/escalate and wildcard verbs are unsupported.")
        roles[key] = role
    seen_bindings = set()
    for binding in data["bindings"]:
        require(set(binding) == {"apiVersion", "kind", "metadata", "subjects", "roleRef"} and binding["apiVersion"] == "rbac.authorization.k8s.io/v1" and binding["kind"] in {"RoleBinding", "ClusterRoleBinding"}, "Unsupported Kubernetes binding object.")
        namespaced = binding["kind"] == "RoleBinding"
        require(set(binding["metadata"]) == ({"name", "namespace"} if namespaced else {"name"}), "Invalid binding metadata.")
        namespace = binding["metadata"].get("namespace")
        require(not namespaced or namespace in namespaces, "Binding namespace is outside the inventory.")
        binding_key = (binding["kind"], namespace, binding["metadata"]["name"])
        require(binding_key not in seen_bindings, "Duplicate binding.")
        seen_bindings.add(binding_key)
        reference = binding["roleRef"]
        require(set(reference) == {"apiGroup", "kind", "name"} and reference["apiGroup"] == "rbac.authorization.k8s.io" and reference["kind"] in {"Role", "ClusterRole"}, "Invalid role reference.")
        require(namespaced or reference["kind"] == "ClusterRole", "ClusterRoleBinding cannot bind a namespaced Role.")
        role = roles.get((reference["kind"], namespace if reference["kind"] == "Role" else None, reference["name"]))
        require(role is not None, "Role reference is unresolved.")
        binding_id = builder.node(identifier("binding", *binding_key), "binding", "role_assignment")
        selected_subjects = set()
        for subject in binding["subjects"]:
            if subject.get("kind") == "ServiceAccount":
                require(set(subject) <= {"kind", "name", "namespace", "apiGroup"} and subject.get("apiGroup", "") == "", "Unsupported ServiceAccount subject fields.")
                owner = principals.get((subject.get("namespace", namespace), subject.get("name")))
                require(owner is not None, "ServiceAccount subject is not in the explicit inventory.")
                selected_subjects.add(owner)
            else:
                require(set(subject) == {"kind", "name", "apiGroup"} and subject["kind"] == "Group" and subject["apiGroup"] == "rbac.authorization.k8s.io" and subject["name"] in group_nodes, "Only declared built-in service-account/authenticated groups are supported; users and privileged bypass groups require another profile.")
                selected_subjects.add(group_nodes[subject["name"]])
        for subject in sorted(selected_subjects):
            builder.edge(identifier("assignment", binding_id, subject), "assigned", subject, binding_id)
        granted = set()
        for scope in [namespace] if namespaced else sorted(namespaces):
            for rule in role["rules"]:
                for kind in rule["resources"]:
                    granted.add((resources[scope, kind], "read_secret" if kind == "secrets" else "read"))
        for resource, action in sorted(granted):
            builder.edge(identifier("grant", binding_id, resource, action), "grants", binding_id, resource, actions=[action])
    seen_stores = set()
    for record in metadata["stored_credentials"]:
        require(set(record) == {"namespace", "credential_id"} and record["namespace"] in namespaces and record["credential_id"] in credentials, "Stored credential metadata is incomplete or outside the finite profile.")
        store_key = (record["namespace"], record["credential_id"])
        require(store_key not in seen_stores, "Duplicate stored-credential declaration.")
        seen_stores.add(store_key)
        for principal in principals.values():
            builder.edge(identifier("acquire", principal, *store_key), "can_read_secret", principal, credentials[record["credential_id"]], requires={"resource_id": resources[record["namespace"], "secrets"], "action": "read_secret"})
    for item in builder.graph["nodes"] + builder.graph["edges"]:
        item["provenance"] = {"connector": PROFILE, "source_api": "offline metadata-only RBAC export and explicit sidecars", "observed_at": metadata["observed_at"], "evidence_ref": item["id"]}
    return validate(normalized(builder.graph))


def ingest(path):
    return ingest_data(json.loads(Path(path).read_text(encoding="utf-8-sig")))