"""VirulenceFinder typing results."""

from typing import Any

from pydantic import Field, model_validator

from bonsai_libs.parse.core.registry import register_result_model

from .base import GeneWithReference
from .enums import AnalysisSoftware, AnalysisType


@register_result_model(AnalysisSoftware.VIRULENCEFINDER, AnalysisType.STX)
class TypingResultStx(GeneWithReference):
    """Complete STX typing evidence with a legacy single-hit summary.

    Inherited gene fields describe the best match for existing consumers.
    ``hits`` preserves every typing match, including alternative alleles;
    entries are supporting evidence, not necessarily separate toxin copies.
    """

    hits: list[GeneWithReference] = Field(
        min_length=1, description="All matches selected for the STX result by the parser."
    )

    # FIXME: Cleanup after reimport prior to release of v3
    @model_validator(mode="before")
    @classmethod
    def include_legacy_hit(cls, value: Any) -> Any:
        """Read historical single-gene payloads as one-hit results."""
        if isinstance(value, dict) and "hits" not in value:
            return {**value, "hits": [value.copy()]}
        return value
