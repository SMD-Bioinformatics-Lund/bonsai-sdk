"""Functions for parsing shigapass result."""

import logging
import re
from typing import Any, Mapping

from bonsai_libs.parse.core.base import (
    SingleAnalysisParser,
    StreamOrPath,
    warn_if_extra_rows,
)
from bonsai_libs.parse.core.registry import register_parser
from bonsai_libs.parse.io.delimited import (
    DelimiterRow,
    canonical_header,
    is_nullish,
    normalize_row,
    read_delimited,
)
from bonsai_libs.parse.models.enums import AnalysisSoftware, AnalysisType
from bonsai_libs.parse.models.typing import TypingResultShiga

from .utils import safe_float

LOG = logging.getLogger(__name__)


SHIGAPASS = AnalysisSoftware.SHIGAPASS
DELIMITER = ";"
_PERCENT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*%")

COLUMN_MAP: dict[str, str] = {
    "Name": "sample_name",
    "rfb_hits,": "rfb_hits",
    "MLST": "mlst",
    "fliC": "flic",
    "CRISPR": "crispr",
    "ipaH": "ipah",
    "Predicted_Serotype": "predicted_serotype",
    "Predicted_FlexSerotype": "predicted_flex_serotype",
    "Comments": "comments",
    # If your file actually has rfb as a separate column, add it here:
    # "rfb": "rfb",
}

REQUIRED_COLUMNS: set[str] = {
    "Name",
    "rfb_hits,(%)",
    "MLST",
    "fliC",
    "CRISPR",
    "ipaH",
    "Predicted_Serotype",
    "Predicted_FlexSerotype",
    "Comments",
}


def _normalize_shigapass_row(row: DelimiterRow) -> DelimiterRow:
    """Wrapps normalize row."""
    return normalize_row(
        row,
        key_fn=lambda r: canonical_header(r).lstrip(","),
        val_fn=lambda v: None if is_nullish(v) else v,
        column_map=COLUMN_MAP,
    )


def extract_percentage(value: Any) -> float | None:
    """Return float percent from strings like '12.3%' or numeric values."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    match = _PERCENT_RE.search(s)
    if match:
        return safe_float(match.group(1))
    return safe_float(s)


def _to_typing_result(row: Mapping[str, Any], *, strict: bool) -> TypingResultShiga:
    """Cast result to TypingResultShiga."""

    rfb = row["rfb"]  # if you map it
    rfb_hits = extract_percentage(row["rfb_hits"])

    if strict and rfb_hits is None:
        raise ValueError(f"Invalid rfb_hits value: {row.get('rfb_hits')!r}")

    return TypingResultShiga(
        rfb=rfb,
        rfb_hits=rfb_hits or 0.0,
        mlst=row.get("mlst"),
        flic=row.get("flic"),
        crispr=row.get("crispr"),
        ipah=str(row.get("ipah") or ""),
        predicted_serotype=str(row.get("predicted_serotype") or ""),
        predicted_flex_serotype=row.get("predicted_flex_serotype"),
        comments=row.get("comments"),
    )


@register_parser(SHIGAPASS)
class ShigapassParser(SingleAnalysisParser):
    """Parser for ShigaType results."""

    software = SHIGAPASS
    parser_name = "ShigapassParser"
    parser_version = 1
    schema_version = 1

    analysis_type = AnalysisType.SHIGATYPE
    produces = {analysis_type}

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        strict_columns: bool = False,
        strict: bool = False,
        **kwargs: Any,
    ) -> TypingResultShiga | None:
        """Parse shigapass predictions and return a ShigaTypingMethodIndex."""
        rows = read_delimited(source, delimiter=DELIMITER)

        try:
            first_raw = next(rows)
        except StopIteration:
            self.log_info("Shigapass input empty")
            return None

        self.validate_columns(first_raw, required=REQUIRED_COLUMNS, strict=strict_columns)

        # Normalize keys
        first = _normalize_shigapass_row(first_raw)
        warn_if_extra_rows(rows, self.log_warning, context=f"{self.software} file", max_consume=10)

        # Build typing result
        shiga = _to_typing_result(first, strict=strict)
        return shiga
