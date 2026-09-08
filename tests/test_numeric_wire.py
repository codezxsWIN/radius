from io import StringIO
from contextlib import redirect_stdout
import json
from fractions import Fraction

import pytest

from blastradius.cli import main
from blastradius.conformance import exact_statistics, reference_response
from blastradius.model import GraphError, canonical, number, read_json
from blastradius.synthetic import fixture


@pytest.mark.parametrize("token", ["0.10000000000000001", "1e-9999", "1e9999", "NaN", "Infinity"])
def test_lossy_or_nonfinite_wire_decimals_reject(token):
    with pytest.raises(GraphError):read_json(StringIO(token))


@pytest.mark.parametrize("token,expected", [("0.1", Fraction(1,10)), ("1.0", Fraction(1)), ("1e-6", Fraction(1,1000000)), ("0.5000", Fraction(1,2))])
def test_accepted_decimals_have_exact_declared_rational_value(token, expected):
    assert number(read_json(StringIO(token)))==expected


def test_adapter_returns_contract_error_for_duplicate_properties(monkeypatch):
    monkeypatch.setattr("sys.stdin",StringIO('{"contract_version":"1.0-draft","contract_version":"future"}'))
    output=StringIO()
    with redirect_stdout(output):assert main(["conformance","adapter"])==0
    assert json.loads(output.getvalue())["error"]=="INVALID_GRAPH_OR_PARAMETERS"


def test_nearest_rank_p95_is_not_just_maximum():
    result=exact_statistics([Fraction(0)]*20+[Fraction(1)],Fraction(1,4))
    assert result=={"credential_count":21,"maximum":"1","p95":"0","gini":"20/21","share_above_threshold":"1/21"}


@pytest.mark.parametrize("field,value", [("threshold",True),("threshold",0.25),("threshold",None),("step_bound",True),("step_bound",1.0),("step_bound",-1)])
def test_contract_parameter_types_do_not_coerce(field,value):
    parameters={"constraint_model":"default","step_bound":1,"threshold":"1/4"}
    parameters[field]=value
    assert reference_response({"contract_version":"1.0-draft","input":fixture("direct"),"parameters":parameters})["error"]=="INVALID_GRAPH_OR_PARAMETERS"
