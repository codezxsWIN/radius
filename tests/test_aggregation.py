from copy import deepcopy
from fractions import Fraction
import math
import random

import pytest

from blastradius.aggregation import BudgetLedger, CELLS, aggregate_synthetic, geometric_noise, histogram, support_threshold
from blastradius.analysis import Analysis
from blastradius.model import GraphError
from blastradius.summary import structural_preview, validate_summary
from blastradius.synthetic import fixture


def summary():
    return structural_preview(Analysis(fixture("direct")).run(False))


def test_closed_contract_rejects_extra_fields_and_inconsistent_counts():
    for change in (lambda item: item.update(tenant_name="identifier"), lambda item: item["node_counts"].update(credential=99), lambda item: item["principal_counts"].update(extra_type=1)):
        value=summary();change(value)
        with pytest.raises(GraphError):validate_summary(value)


def test_one_tenant_contributes_exactly_one_public_cell():
    value=summary()
    before=histogram([value]*12);after=histogram([value]*13)
    assert set(before)==set(CELLS)
    assert sum(abs(after[cell]-before[cell]) for cell in CELLS)==1
    assert sum(before.values())==12


def test_exact_integer_noise_reproducible_symmetric_and_centered():
    first=random.Random(22);second=random.Random(22)
    left=[geometric_noise(first) for draw in range(20000)]
    assert left==[geometric_noise(second) for draw in range(20000)]
    assert abs(sum(left)/len(left))<0.05
    assert abs(sum(value>0 for value in left)-sum(value<0 for value in left))<350
    assert all(type(value) is int for value in left)


def test_support_bound_is_noisy_not_exact_suppression():
    threshold=support_threshold()
    assert len(CELLS)*Fraction(1,2)**(threshold-10+1)/Fraction(3,2)<=Fraction(1,100)
    assert threshold>10
    result=aggregate_synthetic([summary()]*100, random.Random(19))
    assert result["epsilon"]==math.log(2)
    assert result["delta"]==0
    assert sum(value is not None for value in result["cells"].values())==1
    assert "tenant_count" not in result
    assert result["real_release_authorized"] is False


def test_incompatible_profile_and_real_input_rejected():
    for field,value in (("constraint_model","strict"),("synthetic",False),("action_profile","custom-not-comparable")):
        payload=summary();payload[field]=value
        with pytest.raises(GraphError):aggregate_synthetic([payload])
    with pytest.raises(GraphError):geometric_noise(random.Random(1),Fraction(9,10))


def test_composed_release_budget_cannot_be_spent_twice():
    ledger=BudgetLedger()
    ledger.reserve("fixed-cohort-v1",math.log(2))
    assert ledger.spent==math.log(2)
    with pytest.raises(GraphError):ledger.reserve("fixed-cohort-v1",math.log(2))
    with pytest.raises(GraphError):ledger.reserve("new-version",math.log(2))
