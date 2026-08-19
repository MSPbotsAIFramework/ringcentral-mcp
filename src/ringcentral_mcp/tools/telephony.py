"""RingCentral telephony/contacts/call-log tools.

Tool naming convention: ringcentral_<action>_<resource>

`accountId` and `extensionId` path segments default to "~" (the current
authorized account/extension) per RingCentral's own convention, so tools
below don't expose them as parameters unless targeting a *different*
extension than the authenticated one.
"""

from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import RingCentralClient, RingCentralError
from ._common import NO_TOKEN, clamp_per_page

_RO_IDEMPOTENT = ToolAnnotations(readOnlyHint=True, idempotentHint=True)

_PAGE_DESC = "Page number to retrieve (1-based)."
_PER_PAGE_DESC = "Results per page (vendor default ~100; this server caps it at 200)."


def register(mcp: FastMCP, client_factory: Callable[[], RingCentralClient | None]) -> None:
    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_get_account_info() -> str:
        """Get basic company/account information for the current account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get("/restapi/v1.0/account/~")
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_extensions(
        type: Annotated[
            str | None,
            Field(description='Extension type, e.g. "User", "Department", "Announcement".'),
        ] = None,
        status: Annotated[
            str | None,
            Field(description='Extension status, e.g. "Enabled", "Disabled", "NotActivated".'),
        ] = None,
        extension_number: Annotated[
            str | None, Field(description="Extension short number.")
        ] = None,
        email: Annotated[str | None, Field(description="Extension email address.")] = None,
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List extensions (users, queues, departments) on the account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "type": type,
            "status": status,
            "extensionNumber": extension_number,
            "email": email,
            "page": page,
            "perPage": clamp_per_page(per_page),
        }
        try:
            result = await client.get("/restapi/v1.0/account/~/extension", params=params)
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_get_extension(
        extension_id: Annotated[
            str, Field(description='Extension ID, or "~" for the authenticated extension.')
        ] = "~",
    ) -> str:
        """Get a single extension's details."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(f"/restapi/v1.0/account/~/extension/{extension_id}")
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_phone_numbers(
        usage_type: Annotated[
            str | None,
            Field(description='Usage type filter, e.g. "DirectNumber", "CompanyNumber".'),
        ] = None,
        status: Annotated[
            str | None, Field(description='Status filter, e.g. "Normal", "Reserved".')
        ] = None,
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List company and extension phone numbers on the account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "usageType": usage_type,
            "status": status,
            "page": page,
            "perPage": clamp_per_page(per_page),
        }
        try:
            result = await client.get("/restapi/v1.0/account/~/phone-number", params=params)
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_get_presence(
        extension_id: Annotated[
            str, Field(description='Extension ID, or "~" for the authenticated extension.')
        ] = "~",
    ) -> str:
        """Get an extension's presence, telephony, and do-not-disturb status."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(f"/restapi/v1.0/account/~/extension/{extension_id}/presence")
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_queues(
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List call queues on the account."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                "/restapi/v1.0/account/~/call-queues",
                params={"page": page, "perPage": clamp_per_page(per_page)},
            )
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_queue_members(
        queue_id: Annotated[str, Field(description="The call queue's extension ID.")],
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List the members of a call queue."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/call-queues/{queue_id}/members",
                params={"page": page, "perPage": clamp_per_page(per_page)},
            )
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_internal_contacts(
        type: Annotated[str | None, Field(description="Filter by directory entry type.")] = None,
        site_id: Annotated[
            str | None, Field(description="Filter by business site ID (multi-site accounts).")
        ] = None,
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List internal company directory entries (corporate users/extensions)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "type": type,
            "siteId": site_id,
            "page": page,
            "perPage": clamp_per_page(per_page),
        }
        try:
            result = await client.get("/restapi/v1.0/account/~/directory/entries", params=params)
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_external_contacts(
        extension_id: Annotated[
            str, Field(description='Extension ID, or "~" for the authenticated extension.')
        ] = "~",
        starts_with: Annotated[
            str | None, Field(description="Filter to contacts whose name starts with this string.")
        ] = None,
        phone_number: Annotated[str | None, Field(description="Filter by phone number.")] = None,
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List an extension's personal address-book contacts."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "startsWith": starts_with,
            "phoneNumber": phone_number,
            "page": page,
            "perPage": clamp_per_page(per_page),
        }
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/extension/{extension_id}/address-book/contact",
                params=params,
            )
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_company_call_log(
        date_from: Annotated[
            str | None, Field(description="ISO 8601 start of the date range.")
        ] = None,
        date_to: Annotated[str | None, Field(description="ISO 8601 end of the date range.")] = None,
        view: Annotated[str | None, Field(description='"Simple" or "Detailed".')] = None,
        direction: Annotated[str | None, Field(description='"Inbound" or "Outbound".')] = None,
        type: Annotated[str | None, Field(description='Call type, e.g. "Voice", "Fax".')] = None,
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List account-wide call log records."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "view": view,
            "direction": direction,
            "type": type,
            "page": page,
            "perPage": clamp_per_page(per_page),
        }
        try:
            result = await client.get("/restapi/v1.0/account/~/call-log", params=params)
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_list_user_call_log(
        extension_id: Annotated[
            str, Field(description='Extension ID, or "~" for the authenticated extension.')
        ] = "~",
        date_from: Annotated[
            str | None, Field(description="ISO 8601 start of the date range.")
        ] = None,
        date_to: Annotated[str | None, Field(description="ISO 8601 end of the date range.")] = None,
        view: Annotated[str | None, Field(description='"Simple" or "Detailed".')] = None,
        direction: Annotated[str | None, Field(description='"Inbound" or "Outbound".')] = None,
        page: Annotated[int | None, Field(description=_PAGE_DESC)] = None,
        per_page: Annotated[int | None, Field(description=_PER_PAGE_DESC)] = None,
    ) -> str:
        """List call log records for a specific extension/user."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "view": view,
            "direction": direction,
            "page": page,
            "perPage": clamp_per_page(per_page),
        }
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/extension/{extension_id}/call-log", params=params
            )
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_get_call_recording(
        recording_id: Annotated[
            str, Field(description="The recording ID, from a call-log entry's recording.id field.")
        ],
    ) -> str:
        """Get a call recording's metadata, including its downloadable content URI."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(f"/restapi/v1.0/account/~/recording/{recording_id}")
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()

    @mcp.tool(annotations=_RO_IDEMPOTENT)
    async def ringcentral_download_call_recording(
        recording_id: Annotated[
            str, Field(description="The recording ID, from a call-log entry's recording.id field.")
        ],
    ) -> str:
        """Check a call recording's media content type and size (not the audio itself).

        Binary audio bytes cannot be represented as MCP tool text output; use
        ringcentral_get_call_recording's contentUri for an actual download.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        try:
            result = await client.get(
                f"/restapi/v1.0/account/~/recording/{recording_id}/content", media=True
            )
            return dump_json_capped(result)
        except RingCentralError as e:
            return e.to_envelope()
