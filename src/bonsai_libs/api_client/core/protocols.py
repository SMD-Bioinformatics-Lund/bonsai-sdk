
from collections.abc import Iterable
from typing import Any, Protocol
from http import HTTPStatus

from .models import RequestMethods

class ApiRequestProtocol(Protocol):
    """API request protocol."""

    def request_json(
        self,
        method: RequestMethods,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        expected_status: Iterable[int | HTTPStatus] = (HTTPStatus.OK,),
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> "ApiResponse[Any]":
        """Make a API request passing json info."""
