"""Parse VirulenceFinder v2/v3 JSON results.

V2 groups hits under ``virulencefinder.results.<species>.<database>``.
V3 links phenotypes to ``seq_regions``; ``ref_database`` identifies hit origins.

Example files, relative to the bonsai-sdk repository root:

- V2: ``tests/fixtures/ecoli/virulencefinder.v2.stx.json``.
- V3: ``tests/fixtures/ecoli/virulencefinder.stx_pred.stx.json``.
"""

import logging
from typing import Any

from bonsai_libs.parse.io.json import read_json, require_mapping
from bonsai_libs.parse.io.types import StreamOrPath
from bonsai_libs.parse.core.base import BaseParser
from bonsai_libs.parse.models.base import ParseImplOut
from bonsai_libs.parse.core.envelope import run_as_envelope
from bonsai_libs.parse.core.registry import register_parser
from bonsai_libs.parse.exceptions import DataFormatError, InvalidDataFormat
from bonsai_libs.parse.models.base import ElementTypeResult, GeneWithReference
from bonsai_libs.parse.models.typing import TypingResultStx
from bonsai_libs.parse.models.enums import (
    AnalysisSoftware,
    AnalysisType,
    ElementType,
    ElementVirulenceSubtype,
)

LOG = logging.getLogger(__name__)

VIRFINDER = AnalysisSoftware.VIRULENCEFINDER

REQUIRED_FIELDS = {"databases", "seq_regions", "software_executions"}

STX_ASSAY = "stx"

def parse_vir_gene(
    info: dict[str, Any],
    function: str,
    subtype: ElementVirulenceSubtype = ElementVirulenceSubtype.VIR,
) -> GeneWithReference:
    """Parse virulence gene prediction results."""
    accnr = info.get("ref_acc", None)
    if accnr == "NA":
        accnr = None
    return GeneWithReference(
        # info
        gene_symbol=info["name"],
        accession=accnr,
        ref_database=", ".join(info.get("ref_database") or []) or None,
        sequence_name=function,
        # gene classification
        element_type=ElementType.VIR,
        element_subtype=subtype,
        # position
        ref_start_pos=int(info["ref_start_pos"]),
        ref_end_pos=int(info["ref_end_pos"]),
        ref_gene_length=int(info["ref_seq_length"]),
        alignment_length=int(info["alignment_length"]),
        # prediction
        identity=float(info["identity"]),
        coverage=float(info["coverage"]),
    )


def parse_vir_gene_v2(
    info: dict[str, Any],
    subtype: ElementVirulenceSubtype = ElementVirulenceSubtype.VIR,
    ref_database: str | None = None,
) -> GeneWithReference:
    """Parse a virulence gene hit from v2 output."""
    start_pos, end_pos = map(int, info["position_in_ref"].split(".."))
    accnr = info.get("accession")
    if accnr == "NA":
        accnr = None
    return GeneWithReference(
        # info
        gene_symbol=info["virulence_gene"],
        accession=accnr,
        ref_database=ref_database,
        sequence_name=(info.get("protein_function") or "").strip(),
        # gene classification
        element_type=ElementType.VIR,
        element_subtype=subtype,
        # position
        ref_start_pos=start_pos,
        ref_end_pos=end_pos,
        ref_gene_length=int(info["template_length"]),
        alignment_length=int(info["HSP_length"]),
        # prediction
        identity=float(info["identity"]),
        coverage=float(info["coverage"]),
    )


