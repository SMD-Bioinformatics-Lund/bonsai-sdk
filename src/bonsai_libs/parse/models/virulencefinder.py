"""VirulenceFinder typing results."""

from pydantic import Field

from bonsai_libs.parse.core.registry import register_result_model

from .base import GeneWithReference, RWModel
from .enums import AnalysisSoftware, AnalysisType


@register_result_model(AnalysisSoftware.VIRULENCEFINDER, AnalysisType.STX)
class TypingResultStx(RWModel):
    """Complete STX matches selected by the parser.

    ``hits`` preserves every typing match, including alternative alleles;
    entries are supporting evidence, not necessarily separate toxin copies.
    Each hit's ``ref_database`` identifies its source database when available.
    """

    hits: list[GeneWithReference] = Field(
        min_length=1, description="All matches selected for the STX result by the parser."
    )
