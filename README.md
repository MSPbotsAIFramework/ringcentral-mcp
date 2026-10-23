# ringcentral-mcp

RingCentral MCP Service — a stateless HTTP MCP server wrapping the [RingCentral REST API](https://developers.ringcentral.com/api-reference), covering account info, extensions, phone numbers, presence, call queues, contacts, and call logs/recordings.

**Tech stack:** Python 3.12 + uv + FastMCP (Starlette/Uvicorn)

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## What is RingCentral / when would an agent use this

RingCentral is a cloud phone / UCaaS (telephony) platform MSPs use to manage a customer's business phone system — extensions, phone numbers, presence, call queues, directory/personal contacts, and call history. An agent should reach for this MCP for requests like:

- "Who has extension 101 / what extensions exist?" → `ringcentral_list_extensions`, `ringcentral_get_extension`
- "Is this person available / on a call right now?" → `ringcentral_get_presence`
- "Which numbers are provisioned for this account?" → `ringcentral_list_phone_numbers`
- "Who staffs the support call queue?" → `ringcentral_list_queues`, then `ringcentral_list_queue_members`
- "Show recent inbound calls for extension X" / "get that call's recording" → `ringcentral_list_user_call_log` / `ringcentral_list_company_call_log`, then `ringcentral_get_call_recording` using the call log entry's `recording.id`

It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication. All 13 tools are read-only.

## Authentication

RingCentral's REST API uses the **JWT bearer flow** — a server-to-server grant with no user browser redirect. A JWT credential is generated in the RingCentral admin console for a dedicated "service user" (Roles & Permissions → the service user's JWT credential), then exchanged for a short-lived access token:

```
POST https://platform.ringcentral.com/restapi/oauth/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=<jwt>
```

A fresh access token is cheap to obtain and this service must stay stateless, so it re-authenticates on every call rather than caching/refreshing a token — no derived token is ever cached across requests (SOP §3.4).

**Credentials are read from HTTP headers only, on every request — never from environment variables.** There is no local/single-tenant fallback mode; this keeps one tenant's credentials from ever leaking into another tenant's request.

## Authentication headers

Every request to `/mcp` must include the following HTTP headers:

| Header | Type | Required | Default | Allowed values | Description | Example |
|---|---|---|---|---|---|---|
| `X-RingCentral-Client-Id` | string | Yes | None | None | Client ID of the RingCentral App (an app registered in the RingCentral developer console) | `abCdEfGhIjKlMnOpQr` |
| `X-RingCentral-Client-Secret` | string | Yes | None | None | Client Secret of the RingCentral App | `xYz123AbC456DeF789` |
| `X-RingCentral-Jwt` | string | Yes | None | None | JWT credential bound to a Service User (generated under Roles & Permissions in the RingCentral admin console); this service exchanges it for a short-lived access token and never stores it on disk | `eyJhbGciOiJSUzI1NiIs...`(a long JWT string) |

Missing any of the three headers returns `401 Unauthorized` with a `required_headers` list in the body.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m ringcentral_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

No credentials are required for the health endpoint (it is a pure local liveness probe and never calls the RingCentral API).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |

No credential fields exist in configuration — see Authentication above.

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP)
- Headers: `X-RingCentral-Client-Id`, `X-RingCentral-Client-Secret`, `X-RingCentral-Jwt` (all required)

## Available Tools (13)

