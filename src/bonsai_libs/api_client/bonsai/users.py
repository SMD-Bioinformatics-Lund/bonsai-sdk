"""User-related API methods for Bonsai."""
from typing import TYPE_CHECKING, Any
import logging
from http import HTTPStatus

if TYPE_CHECKING:
    from bonsai_libs.api_client.core.protocols import ApiRequestProtocol
else:
    ApiRequestProtocol = object

from .models import CreateUserInput, UserResponse, OpHeaders

LOG = logging.getLogger(__name__)


class UsersMixin(ApiRequestProtocol):
    """User domain API calls."""

    def create_user(self, user: CreateUserInput, *, headers: OpHeaders = None) -> UserResponse:
        """Create a new Bonsai user."""
        resp = self.request_json(
            "POST",
            "users/",
            json=user.model_dump(mode="json"),
            headers=headers,
            expected_status=(HTTPStatus.CREATED,),
        )
        return UserResponse.model_validate(resp.data)

    def get_user(self, username: str, *, headers: OpHeaders = None) -> UserResponse:
        """Query the API for a user with username."""
        resp = self.request_json(
            "GET",
            f"users/{username}",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return UserResponse.model_validate(resp.data)

    def get_current_user(self, *, headers: OpHeaders = None) -> UserResponse:
        """Query the API for the current user."""
        resp = self.request_json(
            "GET",
            "users/me",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return UserResponse.model_validate(resp.data)

    def get_users(self, *, headers: OpHeaders = None) -> list[UserResponse]:
        """Query the API for all users."""
        resp = self.request_json(
            "GET",
            "users/",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        data = resp.data or []
        return [UserResponse.model_validate(user) for user in data]

    def update_user(
        self, username: str, user_data: dict[str, Any], *, headers: OpHeaders = None
    ) -> UserResponse:
        """Update user information."""
        resp = self.request_json(
            "PUT",
            f"users/{username}",
            json=user_data,
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return UserResponse.model_validate(resp.data)

    def delete_user(self, username: str, *, headers: OpHeaders = None) -> dict[str, Any]:
        """Delete a user."""
        resp = self.request_json(
            "DELETE",
            f"users/{username}",
            headers=headers,
            expected_status=(HTTPStatus.OK, HTTPStatus.NO_CONTENT),
        )
        return resp.data or {}
