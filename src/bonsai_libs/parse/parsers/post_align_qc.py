"""Parse postalignment QC results derived from samtools stats + coverage/bedcov."""

import bisect
from pathlib import Path
from typing import Any, IO

from bonsai_libs.parse.core.base import SingleAnalysisParser, StreamOrPath
from bonsai_libs.parse.core.registry import register_parser
from bonsai_libs.parse.io.delimited import read_delimited
from bonsai_libs.parse.io.utils import ensure_text_stream
from bonsai_libs.parse.models.enums import AnalysisSoftware, AnalysisType
from bonsai_libs.parse.models.qc import PostAlignQcResult

from .utils import safe_float, safe_int

POSTALIGNQC = AnalysisSoftware.POSTALIGNQC
SAMTOOLS = AnalysisSoftware.SAMTOOLS

# SN field names as they appear in `samtools stats` output (after the tab, before the colon)
_SN_RAW_READS = "raw total sequences"
_SN_READS_MAPPED = "reads mapped"
_SN_READS_PAIRED = "reads paired"
_SN_READS_DUP = "reads duplicated"
_SN_INS_SIZE = "insert size average"
_SN_INS_SIZE_DEV = "insert size standard deviation"
_SN_BASES_MAPPED = "bases mapped (cigar)"

# Coverage thresholds for pct_above_x
PCT_ABOVE_THRESHOLDS = [1, 10, 30, 100, 250, 500, 1000]


def _parse_stats_file(
    source: StreamOrPath,
) -> tuple[dict[str, str], list[tuple[int, int]]]:
    """Read a samtools stats file.

    Returns:
        sn: mapping of SN field name → raw string value
        cov: sorted list of (depth, count) pairs from the COV section
    """
    sn: dict[str, str] = {}
    cov: list[tuple[int, int]] = []

    def _process(fh: IO[str]) -> None:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if line.startswith("SN\t"):
                # SN\t<field>:\t<value>\t# optional comment
                parts = line.split("\t")
                if len(parts) >= 3:
                    field = parts[1].rstrip(":")
                    value = parts[2].split("#")[0].strip()
                    sn[field] = value
            elif line.startswith("COV\t"):
                # COV\t[D-D]\tD\t<count>
                parts = line.split("\t")
                if len(parts) >= 4:
                    depth = int(parts[2])
                    count = int(parts[3])
                    cov.append((depth, count))

    if isinstance(source, (str, Path)):
        with open(source, encoding="utf-8") as fh:
            _process(fh)
    else:
        _process(ensure_text_stream(source))

    cov.sort()
    return sn, cov


_COVERAGE_FIELDS = [
    "rname",
    "startpos",
    "endpos",
    "numreads",
    "covbases",
    "coverage",
    "meandepth",
    "meanbaseq",
    "meanmapq",
]


def _reference_stats_from_coverage(coverage: StreamOrPath) -> dict[str, Any]:
    """Derive reference-wide statistics from `samtools coverage` output.

    `samtools coverage` reports one row per reference sequence, so it gives the
    true reference length and a per-contig mean depth. This is preferred over
    deriving a length from a BED file, which may cover only part of the genome.

    Returns a dict with `reference_length`, `mean_cov` (length-weighted mean
    depth) and `covered_bases` (positions with depth >= 1).
    """
    reference_length = 0
    covered_bases = 0.0
    depth_sum = 0.0
    for row in read_delimited(coverage, has_header=False, fieldnames=_COVERAGE_FIELDS):
        rname = row.get("rname")
        if rname is None or rname.startswith("#"):
            continue
        start = safe_int(row.get("startpos"))
        end = safe_int(row.get("endpos"))
        if start is None or end is None:
            continue
        length = end - start + 1
        if length <= 0:
            continue
        reference_length += length
        cov_bases = safe_float(row.get("covbases")) or 0.0
        covered_bases += cov_bases
        mean_depth = safe_float(row.get("meandepth"))
        if mean_depth is not None:
            depth_sum += mean_depth * length

    mean_cov = depth_sum / reference_length if reference_length else None
    return {
        "reference_length": reference_length,
        "mean_cov": mean_cov,
        "covered_bases": covered_bases,
    }


_BEDCOV_FIELDS = ["chrom", "start", "end", "depth_sum"]


def _restricted_cov_from_bedcov(bedcov: StreamOrPath) -> dict[str, Any]:
    """Mean depth across the BED regions given to `samtools bedcov`.

    The fourth column of bedcov output is the summed per-base depth over the
    region, so mean depth is that total divided by the total region length.
    JASEN passes a core-loci BED here, so this is a *restricted* coverage
    metric and must not be used as the genome-wide denominator.
    """
    region_length = 0
    depth_sum = 0.0
    for row in read_delimited(bedcov, has_header=False, fieldnames=_BEDCOV_FIELDS):
        chrom = row.get("chrom")
        if chrom is None or chrom.startswith("#"):
            continue
        start, end = safe_int(row.get("start")), safe_int(row.get("end"))
        if start is None or end is None:
            continue
        region_length += end - start
        depth_sum += safe_float(row.get("depth_sum")) or 0.0
    return {
        "region_length": region_length,
        "mean_cov": depth_sum / region_length if region_length else None,
    }