| Tool | Description | Parameters | API |
|---|---|---|---|
| `ringcentral_get_account_info` | Get basic company/account information for the current account | None | `GET /restapi/v1.0/account/~` |
| `ringcentral_list_extensions` | List the extensions under the account (users/queues/departments) | `type?`, `status?`, `extension_number?`, `email?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/extension` |
| `ringcentral_get_extension` | Get a single extension's details | `extension_id?`(default `~`, the currently authenticated extension) | `GET /restapi/v1.0/account/~/extension/{extensionId}` |
| `ringcentral_list_phone_numbers` | List company and extension phone numbers | `usage_type?`, `status?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/phone-number` |
| `ringcentral_get_presence` | Get an extension's online/on-call/do-not-disturb status | `extension_id?`(default `~`) | `GET /restapi/v1.0/account/~/extension/{extensionId}/presence` |
| `ringcentral_list_queues` | List call queues | `page?`, `per_page?` | `GET /restapi/v1.0/account/~/call-queues` |
| `ringcentral_list_queue_members` | List the members of a call queue | `queue_id`(required), `page?`, `per_page?` | `GET /restapi/v1.0/account/~/call-queues/{groupId}/members` |
| `ringcentral_list_internal_contacts` | List the company directory (internal users) | `type?`, `site_id?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/directory/entries` |
| `ringcentral_list_external_contacts` | List the personal address book contacts of an extension | `extension_id?`(default `~`), `starts_with?`, `phone_number?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/extension/{extensionId}/address-book/contact` |
| `ringcentral_list_company_call_log` | List the company-wide call log | `date_from?`, `date_to?`, `view?`, `direction?`, `type?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/call-log` |
| `ringcentral_list_user_call_log` | List a single extension's call log | `extension_id?`(default `~`), `date_from?`, `date_to?`, `view?`, `direction?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/extension/{extensionId}/call-log` |
| `ringcentral_get_call_recording` | Get recording metadata (including the contentUri used for download) | `recording_id`(required, from `recording.id` in the call log) | `GET /restapi/v1.0/account/~/recording/{recordingId}` |
| `ringcentral_download_call_recording` | Get the recording media's content-type/size (without the audio itself) | `recording_id`(required) | `GET /restapi/v1.0/account/~/recording/{recordingId}/content` |

`page`/`per_page` on list tools: this server caps `per_page` at **200** regardless of the higher limits some RingCentral endpoints document (call-log endpoints allow up to 1000, `directory/entries` up to 2000) — 200 is the stricter of "our SOP ceiling" vs. "vendor's real max" in every case here, so 200 always governs. `per_page` is otherwise passed straight through to RingCentral's own `perPage` query parameter.

## Test Example

```json
{
  "method": "tools/call",
  "params": { "name": "ringcentral_list_extensions", "arguments": {} }
}
```

Equivalent `curl` against the running server (streamable HTTP MCP endpoint):

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-RingCentral-Client-Id: <client_id>" \
  -H "X-RingCentral-Client-Secret: <client_secret>" \
  -H "X-RingCentral-Jwt: <jwt>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "ringcentral_list_extensions", "arguments": {} }
  }'
```

## API Reference

- [RingCentral API Reference](https://developers.ringcentral.com/api-reference)
- [JWT Auth Flow](https://developers.ringcentral.com/guide/authentication/jwt-flow)
- Per-page limits verified against RingCentral's own OpenAPI spec (`assets-developers.ringcentral.com/dpw/api-reference/specs/public/office/rc-platform.yml`): the generic `perPage` parameter (extensions, phone numbers, queues, queue members, contacts) has no documented maximum; call-log endpoints document a documented max of 1000; `directory/entries` documents a max of 2000. This server's own 200 hard cap is stricter than all of these, so it is always the binding limit.

## Known Gaps / Implementation Notes

- **⚠️ Not yet tested against a live RingCentral account.** All 13 tools have been checked structurally only (MCP handshake, tools-list, schema validity, `/health`, gateway 401 credential-gating). Per the parent ClickUp task, this is currently blocked at the business/procurement level — MSPbots has never purchased a RingCentral service (no paid user seat), and a JWT credential can only be bound to a real service user account, so no test credentials are available yet.
- Endpoints verified directly against RingCentral's official OpenAPI spec — not guessed.
- `ringcentral_get_call_recording`/`ringcentral_download_call_recording`: there is no standalone "list all recordings" endpoint — recording IDs must come from a call-log entry's `recording.id` field (query call logs with `recordingType`/`withRecording` params to surface them). `ringcentral_download_call_recording` cannot return actual audio bytes (not representable as MCP tool text output) — it returns content-type/size only; use `ringcentral_get_call_recording`'s `contentUri` field for an actual download URL.
- "Queues" have no separate `/call-queue` resource type in RingCentral's model — they're extensions with type Department/Call Queue, exposed at the dedicated `/call-queues` paths used here.
- Scope is limited to the 13 operations above, not RingCentral's full API surface (which also includes messaging/SMS, meetings, fax, call control/RingOut, and account provisioning).
- This server only runs in HTTP/gateway mode (no stdio transport, no single-tenant env-var credential mode) — the SOP requires credentials to come exclusively from per-request headers, so a code path that reads them from the environment instead was removed rather than kept as a "local dev convenience."
