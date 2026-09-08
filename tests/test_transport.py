from io import BytesIO
import json
import secrets
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from blastradius.connectors.transport import ReadOnlyTransport, NoRedirect
from blastradius.model import GraphError


class Response(BytesIO):
    def __init__(self, value, url):
        super().__init__(json.dumps(value).encode())
        self.url = url

    def geturl(self): return self.url


class Credential:
    def get_token(self, scope):
        assert scope in {"https://graph.microsoft.com/.default", "https://management.azure.com/.default"}
        return SimpleNamespace(token=secrets.token_urlsafe(16))


def test_transport_is_disabled_and_allows_only_read_collections():
    transport = ReadOnlyTransport(Credential())
    with pytest.raises(GraphError, match="disabled"): transport.get_json("https://graph.microsoft.com/v1.0/users")
    for url in ("http://graph.microsoft.com/v1.0/users", "https://example.invalid/v1.0/users", "https://graph.microsoft.com/v1.0/users/secret", "https://management.azure.com/subscriptions/a/providers/Microsoft.Storage/storageAccounts/account/listKeys", "https://graph.microsoft.com@evil.invalid/v1.0/users"):
        with pytest.raises(GraphError): transport.check_url(url)
    with pytest.raises(GraphError): NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid")


def test_transport_paginated_gets_without_writes():
    first = "https://graph.microsoft.com/v1.0/users"
    second = first + "?$skiptoken=fictional-page"
    calls = []
    def opened(request, timeout):
        calls.append(request.full_url)
        assert request.get_method() == "GET"
        assert request.data is None
        assert timeout == 20
        if request.full_url == first: return Response({"value": [{"id": "fictional-first"}], "@odata.nextLink": second}, first)
        return Response({"value": [{"id": "fictional-second"}]}, second)
    transport = ReadOnlyTransport(Credential(), authorized=True, opener=SimpleNamespace(open=opened))
    assert len(transport.collection(first)["value"]) == 2
    assert calls == [first, second]


def test_retry_is_bounded_and_honors_retry_after():
    calls, delays = [], []
    url = "https://graph.microsoft.com/v1.0/users"
    def opened(request, timeout):
        calls.append(request)
        if len(calls) < 3: raise HTTPError(url, 429, "throttled", {"Retry-After": "2"}, None)
        return Response({"value": []}, url)
    transport = ReadOnlyTransport(Credential(), authorized=True, opener=SimpleNamespace(open=opened), sleeper=delays.append)
    assert transport.collection(url) == {"value": []}
    assert delays == [2, 2]


@pytest.mark.parametrize("next_link", ["https://example.invalid/v1.0/users", "https://graph.microsoft.com/v1.0/groups", "https://graph.microsoft.com/v1.0/users"])
def test_malicious_or_repeated_nextlinks_fail(next_link):
    url = "https://graph.microsoft.com/v1.0/users"
    transport = ReadOnlyTransport(Credential(), authorized=True, opener=SimpleNamespace(open=lambda request, timeout: Response({"value": [], "@odata.nextLink": next_link}, url)))
    with pytest.raises(GraphError): transport.collection(url)
