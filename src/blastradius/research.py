"""Prespecified synthetic population and descriptive, non-empirical analysis."""

from collections import Counter
from fractions import Fraction
import math
import random
from statistics import mean, median

from .aggregation import NHI_TYPES, CELLS, geometric_noise, histogram, support_threshold, tenant_cell
from .analysis import Analysis
from .model import GraphError, normalized, number, validate
from .summary import structural_summary
from .synthetic import Builder

SEED = 20260909
TENANTS = 500
REGIMES = ("null", "nhi-broader", "human-broader")


def generate_tenant(index, regime="null", seed=SEED):
    if regime not in REGIMES or type(index) is not int or index < 0:
        raise GraphError("Unknown synthetic regime or tenant index.")
    random_source = random.Random(seed + index * 104729)
    principal_count = random_source.randint(20, 80)
    resource_count = random_source.randint(10, 30)
    share = random_source.choice((Fraction(1, 5), Fraction(7, 20), Fraction(1, 2), Fraction(13, 20)))
    nhi_count = math.ceil(principal_count * share)
    subtypes = [NHI_TYPES[position % len(NHI_TYPES)] for position in range(nhi_count)] + ["human_user"] * (principal_count - nhi_count)
    random_source.shuffle(subtypes)
    builder = Builder(f"Fictional preregistered tenant {index:04d}")
    for position, subtype in enumerate(subtypes):
        builder.identity(f"principal-{position}", subtype, credential_type="password" if subtype == "human_user" else "federated_trust")
    pairs = []
    for position in range(resource_count):
        resource_id = f"resource-{position}"
        builder.node(resource_id, "resource", "collection", actions=["read", "write", "administer"], sensitivity=random_source.choice((0.2, 0.5, 0.8, 1.0)))
        pairs.extend((resource_id, action) for action in ("read", "write", "administer"))
    degrees = random_source.choices(range(1, 9), weights=[1 / degree**2 for degree in range(1, 9)], k=principal_count)
    for position, (subtype, degree) in enumerate(zip(subtypes, degrees)):
        broad = (regime == "nhi-broader" and subtype in NHI_TYPES) or (regime == "human-broader" and subtype == "human_user")
        degree = min(len(pairs), degree * (8 if broad else 1))
        grant_source = random.Random(seed + index * 104729 + position * 1009 + 9176)
        selected = grant_source.sample(pairs, degree)
        grouped = {}
        for resource, action in selected:
            grouped.setdefault(resource, []).append(action)
        builder.binding(f"binding-{position}", f"principal-{position}", sorted(grouped.items()))
    graph = normalized(builder.graph)
    validate(graph)
    config = {"tenant_index": index, "regime": regime, "principal_count": principal_count, "resource_count": resource_count, "target_nhi_share": str(share), "realized_nhi_count": nhi_count}
    return graph, config


def percentile(values, percent):
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * percent / 100) - 1] if ordered else None


def analyze_tenant(graph):
    analysis = Analysis(graph)
    records = [analysis.credential(node["id"], explain=False) for node in graph["nodes"] if node["kind"] == "credential"]
    unions = {"nhi": set(), "human": set()}
    principal_pairs = {}
    principal_type = {}
    for record in records:
        pairs = analysis.engine.reach(record["credential_id"]).pairs
        group = "nhi" if record["principal_type"] in NHI_TYPES else "human"
        unions[group].update(pairs)
        principal_pairs.setdefault(record["principal_id"], set()).update(pairs)
        principal_type[record["principal_id"]] = group
    if not analysis.sensitivity_total:
        raise GraphError("The registered synthetic population must have positive sensitivity weight.")
    def weighted(pairs):
        return sum(analysis.sensitivity[resource] for resource, action in pairs) / analysis.sensitivity_total
    nhi_count = sum(group == "nhi" for group in principal_type.values())
    principal_count = len(principal_type)
    nhi_share = Fraction(nhi_count, principal_count)
    nhi_reach, human_reach = weighted(unions["nhi"]), weighted(unions["human"])
    outcome = {"principal_count": principal_count, "nhi_principal_count": nhi_count, "nhi_share": float(nhi_share), "nhi_share_exact": str(nhi_share),
               "nhi_weighted_union": float(nhi_reach), "nhi_weighted_union_exact": str(nhi_reach), "human_weighted_union": float(human_reach),
               "weighted_overlap": float(weighted(unions["nhi"] & unions["human"])), "weighted_total_union": float(weighted(unions["nhi"] | unions["human"])),
               "joint_success": nhi_share < Fraction(1, 2) and nhi_reach > Fraction(1, 2), "nhi_minority": nhi_share < Fraction(1, 2),
               "human_also_majority_reach": human_reach > Fraction(1, 2), "per_principal": {}}
    for group in ("nhi", "human"):
        values = [float(weighted(pairs)) for principal, pairs in principal_pairs.items() if principal_type[principal] == group]
        outcome["per_principal"][group] = {"median": median(values) if values else None, "p95": percentile(values, 95)}
    return outcome, structural_summary(graph, records)