def parse_stx_typing(pred: dict[str, Any]) -> TypingResultStx | None:
    """Preserve dedicated STX matches and STX genes from virulence databases."""

    phenotypes = pred.get("phenotypes", {}) or {}
    seq_regions = pred.get("seq_regions", {}) or {}

    hits: list[GeneWithReference] = []
    seen_regions: set[str] = set()

    for pheno in phenotypes.values():
        function = pheno.get("function") or ""
        region_keys = pheno.get("seq_regions") or []
        for region_key in region_keys:
            info = seq_regions.get(region_key)
            if info and region_key not in seen_regions:
                databases = info.get("ref_database") or pheno.get("ref_database") or []
                is_stx_database = any(
                    str(db).rsplit(":", 1)[-1] == STX_ASSAY for db in databases
                )
                is_stx_gene = str(info.get("name", "")).lower().startswith("stx")
                if not (is_stx_database or is_stx_gene):
                    continue
                info = {**info, "ref_database": databases}
                hits.append(parse_vir_gene(info, function=function))
                seen_regions.add(region_key)
    if not hits:
        return None
    return TypingResultStx(hits=_sort_genes(hits))


def parse_virulence_block(pred: dict[str, Any]) -> ElementTypeResult:
    """Parse virulencefinder virulence prediction results."""

    vir_genes: list[GeneWithReference] = []
    phenotypes = pred.get("phenotypes", {}) or {}
    seq_regions = pred.get("seq_regions", {}) or {}

    for _, pheno in phenotypes.items():
        function = pheno.get("function") or ""
        ref_dbs = pheno.get("ref_database") or []

        # skip stx typing results
        if any("stx" in str(db).lower() for db in ref_dbs):
            continue

        subtype = ElementVirulenceSubtype.VIR
        if any("toxin" in str(db).lower() for db in ref_dbs):
            subtype = ElementVirulenceSubtype.TOXIN

        region_keys = pheno.get("seq_regions") or []
        regions = [seq_regions.get(k) for k in region_keys if seq_regions.get(k)]
        for info in regions:
            vir_genes.append(parse_vir_gene(info, function=function, subtype=subtype))

    return ElementTypeResult(genes=_sort_genes(vir_genes), variants=[], phenotypes={})


def _sort_genes(genes: list[GeneWithReference]) -> list[GeneWithReference]:
    """Sort genes on symbol and coverage, handling None safely."""
    return sorted(
        genes,
        key=lambda gene: (
            gene.gene_symbol or "",
            gene.coverage if gene.coverage is not None else -1.0,
        ),
    )


def _assay_subtype(assay: str) -> ElementVirulenceSubtype:
    """Derive the gene subtype from a v2 assay name such as 's.aureus_toxin'."""
    group = assay.split("_")[1] if "_" in assay else assay
    if group == "toxin":
        return ElementVirulenceSubtype.TOXIN
    return ElementVirulenceSubtype.VIR


def read_v2_assays(pred: dict[str, Any]) -> dict[str, Any]:
    """Return the per-assay result block of the first species in a v2 file.

    v2 output nests results one level deeper than v3, under the species the
    databases were selected for. Only one species is ever reported.
    """
    root = require_mapping(pred.get("virulencefinder"), what="virulencefinder")
    results = require_mapping(root.get("results"), what="virulencefinder.results")

    species = next(iter(results), None)
    if species is None:
        return {}
    return require_mapping(results[species], what=f"virulencefinder.results.{species}")


def parse_virulence_block_v2(assays: dict[str, Any]) -> ElementTypeResult:
    """Parse virulence genes from v2 output."""

    vir_genes: list[GeneWithReference] = []
    for assay, hits in assays.items():
        if assay == STX_ASSAY:
            continue
        if not isinstance(hits, dict):
            continue

        subtype = _assay_subtype(assay)
        for info in hits.values():
            vir_genes.append(parse_vir_gene_v2(info, subtype, ref_database=assay))

    return ElementTypeResult(genes=_sort_genes(vir_genes), variants=[], phenotypes={})


def parse_stx_typing_v2(assays: dict[str, Any]) -> TypingResultStx | None:
    """Preserve dedicated STX matches and STX genes from virulence databases."""

    genes = []
    for assay, hits in assays.items():
        if not isinstance(hits, dict):
            continue
        for hit in hits.values():
            if assay == STX_ASSAY or hit["virulence_gene"].lower().startswith("stx"):
                genes.append(parse_vir_gene_v2(hit, ref_database=assay))
    return TypingResultStx(hits=_sort_genes(genes)) if genes else None


