"""Parse ShigaTyper results."""

import csv
from pathlib import Path
from typing import Any

from bonsai_libs.parse.core.base import SingleAnalysisParser, StreamOrPath, warn_if_extra_rows
from bonsai_libs.parse.core.registry import register_parser
from bonsai_libs.parse.exceptions import InvalidDataFormat
from bonsai_libs.parse.io.delimited import is_nullish
from bonsai_libs.parse.io.utils import ensure_text_stream
from bonsai_libs.parse.models.enums import AnalysisSoftware, AnalysisType
from bonsai_libs.parse.models.typing import ShigatyperHit, TypingResultShigatyper

SHIGATYPER = AnalysisSoftware.SHIGATYPER

REQUIRED_COLUMNS = {"sample", "prediction", "ipaB", "notes"}

_HITS_REQUIRED_COLUMNS = {"Hit", "Number of reads"}


def _parse_hits(source: StreamOrPath) -> list[ShigatyperHit]:
    """Parse the companion `*-hits.tsv` file into a list of hits."""
    if isinstance(source, (str, Path)):
        with open(source, encoding="utf-8", newline="") as stream:
            return _parse_hits(stream)

    # Ignore the unnamed pandas index and any additional alignment metrics.
    reader = csv.DictReader(ensure_text_stream(source), delimiter="\t")
    if not _HITS_REQUIRED_COLUMNS.issubset(reader.fieldnames or []):
        raise InvalidDataFormat("ShigaTyper hits require 'Hit' and 'Number of reads' columns")

    hits: list[ShigatyperHit] = []
    for row in reader:
        if all(value is None or value == "" for value in row.values()):
            continue
        name = (row.get("Hit") or "").strip()
        try:
            n_reads = int(row.get("Number of reads") or "")
        except ValueError as exc:
            raise InvalidDataFormat(
                f"Invalid ShigaTyper read count on hits line {reader.line_num}"
            ) from exc
        if not name or n_reads < 0:
            raise InvalidDataFormat(
                f"ShigaTyper hits line {reader.line_num} requires a name and nonnegative read count"
            )
        hits.append(ShigatyperHit(name=name, n_reads=n_reads))
    return hits


@register_parser(SHIGATYPER)
class ShigatyperParser(SingleAnalysisParser):
    """Parser for ShigaTyper species/pathotype prediction results."""

    software = SHIGATYPER
    parser_name = "ShigatyperParser"
    parser_version = 2
    schema_version = 1

    analysis_type = AnalysisType.SHIGATYPE
    produces = {analysis_type}

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        hits_path: StreamOrPath | None = None,
        strict_columns: bool = False,
        **kwargs: Any,
    ) -> TypingResultShigatyper | None:
        """Parse ShigaTyper's prediction TSV (+ optional companion hits TSV).

        Args:
            source: ShigaTyper's main output (sample, prediction, ipaB, notes)
            hits_path: optional companion `*-hits.tsv` file listing the k-mer/
                gene hits and read counts supporting the prediction
        """
        first, rows = self._read_rows(
            source,
            required=REQUIRED_COLUMNS,
            strict_columns=strict_columns,
        )
        if first is None:
            return None

        warn_if_extra_rows(rows, self.log_warning, context="shigatyper file", max_consume=10)

        # '-' is an explicit negative marker here, not a missing value.
        ipaB = first.get("ipaB")
        if ipaB != "-" and is_nullish(ipaB):
            ipaB = None
        if ipaB not in (None, "+", "-"):
            raise InvalidDataFormat("ShigaTyper ipaB must be '+', '-', or missing")

        hits = _parse_hits(hits_path) if hits_path is not None else []

        return TypingResultShigatyper(
            prediction=None if is_nullish(first["prediction"]) else first["prediction"],
            ipaB=ipaB,
            notes=None if is_nullish(first.get("notes")) else first["notes"],
            hits=hits,
        )