def wilson(successes, count):
    if not 0 <= successes <= count or count <= 0:
        raise GraphError("Wilson counts must be positive and consistent.")
    quantile = 1.959963984540054
    estimate = successes / count
    denominator = 1 + quantile**2 / count
    center = (estimate + quantile**2 / (2 * count)) / denominator
    width = quantile * math.sqrt(estimate * (1 - estimate) / count + quantile**2 / (4 * count**2)) / denominator
    return [max(0.0, center - width), min(1.0, center + width)]


def summarize_regime(outcomes):
    count = len(outcomes)
    successes = sum(item["joint_success"] for item in outcomes)
    interval = wilson(successes, count)
    verdict = "insufficient-sample" if count < 100 else "support" if interval[0] > 0.5 else "falsified" if interval[1] <= 0.5 else "inconclusive"
    return {"synthetic": True, "real_population_inference": False, "tenants": count, "eligible": count, "excluded": 0, "joint_successes": successes,
            "joint_fraction": successes / count, "wilson_95": interval, "illustrative_criterion_result": verdict,
            "nhi_minority_tenants": sum(item["nhi_minority"] for item in outcomes),
            "successes_with_human_majority_reach": sum(item["joint_success"] and item["human_also_majority_reach"] for item in outcomes),
            "mean_nhi_union": mean(item["nhi_weighted_union"] for item in outcomes), "mean_human_union": mean(item["human_weighted_union"] for item in outcomes),
            "mean_overlap": mean(item["weighted_overlap"] for item in outcomes), "mean_total_union": mean(item["weighted_total_union"] for item in outcomes),
            "mean_within_tenant_nhi_median": mean(item["per_principal"]["nhi"]["median"] for item in outcomes),
            "mean_within_tenant_human_median": mean(item["per_principal"]["human"]["median"] for item in outcomes)}


def features(summary):
    values = []
    for key in ("node_counts", "principal_counts", "credential_counts", "edge_counts", "structural_features"):
        values.extend(summary[key][field] for field in sorted(summary[key]))
    values.extend(bucket["count"] for bucket in summary["canonical_radius_histogram"])
    return tuple(values)


def linkage_stats(vectors):
    frequencies = Counter(vectors)
    count = len(vectors)
    scale = [max(1, max(row[column] for row in vectors)) for column in range(len(vectors[0]))]
    scaled = [tuple(value / bound for value, bound in zip(row, scale)) for row in vectors]
    nearest = [min(math.dist(row, other) / math.sqrt(len(row)) for other_index, other in enumerate(scaled) if other_index != index) for index, row in enumerate(scaled)]
    return {"rows": count, "feature_dimensions": len(vectors[0]), "distinct_profiles": len(frequencies),
            "unique_rows": sum(frequencies[row] == 1 for row in vectors), "unique_fraction": sum(frequencies[row] == 1 for row in vectors) / count,
            "rows_in_groups_below_k10": sum(frequencies[row] < 10 for row in vectors), "minimum_equivalence_class": min(frequencies.values()),
            "nearest_neighbor_rms_distance": {"minimum": min(nearest), "median": median(nearest), "mean": mean(nearest), "p95": percentile(nearest, 95)},
            "linkage_interpretation": "Distinctness under full structural knowledge, not measured real-world identification or membership inference accuracy."}


def privacy_experiment(summaries, repetitions=200):
    exact = [features(summary) for summary in summaries]
    rounded = [tuple(value // 10 for value in row) for row in exact]
    cells = [tuple(int(tenant_cell(summary) == cell) for cell in CELLS) for summary in summaries]
    true_counts = histogram(summaries)
    utility = []
    for q in (Fraction(3, 4), Fraction(1, 2), Fraction(1, 4)):
        threshold = support_threshold(q=q)
        errors, retained, maxima = [], [], []
        for repeat in range(repetitions):
            random_source = random.Random(SEED + repeat * 43 + q.denominator * 211 + q.numerator)
            releases = {cell: max(0, true_counts[cell] + geometric_noise(random_source, q)) for cell in CELLS}
            releases = {cell: value if value >= threshold else 0 for cell, value in releases.items()}
            differences = [abs(releases[cell] - true_counts[cell]) for cell in CELLS]
            errors.append(mean(differences))
            retained.append(sum(true_counts[cell] for cell in CELLS if releases[cell] > 0) / len(summaries))
            maxima.append(max(differences))
        utility.append({"q": str(q), "epsilon": math.log(q.denominator / q.numerator), "k_target": 10, "noisy_threshold": threshold, "trials": repetitions,
                        "mean_count_mae_including_suppression": mean(errors), "p95_count_mae": percentile(errors, 95), "mean_true_support_retained": mean(retained), "maximum_absolute_cell_error": max(maxima)})
    return {"synthetic": True, "tenants": len(summaries), "exact_summary": linkage_stats(exact), "rounded_counts_div10": linkage_stats(rounded),
            "minimal_release_projection": linkage_stats(cells), "true_synthetic_aggregate": true_counts, "utility": utility,
            "chosen_q": "1/2", "chosen_epsilon": math.log(2), "chosen_k": 10,
            "selection_basis": "Prespecified budget ln2 limits the membership likelihood ratio to2 for one ideal independently sampled release; k10 is a policy support target with a noisy screening bound, not anonymity. Parameters were fixed before observing utility."}
