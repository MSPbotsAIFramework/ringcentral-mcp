"""RingCentral telephony/contacts/call-log tools.

Tool naming convention: ringcentral_<action>_<resource>

`accountId` and `extensionId` path segments default to "~" (the current
authorized account/extension) per RingCentral's own convention, so tools
below don't expose them as parameters unless targeting a *different*
extension than the authenticated one.
"""

import json
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP

from ..api_client import RingCentralClient, RingCentralError

_NO_CREDS = (
    "Error: No RingCentral credentials configured. Set RINGCENTRAL_CLIENT_ID/"
    "RINGCENTRAL_CLIENT_SECRET/RINGCENTRAL_JWT or use AUTH_MODE=gateway."
)


def register(mcp: FastMCP, client_factory: Callable[[], RingCentralClient | None]) -> None:
    @mcp.tool()
    async def ringcentral_get_account_info() -> str:
        """Get basic company/account information for the current account.

        API: GET /restapi/v1.0/account/~
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get("/restapi/v1.0/account/~")
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_extensions(
        type: str | None = None,
        status: str | None = None,
        extension_number: str | None = None,
        email: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """List extensions on the account.

        API: GET /restapi/v1.0/account/~/extension

        Args:
            type: Filter by extension type, e.g. "User", "Department", "Announcement".
            status: Filter by status, e.g. "Enabled", "Disabled", "NotActivated".
            extension_number: Filter by extension number.
            email: Filter by email address.
            page: Page number.
            per_page: Results per page.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "type": type,
            "status": status,
            "extensionNumber": extension_number,
            "email": email,
            "page": page,
            "perPage": per_page,
        }
        try:
            result = await client.get("/restapi/v1.0/account/~/extension", params=params)
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_get_extension(extension_id: str = "~") -> str:
        """Get a single extension's details.

        API: GET /restapi/v1.0/account/~/extension/{extensionId}

        Args:
            extension_id: The extension ID, or "~" for the currently authenticated extension (default).
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(f"/restapi/v1.0/account/~/extension/{extension_id}")
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_phone_numbers(
        usage_type: str | None = None,
        status: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """List all company and extension phone numbers.

        API: GET /restapi/v1.0/account/~/phone-number

        Args:
            usage_type: Filter by usage type, e.g. "DirectNumber", "CompanyNumber".
            status: Filter by status, e.g. "Normal", "Reserved".
            page: Page number.
            per_page: Results per page.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {"usageType": usage_type, "status": status, "page": page, "perPage": per_page}
        try:
            result = await client.get("/restapi/v1.0/account/~/phone-number", params=params)
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_get_presence(extension_id: str = "~") -> str:
        """Get an extension's presence/telephony/do-not-disturb status.

        API: GET /restapi/v1.0/account/~/extension/{extensionId}/presence

        Args:
            extension_id: The extension ID, or "~" for the currently authenticated extension (default).
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(f"/restapi/v1.0/account/~/extension/{extension_id}/presence")
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_queues(page: int | None = None, per_page: int | None = None) -> str:
        """List call queues on the account.

        API: GET /restapi/v1.0/account/~/call-queues

        Args:
            page: Page number.
            per_page: Results per page.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(
                "/restapi/v1.0/account/~/call-queues", params={"page": page, "perPage": per_page}
            )
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_queue_members(
        queue_id: str, page: int | None = None, per_page: int | None = None
    ) -> str:
        """List the members of a call queue.

        API: GET /restapi/v1.0/account/~/call-queues/{groupId}/members

        Args:
            queue_id: Required. The call queue's extension ID.
            page: Page number.
            per_page: Results per page.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/call-queues/{queue_id}/members",
                params={"page": page, "perPage": per_page},
            )
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_internal_contacts(
        type: str | None = None,
        site_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """List internal company directory entries (corporate users/extensions).

        API: GET /restapi/v1.0/account/~/directory/entries

        Args:
            type: Filter by directory entry type.
            site_id: Filter by site ID (for multi-site accounts).
            page: Page number.
            per_page: Results per page.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {"type": type, "siteId": site_id, "page": page, "perPage": per_page}
        try:
            result = await client.get("/restapi/v1.0/account/~/directory/entries", params=params)
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_external_contacts(
        extension_id: str = "~",
        starts_with: str | None = None,
        phone_number: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """List an extension's personal address-book contacts.

        API: GET /restapi/v1.0/account/~/extension/{extensionId}/address-book/contact

        Args:
            extension_id: The extension ID, or "~" for the currently authenticated extension (default).
            starts_with: Filter to contacts whose name starts with this string.
            phone_number: Filter by phone number.
            page: Page number.
            per_page: Results per page.
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {"startsWith": starts_with, "phoneNumber": phone_number, "page": page, "perPage": per_page}
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/extension/{extension_id}/address-book/contact", params=params
            )
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_company_call_log(
        date_from: str | None = None,
        date_to: str | None = None,
        view: str | None = None,
        direction: str | None = None,
        type: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """List account-wide call log records.

        API: GET /restapi/v1.0/account/~/call-log

        Args:
            date_from: ISO 8601 start of the date range.
            date_to: ISO 8601 end of the date range.
            view: "Simple" or "Detailed".
            direction: "Inbound" or "Outbound".
            type: Call type, e.g. "Voice", "Fax".
            page: Page number.
            per_page: Results per page (max 1000).
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "view": view,
            "direction": direction,
            "type": type,
            "page": page,
            "perPage": per_page,
        }
        try:
            result = await client.get("/restapi/v1.0/account/~/call-log", params=params)
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_list_user_call_log(
        extension_id: str = "~",
        date_from: str | None = None,
        date_to: str | None = None,
        view: str | None = None,
        direction: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """List call log records for a specific extension/user.

        API: GET /restapi/v1.0/account/~/extension/{extensionId}/call-log

        Args:
            extension_id: The extension ID, or "~" for the currently authenticated extension (default).
            date_from: ISO 8601 start of the date range.
            date_to: ISO 8601 end of the date range.
            view: "Simple" or "Detailed".
            direction: "Inbound" or "Outbound".
            page: Page number.
            per_page: Results per page (max 1000).
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "view": view,
            "direction": direction,
            "page": page,
            "perPage": per_page,
        }
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/extension/{extension_id}/call-log", params=params
            )
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_get_call_recording(recording_id: str) -> str:
        """Get a call recording's metadata (returns a content URI, not the audio itself).

        API: GET /restapi/v1.0/account/~/recording/{recordingId}

        Args:
            recording_id: Required. The recording ID (from a call-log entry's `recording.id` field).
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(f"/restapi/v1.0/account/~/recording/{recording_id}")
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def ringcentral_download_call_recording(recording_id: str) -> str:
        """Download a call recording's media content (returns metadata about the
        binary — content type and size — not the raw audio bytes, which aren't
        representable as MCP tool output).

        API: GET /restapi/v1.0/account/~/recording/{recordingId}/content
        (served from the media.ringcentral.com host, not the platform API host)

        Args:
            recording_id: Required. The recording ID (from a call-log entry's `recording.id` field).
        """
        client = client_factory()
        if client is None:
            return _NO_CREDS
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/recording/{recording_id}/content", media=True
            )
            return json.dumps(result, indent=2)
        except RingCentralError as e:
            return f"Error: {e}"
