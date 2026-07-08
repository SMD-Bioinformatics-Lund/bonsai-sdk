"""Helper functions for file I/O operations."""

import io
import os
from pathlib import Path
from typing import IO

from pydantic import ValidationInfo

from bonsai_libs.parse.io.types import StreamOrPath


def ensure_text_stream(
    source: StreamOrPath,
    *,
    encoding: str = "utf-8",
    newline: str = "",
) -> IO[str]:
    """
    Normalize input to a text stream (IO[str]) using given encoding & newline policy.

    Accepts:
      - path-like (str/Path)
      - raw bytes/bytearray
      - text stream (IO[str]) -> returned as-is
      - binary stream (IO[bytes]) -> wrapped in TextIOWrapper
      - duck-typed .read() objects (best-effort)
    """
    # Path-like
    if isinstance(source, (str, Path)):
        # open with newline="" for CSV correctness across platforms
        return open(os.fspath(source), "r", encoding=encoding, newline=newline)

    # Already a text stream
    if isinstance(source, io.TextIOBase):
        return source

    # Raw bytes -> wrap into BytesIO -> TextIOWrapper
    if isinstance(source, (bytes, bytearray)):
        return io.TextIOWrapper(io.BytesIO(source), encoding=encoding, newline=newline)

    # Binary streams
    if isinstance(source, (io.BufferedIOBase, io.RawIOBase)):
        return io.TextIOWrapper(source, encoding=encoding, newline=newline)

    # Duck-typed file-like
    read = getattr(source, "read", None)
    if callable(read):
        # Try safe zero-byte read to detect binary vs text
        try:
            sample = source.read(0)  # may be '' or b''; must not advance position
        except Exception:
            # If we can't probe, assume text-like
            return source  # type: ignore[return-value]

        if isinstance(sample, (bytes, bytearray)):
            return io.TextIOWrapper(
                source, encoding=encoding, newline=newline
            )  # type: ignore[arg-type]
        return source  # type: ignore[return-value]

    raise TypeError(f"Unsupported StreamOrPath type: {type(source)!r}")


def convert_rel_to_abs_path(path: str, validation_info: ValidationInfo) -> Path:
    """Validate that file exist and resolve realtive directories.

    if a path is relative, convert to absolute from the configs parent directory
    i.e.  prp_path = ./results/sample_name.json --> /path/to/sample_name.json
          given, cnf_path = /data/samples/cnf.yml
    relative paths are used when bootstraping a test database
    """
    # convert relative path to absolute
    upd_path = Path(path)
    if not upd_path.is_absolute():
        # check if config file path is provided as the model context
        if validation_info.context is None:
            raise ValueError("No context defined for model.")
        upd_path = Path(validation_info.context).parent / upd_path

    assert upd_path.is_file(), f"Invalid path: {upd_path}"
    return upd_path
