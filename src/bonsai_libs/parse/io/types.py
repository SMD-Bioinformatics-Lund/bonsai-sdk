"""Shared IO types."""

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import BinaryIO, TextIO, TypeAlias

# Path-ish types that are commonly accepted by open()
Pathish: TypeAlias = str | Path | PathLike[str]

StreamOrPath: TypeAlias = TextIO | BinaryIO | Pathish

DelimiterRow: TypeAlias = dict[str, str | None]

DelimiterRows: TypeAlias = list[DelimiterRow]


@dataclass(frozen=True)
class FieldValidationResult:
    """Result of validated fields."""

    missing: set[str]
    extra: set[str]
    resolved: dict[str, str] | None = None
