import contextvars

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import RingCentralClient
from .config import Settings

# Header names are a registered contract (SOP §3.1): X-<Vendor>-<Credential>,
# ASCII, hyphen-separated, each segment capitalized. Renaming these is a
# breaking change and must not be done silently.
CLIENT_ID_HEADER = "X-RingCentral-Client-Id"
CLIENT_SECRET_HEADER = "X-RingCentral-Client-Secret"
JWT_HEADER = "X-RingCentral-Jwt"

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent requests from
# different tenants are isolated from one another.
_gateway_creds_var: contextvars.ContextVar[tuple[str, str, str] | None] = contextvars.ContextVar(
    "ringcentral_gateway_creds", default=None
)


def get_client_from_context(settings: Settings) -> RingCentralClient | None:
    """Resolve the active RingCentralClient for the current request context."""
    creds = _gateway_creds_var.get()
    if creds is None:
        return None
    client_id, client_secret, jwt = creds
    return RingCentralClient(client_id, client_secret, jwt)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads the three required RingCentral credential headers from the request
    and stores them in the contextvar. Returns 401 if any is missing on /mcp
    requests. Credentials are never read from environment variables — see
    SOP §3.1.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        client_id = request.headers.get(CLIENT_ID_HEADER.lower())
        client_secret = request.headers.get(CLIENT_SECRET_HEADER.lower())
        jwt = request.headers.get(JWT_HEADER.lower())
        if not client_id or not client_secret or not jwt:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": (
                        f"This server requires the {CLIENT_ID_HEADER}, "
                        f"{CLIENT_SECRET_HEADER}, and {JWT_HEADER} headers"
                    ),
                    "required_headers": [CLIENT_ID_HEADER, CLIENT_SECRET_HEADER, JWT_HEADER],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set((client_id, client_secret, jwt))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all RingCentral tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="ringcentral-mcp",
        instructions=(
            "RingCentral is a cloud phone/UCaaS platform: it provides an "
            "organization's extensions (users/queues/departments), phone "
            "numbers, presence status, call queues, directory and personal "
            "contacts, and call log/recording history. Use this server for "
            "questions about a customer's phone system — who has which "
            "extension, what numbers are provisioned, whether someone is "
            "available/on a call, who's in a call queue, or history of "
            "inbound/outbound calls and their recordings. All tools are "
            "read-only. Typical flow: ringcentral_list_extensions to find an "
            "extension, then ringcentral_get_presence or "
            "ringcentral_list_user_call_log with that extension_id; "
            "ringcentral_list_queues then ringcentral_list_queue_members to "
            "see who staffs a queue; a call-log entry's recording.id feeds "
            "ringcentral_get_call_recording / "
            "ringcentral_download_call_recording."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    def client_factory() -> RingCentralClient | None:
        return get_client_from_context(settings)

    from .tools import telephony

    telephony.register(mcp, client_factory)

    return mcp
