"""Group-related API methods for Bonsai."""
from typing import TYPE_CHECKING, Any
import logging
from http import HTTPStatus

if TYPE_CHECKING:
    from bonsai_libs.api_client.core.protocols import ApiRequestProtocol
else:
    ApiRequestProtocol = object

from .models import CreateGroupInput, GroupResponse, GroupColumnsResponse, OpHeaders

LOG = logging.getLogger(__name__)


class GroupsMixin(ApiRequestProtocol):
    """Group domain API functions."""

    def create_group(self, group: CreateGroupInput, *, headers: OpHeaders = None) -> GroupResponse:
        """Create a group in Bonsai."""

        payload = group.model_dump(mode="json")
        resp = self.request_json(
            "POST", "groups/", json=payload, headers=headers, expected_status=(HTTPStatus.CREATED,)
        )

        return GroupResponse.model_validate(resp.data)

    def get_group(self, group_id: str, *, headers: OpHeaders = None) -> GroupResponse:
        """Query the API for a group using group id."""
        resp = self.request_json(
            "GET",
            f"groups/{group_id}",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return GroupResponse.model_validate(resp.data)

    def get_groups(self, *, headers: OpHeaders = None) -> list[GroupResponse]:
        """Query the API for all groups."""
        resp = self.request_json(
            "GET",
            "groups/",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        groups = []
        if resp.data: 
            groups = resp.data.get("data", [])
        return [GroupResponse.model_validate(group) for group in groups]

    def delete_group(self, group_id: str, *, headers: OpHeaders = None) -> dict[str, Any]:
        """Delete a group."""
        resp = self.request_json(
            "DELETE",
            f"groups/{group_id}",
            headers=headers,
            expected_status=(HTTPStatus.OK, HTTPStatus.NO_CONTENT),
        )
        return resp.data or {}

    def update_group_core_info(
        self,
        group_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        headers: OpHeaders = None,
    ) -> GroupResponse:
        """Update group core information."""
        payload = {"display_name": name, "description": description}
        resp = self.request_json(
            "PUT",
            f"groups/{group_id}",
            json=payload,
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return GroupResponse.model_validate(resp.data)

    def update_group_presets(
        self,
        group_id: str,
        *,
        preset: dict[str, Any],
        set_default: bool | None = None,
        headers: OpHeaders = None,
    ) -> dict[str, Any]:
        """Update group presets."""
        url = f"groups/{group_id}/presets"
        params = {}
        if set_default is not None:
            params["default"] = set_default

        resp = self.request_json(
            "POST",
            url,
            json=preset,
            params=params if params else None,
            headers=headers,
            expected_status=(HTTPStatus.OK, HTTPStatus.CREATED),
        )
        return resp.data or {}

    def get_valid_group_columns(
        self,
        group_id: str,
        *,
        preset: str | None = None,
        include_invisible: bool | None = None,
        headers: OpHeaders = None,
    ) -> GroupColumnsResponse:
        """Get valid columns for a group."""
        params = {}
        if preset is not None:
            params["preset"] = preset
        if include_invisible is not None:
            params["include_invisible"] = include_invisible

        resp = self.request_json(
            "GET",
            f"groups/{group_id}/columns",
            params=params if params else None,
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return GroupColumnsResponse.model_validate(resp.data or {})
