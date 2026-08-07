import base64
from typing import Any

import httpx

BASE_URL = "https://platform.ringcentral.com"
MEDIA_BASE_URL = "https://media.ringcentral.com"
TOKEN_URL = f"{BASE_URL}/restapi/oauth/token"
JWT_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"


class RingCentralError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"RingCentral API error {status_code}: {message}")


class RingCentralClient:
    """Async httpx client wrapping the RingCentral REST API.

    Auth: JWT bearer flow (server-to-server, no user browser redirect). A JWT
    credential — issued to a "service user" in the RingCentral admin console —
    is exchanged for a short-lived access token via HTTP Basic Auth of the
    app's client_id/client_secret on POST /restapi/oauth/token. Since a fresh
    access token is cheap to obtain and this service must stay stateless, it
    re-authenticates on every call rather than caching/refreshing a token.
    """

    def __init__(self, client_id: str, client_secret: str, jwt: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._jwt = jwt

    async def _login(self, client: httpx.AsyncClient) -> str:
        basic = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        resp = await client.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": JWT_GRANT_TYPE, "assertion": self._jwt},
        )
        self._raise_for_status(resp)
        return resp.json()["access_token"]

    def _clean_params(self, params: dict | None) -> dict:
        if not params:
            return {}
        return {k: v for k, v in params.items() if v is not None}

    async def get(self, path: str, params: dict | None = None, media: bool = False) -> Any:
        base = MEDIA_BASE_URL if media else BASE_URL
        async with httpx.AsyncClient() as client:
            token = await self._login(client)
            resp = await client.get(
                f"{base}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=self._clean_params(params),
            )
            self._raise_for_status(resp)
            if media:
                return {
                    "content_type": resp.headers.get("content-type"),
                    "content_length": len(resp.content),
                    "note": "Binary media content — this tool returns metadata only, not the raw bytes.",
                }
            return resp.json() if resp.status_code != 204 else None

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RingCentralError(resp.status_code, str(detail))
