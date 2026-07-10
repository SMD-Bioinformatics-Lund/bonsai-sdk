"""Functions for reading delimited files and validating its content."""

import csv
import logging
import re
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence

from .types import DelimiterRow, FieldValidationResult, StreamOrPath
from .utils import ensure_text_stream

_NULLISH = [None, "", " ", "NA", "N/A", "na", "n/a", ".", "-", "ND", "none"]
_TRAILING_ANNOT_RE = re.compile(r"\s*(\([^)]*\)|\[[^\]]*\])\s*$")

LOG = logging.getLogger(__name__)

KeyFn = Callable[[str], str]
ValFn = Callable[[Any], Any]


def read_delimited(
    source: StreamOrPath,
    *,
    delimiter: str = "\t",
    encoding: str = "utf-8",
    has_header: bool = True,
    fieldnames: Sequence[str] | None = None,
    none_values: set[str] | None = None,
    skip_blank_lines: bool = True,
) -> Iterator[DelimiterRow]:
    """
    Read a delimited text file (TSV/CSV) and yield each row as a dict.

    Supports:
      - path-like (str/Path)
      - text streams (IO[str])
      - binary streams (IO[bytes]) e.g. FastAPI UploadFile.file

    Returns raw string values as produced by csv.DictReader.
    """
    if not has_header and fieldnames is None:
        raise ValueError("fieldnames must be provided when has_header=False")

    if isinstance(source, (str, Path)):
        with open(source, "r", encoding=encoding, newline="") as fp:
            yield from read_delimited(
                fp,
                delimiter=delimiter,
                encoding=encoding,
                has_header=has_header,
                fieldnames=fieldnames,
                none_values=none_values,
                skip_blank_lines=skip_blank_lines,
            )
        return

    text_stream = ensure_text_stream(source, encoding=encoding)
    # If has_header=False, DictReader will treat the first row as data
    # and use provided fieldnames.
    # If has_header=True and fieldnames=None,
    # DictReader reads header from first row.
    reader = csv.DictReader(text_stream, delimiter=delimiter, fieldnames=fieldnames)

    # If has_header=True AND fieldnames was provided,
    # DictReader will NOT consume header.
    if has_header and fieldnames is not None:
        # Consume one row (the header row) and discard
        next(reader, None)

    none_values = none_values or []

    for row in reader:
        # DictReader may return None keys on malformed rows; ignore those safely
        if None in row:
            row.pop(None, None)

        # Optionally skip blank/empty rows
        if skip_blank_lines and (
            not row or all((v is None or str(v).strip() == "") for v in row.values())
        ):
            continue

        cleaned: dict[str, str | None] = {}
        for key, val in row.items():
            if val is None:
                cleaned[key] = None
                continue
            val = val.strip()
            cleaned[key] = None if val in none_values else val
        yield cleaned


def is_nullish(value: Any, null_values: set[str] | None = None) -> bool:
    """Check if value is a null value."""
    null_values = null_values or set(_NULLISH)
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in null_values:
        return True
    return False


def normalize_nulls(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert empty strings to None and preserve other values."""
    out: dict[str, Any] = {}
    for key, val in row.items():
        if is_nullish(val):
            out[key] = None
        else:
            out[key] = val
    return out


def validate_fields(
    row: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
    strict: bool = False,
) -> FieldValidationResult:
    """Validate fields that mandatory fields are present in the data."""
    cols = set(row.keys())
    optional = optional or set()

    missing = required - cols
    allowed = required | optional
    extra = (cols - allowed) if strict else set()

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}; got: {sorted(cols)}"
        )
    if strict and extra:
        raise ValueError(f"Unexpected extra columns: {sorted(extra)}")

    return FieldValidationResult(missing=set(), extra=extra)


def canonical_header(header: str) -> str:
    """
    Remove trailing comment-like blocks: ' (...)' and/or ' [...]' at end of header.
    Repeats removal to handle headers with both (...) and [...] suffixes.
    """
    h = header.strip()
    while True:
        new = _TRAILING_ANNOT_RE.sub("", h).strip()
        if new == h:
            return h
        h = new


def normalize_row(
    row: Mapping[str, Any],
    *,
    key_fn: KeyFn | None = None,
    val_fn: ValFn | None = None,
    column_map: Mapping[str, str] | None = None,
    drop: set[str] | None = None,
    keep_unmapped: bool = True,
    on_collision: str = "last",  # "last" | "raise"
) -> dict[str, Any]:
    """
    Generic row normalization:
    - drop unwanted columns
    - normalize keys (canonicalize headers)
    - normalize values (nullish->None etc.)
    - optionally rename keys via column_map
    """
    key_fn = key_fn or (lambda s: s)
    val_fn = val_fn or (lambda v: v)
    column_map = column_map or {}
    drop = drop or set()

    out: dict[str, Any] = {}
    for k, v in row.items():
        if k in drop:
            continue

        nk = key_fn(k)
        nk = column_map.get(nk, nk)

        if not keep_unmapped and nk not in column_map.values():
            continue

        nv = val_fn(v)

        if on_collision == "raise" and nk in out and out[nk] != nv:
            raise ValueError(f"Key collision after normalization: {k!r} -> {nk!r}")
        out[nk] = nv

    return out
