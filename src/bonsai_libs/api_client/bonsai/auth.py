"""Authentication-related API methods for Bonsai."""
from http import HTTPStatus
import logging

from bonsai_libs.api_client.core.auth import BearerTokenAuth
from bonsai_libs.api_client.core.exceptions import ClientError, UnauthorizedError

from bonsai_libs.api_client.core.base import BaseClient

from .models import OpHeaders

LOG = logging.getLogger(__name__)


class AuthMixin(BaseClient):
    """Authenticate users useing the Bonsai API."""

    def authenticate_user(self, username: str, password: str, *, headers: OpHeaders = None) -> bool:
        """Authenticate using username/password and configure bearer token.

        Returns True if login was successful.
        """
        try:
            resp = self.request_form(
                "POST",
                "token",
                data={"username": username, "password": password},
                headers=headers,
                expected_status=(HTTPStatus.OK,),
            )
        except UnauthorizedError:
            LOG.error("Invalid login credentials for user=%s", username)
            return False
        except ClientError as exc:
            LOG.error(
                "Something went wrong when authenticating user %s; %s",
                username,
                exc,
            )
            raise

        data = resp.data or {}
        token_type = str(data.get("token_type", "")).lower()
        access_token = data.get("access_token")

        if token_type == "bearer" and access_token:
            self.auth = BearerTokenAuth(token=access_token)
            return True

        LOG.error("Unexpected token response: %s", resp)
        return False
