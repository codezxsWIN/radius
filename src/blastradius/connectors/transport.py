"""Explicitly gated, read-only HTTPS transport. Never executed live by this build."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from ..model import GraphError
from .entra_azure import reject_material

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
ARM_BASE = "https://management.azure.com"
GRAPH_COLLECTIONS = {
    "users": "/users?$select=id,displayName,createdDateTime",
    "groups": "/groups?$select=id,displayName",
    "servicePrincipals": "/servicePrincipals?$select=id,appId,displayName,servicePrincipalType,createdDateTime,appRoles",
    "oauth2PermissionGrants": "/oauth2PermissionGrants",
    "directoryRoleAssignments": "/roleManagement/directory/roleAssignments",
    "directoryRoleDefinitions": "/roleManagement/directory/roleDefinitions",
    "roleEligibilityScheduleInstances": "/roleManagement/directory/roleEligibilityScheduleInstances",
    "conditionalAccessPolicies": "/identity/conditionalAccess/policies",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        raise GraphError("HTTP redirects are refused; credentials never follow redirects.")


class ReadOnlyTransport:
    def __init__(self, credential, authorized=False, opener=None, sleeper=time.sleep, timeout=20, max_pages=1000, attempts=4):
        self.credential = credential
        self.authorized = authorized
        self.opener = opener or build_opener(NoRedirect())
        self.sleeper = sleeper
        self.timeout, self.max_pages, self.attempts = timeout, max_pages, attempts

    def check_url(self, url):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in {"graph.microsoft.com", "management.azure.com"} or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment:
            raise GraphError("Only allowlisted HTTPS Graph/ARM origins are permitted.")
        path = unquote(parsed.path)
        if ".." in path.split("/") or "\\" in path:
            raise GraphError("Traversal is not permitted in collector URLs.")
        if parsed.hostname == "graph.microsoft.com":
            allowed = any(path == "/v1.0" + value.split("?")[0] for value in GRAPH_COLLECTIONS.values())
            allowed |= bool(re.fullmatch(r"/v1\.0/groups/[A-Za-z0-9-]+/(members|transitiveMembers)", path))
            allowed |= bool(re.fullmatch(r"/v1\.0/servicePrincipals/[A-Za-z0-9-]+/(appRoleAssignments|appRoleAssignedTo)", path))
            if not allowed: raise GraphError("Graph endpoint is not in the read-only collection allowlist.")
            return "https://graph.microsoft.com/.default"
        if not re.fullmatch(r"/subscriptions/[0-9a-fA-F-]+/(resources|providers/Microsoft\.Authorization/(roleAssignments|roleDefinitions|denyAssignments)|providers/Microsoft\.KeyVault/vaults)", path):
            raise GraphError("ARM endpoint is not in the read-only collection allowlist.")
        return "https://management.azure.com/.default"

    def _delay(self, retry_after, attempt):
        try:
            delay = float(retry_after)
        except (TypeError, ValueError):
            try:
                delay = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                delay = 2**attempt
        return max(0, min(30, delay))

    def get_json(self, url):
        if not self.authorized:
            raise GraphError("Live reads are disabled. Explicit authorization and a caller-supplied credential provider are required.")
        scope = self.check_url(url)
        for attempt in range(self.attempts):
            access = self.credential.get_token(scope)
            request = Request(url, headers={"Authorization": "Bearer " + access.token, "Accept": "application/json"}, method="GET")
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    if response.geturl() != url: raise GraphError("Unexpected response redirect.")
                    contents = response.read(16 * 1024 * 1024 + 1)
                    if len(contents) > 16 * 1024 * 1024: raise GraphError("Collector page exceeds the 16 MiB limit.")
                    value = json.loads(contents)
                    reject_material(value)
                    return value
            except HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt + 1 == self.attempts:
                    raise GraphError(f"Read-only API request failed with HTTP {error.code}; no response body or credentials are logged.") from None
                self.sleeper(self._delay(error.headers.get("Retry-After"), attempt))
            except URLError:
                if attempt + 1 == self.attempts:
                    raise GraphError("Read-only API network request failed after bounded retries.") from None
                self.sleeper(min(30, 2**attempt))
        raise GraphError("Read attempts exhausted.")

    def collection(self, url):
        original = urlsplit(url)
        seen, records = set(), []
        for _page in range(self.max_pages):
            if url in seen: raise GraphError("Repeated pagination link; refusing an infinite collection loop.")
            self.check_url(url)
            page_url = urlsplit(url)
            if (page_url.netloc, page_url.path) != (original.netloc, original.path):
                raise GraphError("Pagination cannot change origin or collection path.")
            seen.add(url)
            payload = self.get_json(url)
            if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
                raise GraphError("Expected a Graph/ARM value collection.")
            records.extend(payload["value"])
            next_link = payload.get("@odata.nextLink") or payload.get("nextLink")
            if not next_link: return {"value": records}
            url = next_link
        raise GraphError("Pagination exceeded the configured page limit; output would be incomplete.")

    def collect(self, subscription_id):
        subscription_id = str(UUID(subscription_id))
        bundle = {name: self.collection(GRAPH_BASE + path) for name, path in GRAPH_COLLECTIONS.items()}
        bundle["groupMembers"] = {group["id"]: self.collection(f"{GRAPH_BASE}/groups/{group['id']}/members") for group in bundle["groups"]["value"]}
        bundle["appRoleAssignments"] = {"value": []}
        for principal in bundle["servicePrincipals"]["value"]:
            bundle["appRoleAssignments"]["value"].extend(self.collection(f"{GRAPH_BASE}/servicePrincipals/{principal['id']}/appRoleAssignments")["value"])
        scope = f"{ARM_BASE}/subscriptions/{subscription_id}"
        for name, suffix in (("armRoleAssignments", "roleAssignments"), ("armRoleDefinitions", "roleDefinitions"), ("armDenyAssignments", "denyAssignments")):
            bundle[name] = self.collection(f"{scope}/providers/Microsoft.Authorization/{suffix}?api-version=2022-04-01")
        bundle["resources"] = self.collection(f"{scope}/resources?api-version=2021-04-01")
        bundle["vaults"] = self.collection(f"{scope}/providers/Microsoft.KeyVault/vaults?api-version=2024-11-01")
        return {"synthetic": False, "collections": bundle, "coverage": ["Live transport only, not a validated tenant scan; direct group-members service-principal omission, hidden members, directory/app/CA/PIM semantics and protected persistence require review."]}
