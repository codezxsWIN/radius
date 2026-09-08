"""Tenant-level discrete-noise aggregate experiment; no real-data release service."""

from collections import Counter
from fractions import Fraction
import math
import secrets

from .model import GraphError
from .summary import PRINCIPAL_TYPES, validate_summary

CELLS = tuple(f"{minority}:p95-bin-{bucket}" for minority in ("nhi-minority", "nhi-not-minority") for bucket in range(10)) + ("empty-credential-population",)
NHI_TYPES = tuple(kind for kind in PRINCIPAL_TYPES if kind not in {"human_user", "group"})
DEFAULT_Q = Fraction(1, 2)
DEFAULT_K = 10


def tenant_cell(summary):
    validate_summary(summary)
    if summary["constraint_model"] != "default" or summary["action_profile"] != "core-1-3-5":
        raise GraphError("Aggregate cohorts must use the declared default/core action profile.")
    count = summary["node_counts"]["credential"]
    if not count:
        return "empty-credential-population"
    rank = (95 * count + 99) // 100
    cumulative = 0
    for bucket, item in enumerate(summary["canonical_radius_histogram"]):
        cumulative += item["count"]
        if cumulative >= rank:
            break
    nhi = sum(summary["principal_counts"][kind] for kind in NHI_TYPES)
    human = summary["principal_counts"]["human_user"]
    label = "nhi-minority" if nhi < human else "nhi-not-minority"
    return f"{label}:p95-bin-{bucket}"


def histogram(summaries):
    counts = Counter(tenant_cell(summary) for summary in summaries)
    return {cell: counts[cell] for cell in CELLS}


def geometric_noise(random_source, q=DEFAULT_Q):
    q = Fraction(q)
    if q not in (Fraction(3, 4), Fraction(1, 2), Fraction(1, 4)):
        raise GraphError("Only reviewed rational noise parameters are implemented.")
    values = []
    for draw in range(2):
        value = 0
        while random_source.randrange(q.denominator) < q.numerator:
            value += 1
        values.append(value)
    return values[0] - values[1]


def support_threshold(k=DEFAULT_K, q=DEFAULT_Q, family_error=Fraction(1, 100)):
    q = Fraction(q)
    if type(k) is not int or k < 2 or not 0 < family_error < 1:
        raise GraphError("Invalid support target or family error.")
    threshold = k
    while len(CELLS) * q ** (threshold - k + 1) / (1 + q) > family_error:
        threshold += 1
    return threshold


def aggregate_synthetic(summaries, random_source=None, q=DEFAULT_Q, k=DEFAULT_K):
    q = Fraction(q)
    if q not in (Fraction(3, 4), Fraction(1, 2), Fraction(1, 4)):
        raise GraphError("Unsupported noise parameter.")
    random_source = random_source or secrets.SystemRandom()
    counts = histogram(summaries)
    threshold = support_threshold(k, q)
    released = {}
    for cell in CELLS:
        noisy = max(0, counts[cell] + geometric_noise(random_source, q))
        released[cell] = noisy if noisy >= threshold else None
    return {"release_profile": "synthetic-experiment-1.0-draft", "synthetic": True,
            "privacy_unit": "one independently deduplicated tenant", "adjacency": "add-or-remove-one-tenant",
            "epsilon": math.log(q.denominator / q.numerator), "delta": 0, "noise_q": str(q),
            "target_support_k": k, "noisy_release_threshold": threshold,
            "small_cell_family_error_bound": float(len(CELLS) * q ** (threshold - k + 1) / (1 + q)),
            "cells": released, "real_release_authorized": False}


class BudgetLedger:
    def __init__(self, maximum=math.log(2)):
        if not math.isfinite(maximum) or maximum <= 0:
            raise GraphError("A privacy budget must be finite and positive.")
        self.maximum = maximum
        self.spent = 0.0
        self.releases = set()

    def reserve(self, release_id, epsilon):
        if not isinstance(release_id, str) or not release_id or not math.isfinite(epsilon) or epsilon <= 0:
            raise GraphError("Invalid release reservation.")
        if release_id in self.releases or self.spent + epsilon > self.maximum + 1e-12:
            raise GraphError("Repeated release or privacy budget exhausted; reuse the cached release.")
        self.spent += epsilon
        self.releases.add(release_id)
