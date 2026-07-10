"""Functions related to setting result envelopes and their content."""

from logging import Logger
from typing import Any, Callable, TypeVar

from bonsai_libs.parse.exceptions import AbsentResultError, ParserError
from bonsai_libs.parse.models.enums import ResultStatus

PredicateFn = Callable[[Any], bool]

T = TypeVar("T")


def default_empty_predicate(value: Any) -> bool:
    """Generic tester if result is empty."""
    if value is None:
        return True
    if value in ["", [], {}]:
        return True
    return False


def envelope_from_value(
    value: Any,
    *,
    empty_predicate: PredicateFn = default_empty_predicate,
    reason: str | None = None,
    meta: dict[str, Any] | None = None,
) -> "ResultEnvelope":
    """Create a PARSED/ EMPTY envelope based on the provided result."""

    status = ResultStatus.EMPTY if empty_predicate(value) else ResultStatus.PARSED
    from bonsai_libs.parse.models.base import ResultEnvelope
    return ResultEnvelope(status=status, value=value, reason=reason, meta=meta or {})


def envelope_error(
    reason: str, *, meta: dict[str, Any] | None = None
) -> "ResultEnvelope":
    """Create an envelope that signifies that an error occured."""
    from bonsai_libs.parse.models.base import ResultEnvelope
    return ResultEnvelope(status=ResultStatus.ERROR, reason=reason, meta=meta or {})


def envelope_absent(
    reason: str, *, meta: dict[str, Any] | None = None
) -> "ResultEnvelope":
    """Create an envelope that for result being absent in the input file."""
    from bonsai_libs.parse.models.base import ResultEnvelope
    return ResultEnvelope(status=ResultStatus.ABSENT, reason=reason, meta=meta or {})


def envelope_skipped(
    reason: str = "Omitted by user", *, meta: dict[str, Any] | None = None
) -> "ResultEnvelope":
    """Create an envelope that signifies that the result was skipped by the user."""
    from bonsai_libs.parse.models.base import ResultEnvelope
    return ResultEnvelope(status=ResultStatus.SKIPPED, reason=reason, meta=meta or {})


def run_as_envelope(
    analysis_name: str,
    fn: Callable[[], T],
    *,
    empty_predicate: PredicateFn = default_empty_predicate,
    absent_predicate: PredicateFn | None = None,
    reason_if_absent: str | None = None,
    reason_if_empty: str | None = None,
    meta: dict[str, Any] | None = None,
    logger: Logger | None = None,
) -> "ResultEnvelope":
    """Execute a parser function and wrap it in a ResultEnvelope."""
    base_meta = {**(meta or {}), "step": analysis_name}
    try:
        value = fn()
    except AbsentResultError as exc:
        if logger:
            logger.info(
                "result absent", extra={"context": {**base_meta, "error": str(exc)}}
            )
        return envelope_absent(reason=reason_if_absent or str(exc), meta=base_meta)

    except ParserError as exc:
        if logger:
            logger.error(
                "Parser error",
                extra={
                    "context": {
                        **base_meta,
                        **getattr(exc, "context", {}),
                        "error": str(exc),
                    }
                },
            )

    except Exception as exc:
        if logger:
            logger.exception(
                "Step failed", extra={"context": {**base_meta, "error": str(exc)}}
            )
        err_meta = {**base_meta, "exception": type(exc).__name__}
        return envelope_error(reason=str(exc), meta=err_meta)

    # Optional: Custom absent predicate
    if absent_predicate is not None and absent_predicate(value):
        return envelope_absent(
            reason=reason_if_absent or "Not present",
            meta={**(meta or {}), "step": analysis_name},
        )

    # Normal PARSED/ EMPTY resolution
    status = ResultStatus.PARSED
    reason = None
    if empty_predicate(value):
        status = ResultStatus.EMPTY
        reason = reason_if_empty or None

    from bonsai_libs.parse.models.base import ResultEnvelope
    return ResultEnvelope(status=status, value=value, reason=reason, meta=base_meta)