def _coverage_stats(
    cov: list[tuple[int, int]],
    genome_length: int,
) -> dict[str, Any]:
    """Compute depth-distribution statistics from the stats COV section.

    `samtools stats` is the only one of the samtools outputs carrying a depth
    histogram, so the quartiles, median and pct_above_x thresholds come from
    here. `genome_length` must be the full reference length (from
    `samtools coverage`), since it is the denominator for every fraction below.

    Returns a dict with keys: pct_above_x, quartile1, median_cov, quartile3,
    coverage_uniformity.
    """

    # Build (depth → count) including depth 0
    coverages = [c for _, c in cov]
    depth0_count = max(0, genome_length - sum(coverages))

    # depths and counts in ascending order (0 first, then COV entries)
    depths = [0] + [d for d, _ in cov]
    counts = [depth0_count] + coverages

    # Cumulative counts for percentile lookup
    cumulative: list[int] = []
    running = 0
    for c in counts:
        running += c
        cumulative.append(running)

    def _percentile(pct: float) -> float:
        """Find the depth at which cumulative fraction reaches pct."""
        target = pct * genome_length
        idx = bisect.bisect_left(cumulative, target)
        idx = min(idx, len(depths) - 1)
        return float(depths[idx])

    quartile1 = _percentile(0.25)
    median_cov = _percentile(0.50)
    quartile3 = _percentile(0.75)
    coverage_uniformity = (quartile3 - quartile1) / median_cov if median_cov else None

    # pct_above_x: % of genome positions with depth >= threshold
    def _pct_above(threshold: int) -> float:
        # sum of counts at depth >= threshold
        above = sum(c for d, c in cov if d >= threshold)
        return above / genome_length * 100.0 if genome_length else 0.0

    pct_above_x = {str(t): round(_pct_above(t), 6) for t in PCT_ABOVE_THRESHOLDS}

    return {
        "pct_above_x": pct_above_x,
        "quartile1": quartile1,
        "median_cov": median_cov,
        "quartile3": quartile3,
        "coverage_uniformity": coverage_uniformity,
    }


@register_parser(SAMTOOLS, subcommand="stats")
class SamtoolsQcParser(SingleAnalysisParser):
    """Parse samtools stats, with optional coverage and bedcov, into a PostAlignQcResult."""

    software = POSTALIGNQC
    subcommand = "stats"
    parser_name = "SamtoolsQcParser"
    parser_version = 1
    schema_version = 1

    analysis_type = AnalysisType.QC
    produces = {analysis_type}

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        coverage_path: StreamOrPath | None = None,
        bedcov_path: StreamOrPath | None = None,
        **kwargs: Any,
    ) -> PostAlignQcResult | None:
        """Parse samtools stats into PostAlignQcResult.

        Args:
            source: `samtools stats` output, as a path, text stream or binary stream
            coverage_path: optional `samtools coverage` output. Supplies the true
                reference length and mean depth, which unlocks pct_above_x, the
                quartiles and uniformity. Preferred over bedcov for this.
            bedcov_path: optional `samtools bedcov` output. JASEN passes a
                core-loci BED, so this yields a *restricted* mean coverage
                reported separately; it is only used for the reference length as
                a fallback when `coverage_path` is absent.
        """
        try:
            sn, cov = _parse_stats_file(source)
        except Exception as exc:
            self.log_error("Failed to read samtools stats file", error=str(exc))
            return None

        # --- read metrics from SN section ---
        n_reads = safe_int(sn.get(_SN_RAW_READS))
        if n_reads is None:
            self.log_error("samtools stats missing 'raw total sequences'")
            return None

        n_mapped_reads = safe_int(sn.get(_SN_READS_MAPPED))
        n_read_pairs = safe_int(sn.get(_SN_READS_PAIRED))
        if n_read_pairs is None:
            self.log_error("samtools stats missing 'reads paired'")
            return None

        n_dup_reads = safe_int(sn.get(_SN_READS_DUP))
        ins_size = safe_float(sn.get(_SN_INS_SIZE))
        ins_size_dev = safe_float(sn.get(_SN_INS_SIZE_DEV))
        dup_pct = (n_dup_reads / n_reads * 100.0) if (n_dup_reads is not None and n_reads) else None

        # --- coverage metrics (require samtools coverage for reference length) ---
        mean_cov = None
        pct_above_x = None
        quartile1 = None
        median_cov = None
        quartile3 = None
        coverage_uniformity = None

        reference_length = 0
        restricted_mean_cov = None

        if coverage_path is not None:
            try:
                ref = _reference_stats_from_coverage(coverage_path)
                reference_length = ref["reference_length"]
                mean_cov = ref["mean_cov"]
            except Exception as exc:
                self.log_error("Failed to read samtools coverage file", error=str(exc))

        if bedcov_path is not None:
            try:
                restricted = _restricted_cov_from_bedcov(bedcov_path)
                restricted_mean_cov = restricted["mean_cov"]
                # under-counts when the BED covers only part of the genome
                if not reference_length:
                    reference_length = restricted["region_length"]
                    if mean_cov is None:
                        mean_cov = restricted_mean_cov
            except Exception as exc:
                self.log_error("Failed to read bedcov file", error=str(exc))

        if reference_length > 0 and cov:
            stats = _coverage_stats(cov, reference_length)
            pct_above_x = stats["pct_above_x"]
            quartile1 = stats["quartile1"]
            median_cov = stats["median_cov"]
            quartile3 = stats["quartile3"]
            coverage_uniformity = stats["coverage_uniformity"]

        result = PostAlignQcResult(
            ins_size=ins_size,
            ins_size_dev=ins_size_dev,
            mean_cov=mean_cov,
            pct_above_x=pct_above_x,
            n_reads=n_reads,
            n_mapped_reads=n_mapped_reads,
            n_read_pairs=n_read_pairs,
            n_dup_reads=n_dup_reads,
            dup_pct=dup_pct,
            coverage_uniformity=coverage_uniformity,
            quartile1=quartile1,
            median_cov=median_cov,
            quartile3=quartile3,
            restricted_mean_cov=restricted_mean_cov,
        )

        self.log_info(
            "Parsed SamtoolsQc",
            n_reads=result.n_reads,
            mean_cov=result.mean_cov,
        )
        return result
