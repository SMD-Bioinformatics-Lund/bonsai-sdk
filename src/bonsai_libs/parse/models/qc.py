"""QC result specific data models."""

from pydantic import BaseModel, Field

from bonsai_libs.parse.core.registry import register_result_model

from .enums import AnalysisSoftware, AnalysisType, GambitQcFlag


@register_result_model(AnalysisSoftware.QUAST, AnalysisType.QC)
class QuastQcResult(BaseModel):
    """Assembly QC metrics."""

    total_length: int
    reference_length: int | None = None
    largest_contig: int
    n_contigs: int
    n50: int
    ng50: int | None = None
    assembly_gc: float
    reference_gc: float | None = None
    duplication_ratio: float | None = None


@register_result_model(AnalysisSoftware.POSTALIGNQC, AnalysisType.QC)
class PostAlignQcResult(BaseModel):
    """Alignment QC metrics."""

    ins_size: float | None = None
    ins_size_dev: float | None = None
    mean_cov: float
    pct_above_x: dict[str, float]
    n_reads: int
    n_mapped_reads: int
    n_read_pairs: int
    coverage_uniformity: float | None = None
    quartile1: float
    median_cov: float
    quartile3: float


class GenomeCompleteness(BaseModel):
    """cgMLST QC metric."""

    n_missing: int = Field(..., description="Number of missing cgMLST alleles")


@register_result_model(AnalysisSoftware.GAMBIT, AnalysisType.QC)
class GambitcoreQcResult(BaseModel):
    """Gambitcore genome completeness QC metrics."""

    scientific_name: str
    completeness: float
    assembly_core: int
    species_core: int
    closest_accession: str | None = None
    closest_distance: float | None = None
    assembly_kmers: int | None = None
    species_kmers_mean: int | None = None
    species_kmers_std_dev: int | None = None
    assembly_qc: GambitQcFlag | None = None


class NanoPlotSummary(BaseModel):
    """Summary of NanoPlot results."""

    mean_read_length: float
    mean_read_quality: float
    median_read_length: float
    median_read_quality: float
    n_reads: float
    read_length_n50: float
    stdev_read_length: float
    total_bases: float


class NanoPlotQcCutoff(BaseModel):
    """Percentage of reads above quality cutoffs."""

    q10: float
    q15: float
    q20: float
    q25: float
    q30: float


@register_result_model(AnalysisSoftware.NANOPLOT, AnalysisType.QC)
class NanoPlotQcResult(BaseModel):
    """Nanopore sequencing QC metrics from NanoPlot."""

    summary: NanoPlotSummary
    qc_cutoff: NanoPlotQcCutoff
    top_quality: list[float] = Field(default_factory=list)
    top_longest: list[int] = Field(default_factory=list)


class ContigCoverage(BaseModel):
    """Coverage information for a single contig."""

    contig_name: str
    start_pos: int
    end_pos: int
    n_reads: int
    cov_bases: int
    coverage: float
    mean_depth: float
    mean_base_quality: float
    mean_map_quality: float


@register_result_model(AnalysisSoftware.SAMTOOLS, AnalysisType.QC)
class SamtoolsCoverageQcResult(BaseModel):
    """SAMtools coverage QC result model."""

    contigs: list[ContigCoverage]
