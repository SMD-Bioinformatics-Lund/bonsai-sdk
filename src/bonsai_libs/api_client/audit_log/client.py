"""Audit log client."""

import datetime as dt
import logging
from http import HTTPStatus

from pydantic import ValidationError

from bonsai_libs.api_client.core.base import BaseClient
from bonsai_libs.api_client.core.exceptions import ApiError

from .models import EventCreate, EventResponse, PaginatedEventsOut

LOG = logging.getLogger(__name__)


class AuditLogClient(BaseClient):
    """Log and retrieve events from the Audit Log service."""

    def post_event(self, event: EventCreate) -> EventResponse:
        """Record a new event to the event log."""
        payload = event.model_dump(mode="json", by_alias=True, exclude_none=True)
        try:
            resp = self.post("events", json=payload, expected_status=(HTTPStatus.ACCEPTED,))
            return EventResponse.model_validate(resp.data)
        except ApiError as err:
            LOG.error("Audit Log Error: %s", err)
            raise
        except ValidationError as err:
            LOG.error("Audit Log Error: %s", err)
            raise ApiError(f"Internal api error - {err}") from err

    def get_events(
        self,
        limit: int = 50,
        skip: int = 0,
        source_service: list[str] | None = None,
        occurred_after: dt.datetime | None = None,
        occurred_before: dt.datetime | None = None,
    ):
        """Get multiple events."""
        params: dict[str, int | dt.datetime | list[str]] = {
            "limit": limit,
            "skip": skip,
        }
        if source_service:
            params["source_service"] = source_service
        if occurred_after:
            params["occurred_after"] = occurred_after
        if occurred_before:
            params["occurred_before"] = occurred_before

        try:
            resp = self.get("events", params=params, expected_status=(HTTPStatus.OK,))
            return PaginatedEventsOut.model_validate(resp.data)
        except ApiError as err:
            LOG.error("Audit Log Error: %s", err)
            raise
        except ValidationError as err:
            LOG.error("Audit Log Error: %s", err)
            raise ApiError(f"Internal api error - {err}") from err
