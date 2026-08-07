# ringcentral-mcp

RingCentral MCP Service — a stateless HTTP MCP server wrapping the [RingCentral REST API](https://developers.ringcentral.com/api-reference), covering account info, extensions, phone numbers, presence, call queues, contacts, and call logs/recordings.

**Tech stack:** Python 3.12 + uv + FastMCP (Starlette/Uvicorn)

## Scope

**13 tools**, aligned to MSPbots' historical usage categories (Account Info, Extension, Phone Numbers, Presence, Queues, Queue Members, Internal Contacts, External Contacts, Company Call Log Records, User Call Log Records, Call Recording).

## Authentication

RingCentral's REST API uses the **JWT bearer flow** — a server-to-server grant with no user browser redirect. A JWT credential is generated in the RingCentral admin console for a dedicated "service user" (Roles & Permissions → the service user's JWT credential), then exchanged for a short-lived access token:

```
POST https://platform.ringcentral.com/restapi/oauth/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=<jwt>
```

The response includes both an access token and a refresh token, but since re-exchanging the JWT itself is cheap and this service must stay stateless, it re-authenticates on every call rather than caching/refreshing.

## Quick Start

```powershell
cd D:\claude\project\ringcentral-mcp
uv sync

$env:RINGCENTRAL_CLIENT_ID="your_app_client_id"
$env:RINGCENTRAL_CLIENT_SECRET="your_app_client_secret"
$env:RINGCENTRAL_JWT="your_service_user_jwt_credential"
uv run ringcentral-mcp
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

| Variable | Default | Description |
|----------|---------|--------------|
| `RINGCENTRAL_CLIENT_ID` | — | RingCentral app's client ID |
| `RINGCENTRAL_CLIENT_SECRET` | — | RingCentral app's client secret |
| `RINGCENTRAL_JWT` | — | JWT credential issued to a service user |
| `AUTH_MODE` | `gateway` | `gateway` = credentials per-request via headers (SOP-compliant); `env` = shared credentials from env vars (local dev only) |
| `MCP_TRANSPORT` | `stdio` | `stdio` (Claude Desktop) or `http` (gateway) |
| `MCP_HTTP_PORT` | `8080` | HTTP server port |

## HEADER 授权参数说明

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-RingCentral-Client-Id` | string | 是 | 无 | 无 | RingCentral App 的 Client ID | `abCdEfGhIjKlMnOpQr` |
| `X-RingCentral-Client-Secret` | string | 是 | 无 | 无 | RingCentral App 的 Client Secret | `xYz123AbC456DeF789` |
| `X-RingCentral-Jwt` | string | 是 | 无 | 无 | 绑定在某个 Service User 上的 JWT 凭据（RingCentral 后台 Roles & Permissions 生成），本服务用其换 access token | `eyJhbGciOiJSUzI1NiIs...`（一长串 JWT 字符串） |

## Claude Desktop Setup

```json
{
  "mcpServers": {
    "ringcentral": {
      "command": "uv",
      "args": ["run", "--directory", "D:/claude/project/ringcentral-mcp", "ringcentral-mcp"],
      "env": {
        "RINGCENTRAL_CLIENT_ID": "your_app_client_id",
        "RINGCENTRAL_CLIENT_SECRET": "your_app_client_secret",
        "RINGCENTRAL_JWT": "your_service_user_jwt_credential"
      }
    }
  }
}
```

## Transport Modes

### stdio
```powershell
$env:RINGCENTRAL_CLIENT_ID="your_app_client_id"
$env:RINGCENTRAL_CLIENT_SECRET="your_app_client_secret"
$env:RINGCENTRAL_JWT="your_service_user_jwt_credential"
uv run ringcentral-mcp
```

### HTTP — single-tenant
```powershell
$env:RINGCENTRAL_CLIENT_ID="your_app_client_id"
$env:RINGCENTRAL_CLIENT_SECRET="your_app_client_secret"
$env:RINGCENTRAL_JWT="your_service_user_jwt_credential"
$env:MCP_TRANSPORT="http"
$env:AUTH_MODE="env"
uv run ringcentral-mcp
```

### HTTP — gateway / multi-tenant
```powershell
$env:MCP_TRANSPORT="http"
$env:AUTH_MODE="gateway"
uv run ringcentral-mcp
# Each request must include: X-RingCentral-Client-Id, X-RingCentral-Client-Secret, X-RingCentral-Jwt headers
```

## Available Tools (13)

| Tool | Description | API |
|---|---|---|
| `ringcentral_get_account_info` | Get company/account info | `GET /restapi/v1.0/account/~` |
| `ringcentral_list_extensions` | List extensions | `GET /restapi/v1.0/account/~/extension` |
| `ringcentral_get_extension` | Get one extension's details | `GET /restapi/v1.0/account/~/extension/{extensionId}` |
| `ringcentral_list_phone_numbers` | List company + extension phone numbers | `GET /restapi/v1.0/account/~/phone-number` |
| `ringcentral_get_presence` | Get an extension's presence/DND status | `GET /restapi/v1.0/account/~/extension/{extensionId}/presence` |
| `ringcentral_list_queues` | List call queues | `GET /restapi/v1.0/account/~/call-queues` |
| `ringcentral_list_queue_members` | List a call queue's members | `GET /restapi/v1.0/account/~/call-queues/{groupId}/members` |
| `ringcentral_list_internal_contacts` | List company directory entries | `GET /restapi/v1.0/account/~/directory/entries` |
| `ringcentral_list_external_contacts` | List an extension's personal address book | `GET /restapi/v1.0/account/~/extension/{extensionId}/address-book/contact` |
| `ringcentral_list_company_call_log` | Account-wide call log | `GET /restapi/v1.0/account/~/call-log` |
| `ringcentral_list_user_call_log` | Call log for one extension | `GET /restapi/v1.0/account/~/extension/{extensionId}/call-log` |
| `ringcentral_get_call_recording` | Get a recording's metadata | `GET /restapi/v1.0/account/~/recording/{recordingId}` |
| `ringcentral_download_call_recording` | Get a recording's media metadata (size/content-type only — binary audio isn't representable as MCP tool output) | `GET /restapi/v1.0/account/~/recording/{recordingId}/content` |

## Known Gaps

- **⚠️ Not yet tested against a live RingCentral account.** All 13 tools have been checked structurally only (MCP handshake, tools-list, schema validity, `/health`, gateway 401 credential-gating). Per the parent ClickUp task, this is currently blocked at the business/procurement level — MSPbots has never purchased a RingCentral service (no paid user seat), and a JWT credential can only be bound to a real service user account, so no test credentials are available yet.
- Endpoints verified directly against RingCentral's official OpenAPI spec (`assets-developers.ringcentral.com/dpw/api-reference/specs/public/office/rc-platform.yml`, linked from the developer docs site) — not guessed.
- `ringcentral_get_call_recording`/`ringcentral_download_call_recording`: there is no standalone "list all recordings" endpoint — recording IDs must come from a call-log entry's `recording.id` field (query call logs with `recordingType`/`withRecording` params to surface them).
- "Queues" have no separate `/call-queue` resource type in RingCentral's model — they're extensions with type Department/Call Queue, exposed at the dedicated `/call-queues` paths used here.
- Scope is limited to the 13 operations above, not RingCentral's full API surface (which also includes messaging/SMS, meetings, fax, call control/RingOut, and account provisioning).

## API Reference

- [RingCentral API Reference](https://developers.ringcentral.com/api-reference)
- [JWT Auth Flow](https://developers.ringcentral.com/guide/authentication/jwt-flow)
