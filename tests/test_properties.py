from copy import deepcopy
import random
import secrets

from blastradius.analysis import Analysis, modify_binding
from blastradius.engine import Engine
from blastradius.model import canonical, graph_hash, validate
from blastradius.signing import sign
from blastradius.synthetic import fixture, Builder


def test_monotonicity_of_effective_allow_grants_with_fixed_universe():
    complete = fixture("cycle")
    for seed in range(20):
        generator = random.Random(seed)
        partial = deepcopy(complete)
        partial["edges"] = [edge for edge in partial["edges"] if edge["kind"] != "grants" or generator.choice((True, False))]
        validate(partial)
        assert Engine(partial).reach("credential-alpha").pairs <= Engine(complete).reach("credential-alpha").pairs
        assert Analysis(partial).denominator == Analysis(complete).denominator
        first, second = Analysis(partial).credential("credential-alpha"), Analysis(complete).credential("credential-alpha")
        for metric in ("canonical_radius", "sensitivity_weighted_radius", "action_weighted_radius", "step_bounded_radius"):
            assert first[metric] <= second[metric]
    removed = modify_binding(complete, remove="allow")
    assert Engine(removed).reach("credential-alpha").pairs <= Engine(complete).reach("credential-alpha").pairs


def test_composability_independent_credentials_equal_unary_union():
    graph = fixture("cycle")
    graph["edges"] = [edge for edge in graph["edges"] if edge["kind"] != "can_assume"]
    builder = Builder()
    builder.graph = graph
    builder.identity("union", "service_principal")
    builder.edge("union-alpha", "can_assume", "union", "alpha")
    builder.edge("union-beta", "can_assume", "union", "beta")
    engine = Engine(validate(builder.graph))
    assert engine.reach("credential-union").pairs == engine.reach("credential-alpha").pairs | engine.reach("credential-beta").pairs


def test_constraint_sensitivity():
    for name in ("network", "time", "approval", "device", "secret", "pim"):
        graph = fixture(name)
        assert Engine(graph, "strict").reach("credential-alpha").pairs <= Engine(graph, "default").reach("credential-alpha").pairs <= Engine(graph, "permissive").reach("credential-alpha").pairs


def test_byte_determinism_and_manifest_hash_under_permutation():
    graph = fixture("secret")
    key = secrets.token_bytes(32)
    expected = canonical(sign(Analysis(graph).run(), key))
    for seed in range(10):
        shuffled = deepcopy(graph)
        random.Random(seed).shuffle(shuffled["nodes"])
        random.Random(seed + 1).shuffle(shuffled["edges"])
        for edge in shuffled["edges"]:
            if "actions" in edge: edge["actions"].reverse()
        assert graph_hash(shuffled) == graph_hash(graph)
        assert canonical(sign(Analysis(shuffled).run(), key)) == expected


def test_termination_and_step_order_in_mutual_escalation():
    graph = fixture("cycle")
    previous = frozenset()
    for budget in range(10):
        result = Engine(graph).reach("credential-alpha", budget)
        assert previous <= result.pairs
        assert len(result.pairs) <= 2
        previous = result.pairs
    assert previous == Engine(graph).reach("credential-alpha").pairs


def test_two_credentials_of_one_principal_compose_as_union():
    graph = fixture("direct")
    builder = Builder()
    builder.graph = graph
    builder.node("second-device", "constraint", "device_required")
    first_auth = next(edge for edge in builder.graph["edges"] if edge["kind"] == "authenticates_as")
    first_auth["constraints"] = ["second-device"]
    builder.node("credential-alpha-second", "credential", "token", principal_id="alpha")
    builder.edge("second-auth", "authenticates_as", "credential-alpha-second", "alpha")
    engine = Engine(validate(builder.graph))
    first = engine.reach("credential-alpha").pairs
    second = engine.reach("credential-alpha-second").pairs
    assert not first
    assert second == {("r0", "read")}
    assert engine.principal_reach("alpha") == first | second

