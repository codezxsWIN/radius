from copy import deepcopy
import json
from urllib.parse import quote

import pytest

from blastradius.analysis import Analysis
from blastradius.connectors.aws_iam import REQUIRED_CONTEXT, normalize_exports, pattern_matches
from blastradius.model import GraphError, canonical

USER = "arn:aws:iam::000000000000:user/FictionalAster"
ROLE = "arn:aws:iam::000000000000:role/FictionalLoom"
BUCKET = "arn:aws:s3:::fictional-copper-meadow"
SECRET = "arn:aws:secretsmanager:us-east-1:000000000000:secret:fictional-ledger"


def bundle():
    policy_arn = "arn:aws:iam::000000000000:policy/FictionalReadAndAssume"
    shared = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": [BUCKET, BUCKET + "/*"]}, {"Effect": "Allow", "Action": "sts:AssumeRole", "Resource": ROLE}]}
    details = {
        "IsTruncated": False,
        "UserDetailList": [{"UserName": "FictionalAster", "UserId": "FICTIONALUSER", "Arn": USER, "Path": "/", "GroupList": ["FictionalReaders"], "AttachedManagedPolicies": [], "UserPolicyList": [{"PolicyName": "FictionalDenyWrite", "PolicyDocument": {"Version": "2012-10-17", "Statement": {"Effect": "Deny", "Action": "s3:PutObject", "Resource": BUCKET + "/*"}}}]}],
        "GroupDetailList": [{"GroupName": "FictionalReaders", "GroupId": "FICTIONALGROUP", "Arn": "arn:aws:iam::000000000000:group/FictionalReaders", "GroupPolicyList": [], "AttachedManagedPolicies": [{"PolicyName": "FictionalReadAndAssume", "PolicyArn": policy_arn}]}],
        "RoleDetailList": [{"RoleName": "FictionalLoom", "RoleId": "FICTIONALROLE", "Arn": ROLE, "AssumeRolePolicyDocument": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::000000000000:root"}, "Action": "sts:AssumeRole"}]}, "AttachedManagedPolicies": [], "RolePolicyList": [{"PolicyName": "FictionalWriteAndReadSecret", "PolicyDocument": {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:PutObject", "Resource": BUCKET + "/*"}, {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": SECRET}]}}]}],
        "Policies": [{"PolicyName": "FictionalReadAndAssume", "Arn": policy_arn, "DefaultVersionId": "v1", "PolicyVersionList": [{"VersionId": "v1", "IsDefaultVersion": True, "Document": shared}]}],
    }
    metadata = {"synthetic": True, "organization": "Fictional Copper Meadow AWS", "account_id": "000000000000", "observed_at": "2026-09-09T00:00:00Z", "policy_context": dict(REQUIRED_CONTEXT), "principal_types": {ROLE: "ai_agent"},
                "credential_inventory": [{"id": "fictional-aws-user-metadata", "principal_arn": USER, "type": "key", "name": "Fictional user metadata"}, {"id": "fictional-aws-role-metadata", "principal_arn": ROLE, "type": "token", "name": "Fictional authorized role metadata"}],
                "resource_inventory": [{"arn": BUCKET, "name": "Fictional bucket", "subtype": "storage_account", "sensitivity": 0.5, "operations": [{"action": "s3:ListBucket", "resource_arn": BUCKET, "canonical_action": "read_metadata"}, {"action": "s3:GetObject", "resource_arn": BUCKET + "/*", "canonical_action": "read"}, {"action": "s3:PutObject", "resource_arn": BUCKET + "/*", "canonical_action": "write"}]}, {"arn": SECRET, "name": "Fictional secret metadata", "subtype": "secret_store", "sensitivity": 1.0, "operations": [{"action": "secretsmanager:GetSecretValue", "resource_arn": SECRET, "canonical_action": "read_secret"}]}],
                "secret_links": []}
    return details, metadata


def test_aws_hand_computed_role_transition_and_deny_context():
    details, metadata = bundle()
    graph = normalize_exports(details, metadata)
    records = {item["credential_id"]: item for item in Analysis(graph).run(False)["credentials"]}
    assert records["fictional-aws-user-metadata"]["absolute_reach"] == 4
    assert records["fictional-aws-role-metadata"]["absolute_reach"] == 2
    zero = {item["credential_id"]: item for item in Analysis(graph, steps=0).run(False)["credentials"]}
    assert zero["fictional-aws-user-metadata"]["step_bounded_radius"] == 0.5
    assert records["fictional-aws-user-metadata"]["canonical_radius"] == 1
    assert records["fictional-aws-role-metadata"]["canonical_radius"] == 0.5


def test_assume_requires_both_identity_permission_and_root_trust():
    details, metadata = bundle()
    details["Policies"][0]["PolicyVersionList"][0]["Document"]["Statement"].pop()
    result = Analysis(normalize_exports(details, metadata)).run(False)
    assert all(item["absolute_reach"] == 2 for item in result["credentials"])
    details, metadata = bundle()
    details["RoleDetailList"][0]["AssumeRolePolicyDocument"]["Statement"][0]["Effect"] = "Deny"
    assert all(item["absolute_reach"] == 2 for item in Analysis(normalize_exports(details, metadata)).run(False)["credentials"])


def test_urlencoded_policies_and_literal_brackets():
    details, metadata = bundle()
    original = normalize_exports(details, metadata)
    version = details["Policies"][0]["PolicyVersionList"][0]
    version["Document"] = quote(json.dumps(version["Document"]))
    assert canonical(normalize_exports(details, metadata)) == canonical(original)
    assert pattern_matches("bucket/[abc]", "bucket/[abc]")
    assert not pattern_matches("bucket/a", "bucket/[abc]")


@pytest.mark.parametrize("case", ["truncated", "condition", "boundary", "scp", "trust", "variable", "material", "aws-secret", "aws-session"])
def test_unsupported_aws_context_fails_explicitly(case):
    details, metadata = bundle()
    if case == "truncated": details["IsTruncated"] = True
    if case == "condition": details["UserDetailList"][0]["UserPolicyList"][0]["PolicyDocument"]["Statement"]["Condition"] = {"Bool": {"aws:MultiFactorAuthPresent": True}}
    if case == "boundary": details["UserDetailList"][0]["PermissionsBoundary"] = {"PermissionsBoundaryArn": "fictional"}
    if case == "scp": metadata["policy_context"]["service_control_policies"] = "unknown"
    if case == "trust": details["RoleDetailList"][0]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"] = {"AWS": USER}
    if case == "variable": details["UserDetailList"][0]["UserPolicyList"][0]["PolicyDocument"]["Statement"]["Resource"] = "${aws:username}"
    if case == "material": details["UserDetailList"][0]["secretText"] = "REJECT-SENTINEL"
    if case == "aws-secret": details["UserDetailList"][0]["SecretAccessKey"] = "REJECT-SENTINEL"
    if case == "aws-session": details["UserDetailList"][0]["SessionToken"] = "REJECT-SENTINEL"
    with pytest.raises(GraphError): normalize_exports(details, metadata)


def test_saved_aws_fixture_runs_through_cli(tmp_path):
    from pathlib import Path
    from blastradius.cli import main
    from blastradius.model import read_graph
    folder = Path(__file__).resolve().parents[1] / "connectors" / "aws_iam" / "fixtures" / "basic"
    output = tmp_path / "aws.json"
    assert main(["collect-aws-iam", "--exports", str(folder), "--out", str(output)]) == 0
    records = Analysis(read_graph(output)).run(False)["credentials"]
    assert sorted(record["absolute_reach"] for record in records) == [2, 4]
