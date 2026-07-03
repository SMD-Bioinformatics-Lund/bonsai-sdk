"""Minimal tracing interface for Bonsai jobs."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator, Protocol

if TYPE_CHECKING:
    from .logging import LoggerProtocol


class TracerProtocol(Protocol):
    """Protocol for task tracing."""

    def start_span(self, name: str, **metadata: Any) -> Any: ...


class SimpleTracer:
    """Minimal tracer that logs span lifecycle events using a logger."""

    def __init__(self, logger: LoggerProtocol | None = None) -> None:
        """Initialize tracer with optional logger."""
        self.logger = logger

    @contextmanager
    def start_span(self, name: str, **metadata: Any) -> Iterator[None]:
        """Record a span with start, end, and error events."""
        start = time.perf_counter()

        if self.logger:
            self.logger.debug(
                "span.start",
                span=name,
                **metadata,
            )

        try:
            yield
            duration = time.perf_counter() - start

            if self.logger:
                self.logger.debug(
                    "span.end",
                    span=name,
                    duration_seconds=round(duration, 6),
                    **metadata,
                )

        except Exception as exc:
            duration = time.perf_counter() - start

            if self.logger:
                self.logger.error(
                    "span.error",
                    span=name,
                    duration_seconds=round(duration, 6),
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    **metadata,
                )

            raise