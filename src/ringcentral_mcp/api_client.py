import asyncio
import base64
from typing import Any

import httpx

from ._json import error_envelope

BASE_URL = "https://platform.ringcentral.com"
MEDIA_BASE_URL = "https://media.ringcentral.com"
TOKEN_URL = f"{BASE_URL}/restapi/oauth/token"
JWT_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 20.0

# One shared connection pool for the process lifetime. No credentials are
# ever stored on it — client_id/client_secret/jwt are passed per-request via
# headers supplied by the gateway middleware (see server.py's contextvar-based
# credential isolation, which is what actually keeps tenants apart), so
# sharing this pool across tenants/requests is safe.
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True)
    return _http_client


# status_code -> (error code, retryable). status_code 0 means a network/
# connection-level failure (no response at all).
_STATUS_TO_CODE: dict[int, tuple[str, bool]] = {
    0: ("upstream_error", True),
    400: ("invalid_argument", False),
    401: ("unauthorized", False),
    403: ("unauthorized", False),
    404: ("not_found", False),
    422: ("invalid_argument", False),
    429: ("rate_limited", True),
}


def _classify(status_code: int) -> tuple[str, bool]:
    if status_code in _STATUS_TO_CODE:
        return _STATUS_TO_CODE[status_code]
    if status_code >= 500:
        return "upstream_error", True
    return "invalid_argument", False


class RingCentralError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"RingCentral API error {status_code}: {message}")

    def to_envelope(self) -> str:
        code, retryable = _classify(self.status_code)
        return error_envelope(code, self.message, retryable)


class RingCentralClient:
    """Async httpx client wrapping the RingCentral REST API.

    Auth: JWT bearer flow (server-to-server, no user browser redirect). A JWT
    credential — issued to a "service user" in the RingCentral admin console —
    is exchanged for a short-lived access token via HTTP Basic Auth of the
    app's client_id/client_secret on POST /restapi/oauth/token. A fresh access
    token is cheap to obtain and this service must stay stateless (no
    cross-request caching of derived tokens, per SOP §3.4), so it
    re-authenticates on every call rather than caching/refreshing a token.

    Reuses the module-level connection pool (see _get_http_client) across
    every call made through this instance, rather than opening a new
    connection per request.
    """

    def __init__(self, client_id: str, client_secret: str, jwt: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._jwt = jwt

    async def _login(self) -> str:
        basic = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        body = await self._send(
            "POST",
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": JWT_GRANT_TYPE, "assertion": self._jwt},
        )
        return body["access_token"]

    def _clean_params(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def get(self, path: str, params: dict | None = None, media: bool = False) -> Any:
        token = await self._login()
        base = MEDIA_BASE_URL if media else BASE_URL
        headers = {"Authorization": f"Bearer {token}"}
        return await self._send(
            "GET", f"{base}{path}", headers=headers, params=self._clean_params(params), media=media
        )

    async def _send(
        self,
        method: str,
        url: str,
        headers: dict,
        params: dict | None = None,
        data: dict | None = None,
        media: bool = False,
    ) -> Any:
        client = _get_http_client()
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await client.request(method, url, headers=headers, params=params, data=data)
            except httpx.RequestError as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(min(2**attempt, _MAX_BACKOFF_SECONDS))
                    continue
                raise RingCentralError(0, f"{e or type(e).__name__} (url={url})") from e

            if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES:
                delay = self._retry_delay(resp, attempt)
                await asyncio.sleep(delay)
                continue

            self._raise_for_status(resp)
            return self._parse_body(resp, media=media)

        # Unreachable in practice (loop always returns or raises above), but
        # keeps type checkers happy and guards against future edits.
        if last_exc:
            raise RingCentralError(0, f"{last_exc}") from last_exc
        raise RingCentralError(0, "request failed with no response")

    def _retry_delay(self, resp: httpx.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
        return min(2**attempt, _MAX_BACKOFF_SECONDS)

    def _parse_body(self, resp: httpx.Response, media: bool) -> Any:
        if media:
            return {
                "content_type": resp.headers.get("content-type"),
                "content_length": len(resp.content),
                "note": (
                    "Binary media content — this tool returns metadata only, "
                    "not the raw bytes."
                ),
            }
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"raw_response": resp.text}

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
                if isinstance(detail, dict):
                    msg = (
                        detail.get("message")
                        or detail.get("error_description")
                        or detail.get("error")
                        or str(detail)
                    )
                else:
                    msg = str(detail)
            except ValueError:
                msg = resp.text
            raise RingCentralError(resp.status_code, msg)
