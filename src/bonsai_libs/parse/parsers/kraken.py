"""Parse Kraken reports."""

from typing import Any

from bonsai_libs.parse.core.base import SingleAnalysisParser, StreamOrPath
from bonsai_libs.parse.core.registry import register_parser
from bonsai_libs.parse.io.delimited import read_delimited
from bonsai_libs.parse.models.bracken import BrackenSpeciesPrediction, BrackenSpeciesPredictions
from bonsai_libs.parse.models.enums import AnalysisSoftware, AnalysisType, TaxLevel

from .utils import safe_int

KRAKEN = AnalysisSoftware.KRAKEN
REPORT_COLUMNS = ["percentage", "clade_reads", "direct_reads", "rank", "taxonomy_id", "name"]
SPECIES_RANK = "S"


@register_parser(KRAKEN)
class KrakenParser(SingleAnalysisParser):
    """Parser for Kraken reports, returned in the Bracken species format."""

    software = KRAKEN
    parser_name = "KrakenParser"
    parser_version = 1
    schema_version = 1
    produces = {AnalysisType.SPECIES}
    analysis_type = AnalysisType.SPECIES

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        cutoff: float | None = None,
        **_,
    ) -> BrackenSpeciesPredictions:
        """Parse species-level rows with reads from a Kraken report."""
        species = [
            row
            for row in read_delimited(source, has_header=False, fieldnames=REPORT_COLUMNS)
            if row["rank"].strip() == SPECIES_RANK and self._clade_reads(row)
        ]
        total_reads = sum(self._clade_reads(row) for row in species)

        results: BrackenSpeciesPredictions = []
        for row in species:
            reads = self._clade_reads(row)
            fraction = reads / total_reads
            if cutoff is not None and fraction < cutoff:
                continue
            results.append(
                BrackenSpeciesPrediction(
                    scientific_name=row["name"].strip(),
                    taxonomy_id=row["taxonomy_id"],
                    taxonomy_lvl=TaxLevel.S,
                    kraken_assigned_reads=reads,
                    added_reads=0,
                    fraction_total_reads=fraction,
                )
            )
        return sorted(results, key=lambda spp: spp.kraken_assigned_reads, reverse=True)

    def _clade_reads(self, row: dict[str, Any]) -> int:
        return safe_int(row["clade_reads"], logger=self.logger) or 0
