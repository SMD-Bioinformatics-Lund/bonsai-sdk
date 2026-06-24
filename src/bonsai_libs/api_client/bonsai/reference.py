"""Reference-data-related API methods for Bonsai."""
from typing import TYPE_CHECKING, Any
import logging
from http import HTTPStatus

if TYPE_CHECKING:
    from bonsai_libs.api_client.core.protocols import ApiRequestProtocol
else:
    ApiRequestProtocol = object

from .models import OpHeaders

LOG = logging.getLogger(__name__)


class ReferenceMixin(ApiRequestProtocol):
    """Reference domain API routes."""

    def get_antibiotics(self, *, headers: OpHeaders = None) -> list[dict[str, Any]]:
        """Get list of available antibiotics."""
        resp = self.request_json(
            "GET",
            "reference/antibiotics",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        data = resp.data or []
        return data if isinstance(data, list) else []

    def get_variant_rejection_reasons(self, *, headers: OpHeaders = None) -> list[dict[str, Any]]:
        """Get list of valid variant rejection reasons."""
        resp = self.request_json(
            "GET",
            "reference/variant-rejection",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        data = resp.data or []
        return data if isinstance(data, list) else []
