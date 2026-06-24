from collections.abc import Iterable
from http import HTTPStatus
from typing import Any, Protocol

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

    def request_form(
        self,
        method: RequestMethods,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        expected_status: Iterable[int] = (HTTPStatus.OK,),
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> "ApiResponse[Any]":
        """Make a form data API requests."""

    def request_multipart(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        expected_status: Iterable[int] = (HTTPStatus.OK,),
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> "ApiResponse[Any]":
        """Multi-part API requests."""