class _VirulenceFinderParserBase(BaseParser):
    """Shared parse logic for all VirulenceFinder versions.

    Subclasses implement reading and validation of their own output format in
    ``_read``, and turn the result into virulence and stx blocks in
    ``_virulence`` and ``_stx``; the registry then dispatches to the right
    subclass based on ``software_version`` in the sample manifest.
    """

    software = VIRFINDER
    parser_version = "3"
    schema_version = "2"
    produces = {AnalysisType.VIRULENCE, AnalysisType.STX}

    def _read(self, source: StreamOrPath) -> Any:
        """Read and validate the result file."""
        raise NotImplementedError

    def _virulence(self, pred: Any) -> ElementTypeResult:
        """Build the virulence gene block."""
        raise NotImplementedError

    def _stx(self, pred: Any) -> TypingResultStx | None:
        """Build the stx typing result."""
        raise NotImplementedError

    def _parse_impl(
        self,
        source: StreamOrPath,
        *,
        want: set[AnalysisType],
        strict: bool = False,
        **kwargs: Any,
    ) -> ParseImplOut:
        """Parse virulence finder resuls."""
        try:
            pred = self._read(source)
        except TypeError as exc:
            self.log_error("Failed to read VirulenceFinder JSON", error=str(exc))
            if strict:
                raise
            return {}
        except (DataFormatError, InvalidDataFormat) as exc:
            self.log_error("Failed to read/validate VirulenceFinder JSON", error=str(exc))
            if strict:
                raise
            return {}

        out: dict[AnalysisType, Any] = {}

        base_meta = {"parser": self.parser_name, "software": self.software}

        if AnalysisType.VIRULENCE in want:
            out[AnalysisType.VIRULENCE] = run_as_envelope(
                analysis_name=AnalysisType.VIRULENCE,
                fn=lambda: self._virulence(pred),
                reason_if_absent="No virulence determinants in file.",
                reason_if_empty="No findings",
                meta=base_meta,
                logger=self.logger,
            )

        if AnalysisType.STX in want:
            out[AnalysisType.STX] = run_as_envelope(
                analysis_name=AnalysisType.STX,
                fn=lambda: self._stx(pred),
                reason_if_absent="No STX gene identified.",
                reason_if_empty="No findings",
                meta=base_meta,
                logger=self.logger,
            )
        return out


@register_parser(VIRFINDER, max_version="2.99.99")
class VirulenceFinderV2Parser(_VirulenceFinderParserBase):
    """Parse VirulenceFinder v2 output (pre-seq_regions JSON schema)."""

    parser_name = "VirulenceFinderV2Parser"

    def _read(self, source: StreamOrPath) -> dict[str, Any]:
        raw = require_mapping(read_json(source), what="<root>")
        return read_v2_assays(raw)

    def _virulence(self, pred: dict[str, Any]) -> ElementTypeResult:
        return parse_virulence_block_v2(pred)

    def _stx(self, pred: dict[str, Any]) -> TypingResultStx | None:
        return parse_stx_typing_v2(pred)


@register_parser(VIRFINDER, min_version="3.0.0")
class VirulenceFinderParser(_VirulenceFinderParserBase):
    """Parse VirulenceFinder v3+ output."""

    parser_name = "VirulenceFinderParser"

    def _read(self, source: StreamOrPath) -> dict[str, Any]:
        raw = require_mapping(read_json(source), what="<root>")
        for field in REQUIRED_FIELDS:
            require_mapping(raw.get(field), what=field)
        return raw

    def _virulence(self, pred: dict[str, Any]) -> ElementTypeResult:
        return parse_virulence_block(pred)

    def _stx(self, pred: dict[str, Any]) -> TypingResultStx | None:
        return parse_stx_typing(pred)
