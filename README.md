# ringcentral-mcp

RingCentral MCP Service — a stateless HTTP MCP server wrapping the [RingCentral REST API](https://developers.ringcentral.com/api-reference), covering account info, extensions, phone numbers, presence, call queues, contacts, and call logs/recordings.

**Tech stack:** Python 3.12 + uv + FastMCP (Starlette/Uvicorn)

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

## 授权参数说明 (Authentication headers)

Every request to `/mcp` must include the following HTTP headers:

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-RingCentral-Client-Id` | string | 是 | 无 | 无 | RingCentral App 的 Client ID(在 RingCentral 开发者后台申请的应用) | `abCdEfGhIjKlMnOpQr` |
| `X-RingCentral-Client-Secret` | string | 是 | 无 | 无 | RingCentral App 的 Client Secret | `xYz123AbC456DeF789` |
| `X-RingCentral-Jwt` | string | 是 | 无 | 无 | 绑定在某个 Service User 上的 JWT 凭据(RingCentral 后台 Roles & Permissions 生成),本服务用其换取短期 access token,从不落盘存储 | `eyJhbGciOiJSUzI1NiIs...`(一长串 JWT 字符串) |

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

| Tool | 功能 | 参数 | API |
|---|---|---|---|
| `ringcentral_get_account_info` | 获取当前账号的公司/账号基本信息 | 无 | `GET /restapi/v1.0/account/~` |
| `ringcentral_list_extensions` | 列出账号下的分机(用户/队列/部门) | `type?`, `status?`, `extension_number?`, `email?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/extension` |
| `ringcentral_get_extension` | 获取单个分机详情 | `extension_id?`(默认 `~` 即当前认证分机) | `GET /restapi/v1.0/account/~/extension/{extensionId}` |
| `ringcentral_list_phone_numbers` | 列出公司及分机号码 | `usage_type?`, `status?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/phone-number` |
| `ringcentral_get_presence` | 获取分机的在线/通话/免打扰状态 | `extension_id?`(默认 `~`) | `GET /restapi/v1.0/account/~/extension/{extensionId}/presence` |
| `ringcentral_list_queues` | 列出呼叫队列 | `page?`, `per_page?` | `GET /restapi/v1.0/account/~/call-queues` |
| `ringcentral_list_queue_members` | 列出某呼叫队列的成员 | `queue_id`(必填), `page?`, `per_page?` | `GET /restapi/v1.0/account/~/call-queues/{groupId}/members` |
| `ringcentral_list_internal_contacts` | 列出公司通讯录(内部用户) | `type?`, `site_id?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/directory/entries` |
| `ringcentral_list_external_contacts` | 列出某分机的个人通讯录联系人 | `extension_id?`(默认 `~`), `starts_with?`, `phone_number?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/extension/{extensionId}/address-book/contact` |
| `ringcentral_list_company_call_log` | 列出全公司通话记录 | `date_from?`, `date_to?`, `view?`, `direction?`, `type?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/call-log` |
| `ringcentral_list_user_call_log` | 列出单个分机的通话记录 | `extension_id?`(默认 `~`), `date_from?`, `date_to?`, `view?`, `direction?`, `page?`, `per_page?` | `GET /restapi/v1.0/account/~/extension/{extensionId}/call-log` |
| `ringcentral_get_call_recording` | 获取录音元数据(含下载用的 contentUri) | `recording_id`(必填,来自通话记录的 `recording.id`) | `GET /restapi/v1.0/account/~/recording/{recordingId}` |
| `ringcentral_download_call_recording` | 获取录音媒体的 content-type/大小(不含音频本体) | `recording_id`(必填) | `GET /restapi/v1.0/account/~/recording/{recordingId}/content` |

`page`/`per_page` on list tools: this server caps `per_page` at **200** regardless of the higher limits some RingCentral endpoints document (call-log endpoints allow up to 1000, `directory/entries` up to 2000) — 200 is the stricter of "our SOP ceiling" vs. "vendor's real max" in every case here, so 200 always governs. `per_page` is otherwise passed straight through to RingCentral's own `perPage` query parameter.

## 测试示例 (Test Example)

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
