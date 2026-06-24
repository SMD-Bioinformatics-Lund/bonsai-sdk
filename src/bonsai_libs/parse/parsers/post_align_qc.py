from typing import Any, Mapping

from bonsai_libs.parse.core.base import SingleAnalysisParser, StreamOrPath
from bonsai_libs.parse.core.registry import register_parser
from bonsai_libs.parse.io.json import read_json
from bonsai_libs.parse.models.enums import AnalysisSoftware, AnalysisType
from bonsai_libs.parse.models.qc import PostAlignQcResult

from .utils import safe_float, safe_int

POSTALIGNQC = AnalysisSoftware.POSTALIGNQC

# Optional: required keys you consider mandatory for a valid QC blob
REQUIRED_KEYS = {
    "mean_cov",
    "pct_above_x",
    "n_reads",
    "n_mapped_reads",
    "n_read_pairs",
    "quartile1",
    "median_cov",
    "quartile3",
    # ins_size, ins_size_dev, coverage_uniformity are optional in your original code
}


def _validate_keys(qc_dict: Mapping[str, Any], *, strict: bool = False) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in qc_dict]
    if missing:
        msg = f"PostAlignQC JSON missing required keys: {sorted(missing)}"
        if strict:
            raise ValueError(msg)


def _to_postalignqc_result(
    qc_dict: Mapping[str, Any], *, strict: bool = False, logger: Any | None = None
) -> PostAlignQcResult:
    """Convert raw dict to PostAlignQcResult."""

    # optional fields
    ins_size = None
    if qc_dict.get("ins_size") is not None:
        # preserve old behavior: int(float(x)) handles "123.0"
        try:
            ins_size = safe_float(qc_dict["ins_size"], logger=logger)
        except (TypeError, ValueError) as exc:
            if strict:
                raise ValueError(f"Invalid ins_size={qc_dict.get('ins_size')!r}") from exc

    ins_size_dev = None
    if qc_dict.get("ins_size_dev") is not None:
        try:
            ins_size_dev = safe_float(qc_dict["ins_size_dev"], logger=logger)
        except (TypeError, ValueError) as exc:
            if strict:
                raise ValueError(f"Invalid ins_size_dev={qc_dict.get('ins_size_dev')!r}") from exc

    coverage_uniformity = None
    if qc_dict.get("coverage_uniformity") is not None:
        try:
            coverage_uniformity = safe_float(qc_dict["coverage_uniformity"], logger=logger)
        except (TypeError, ValueError) as exc:
            if strict:
                raise ValueError(
                    f"Invalid coverage_uniformity={qc_dict.get('coverage_uniformity')!r}"
                ) from exc

    # required fields
    try:
        mean_cov = safe_float(qc_dict["mean_cov"])
        n_reads = safe_int(qc_dict["n_reads"])
        n_mapped_reads = safe_int(qc_dict["n_mapped_reads"])
        n_read_pairs = safe_int(qc_dict["n_read_pairs"])

        quartile1 = safe_float(qc_dict["quartile1"])
        median_cov = safe_float(qc_dict["median_cov"])
        quartile3 = safe_float(qc_dict["quartile3"])

        pct_above_x = qc_dict["pct_above_x"]
    except KeyError as exc:
        raise ValueError(f"Missing key in PostAlignQC JSON: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Bad numeric value in PostAlignQC JSON: {exc}") from exc

    return PostAlignQcResult(
        ins_size=ins_size,
        ins_size_dev=ins_size_dev,
        mean_cov=mean_cov,
        pct_above_x=pct_above_x,
        n_reads=n_reads,
        n_mapped_reads=n_mapped_reads,
        n_read_pairs=n_read_pairs,
        coverage_uniformity=coverage_uniformity,
        quartile1=quartile1,
        median_cov=median_cov,
        quartile3=quartile3,
    )


@register_parser(POSTALIGNQC)
class PostAlignQcParser(SingleAnalysisParser):
    software = POSTALIGNQC
    parser_name = "PostAlignQcParser"
    parser_version = 1
    schema_version = 1

    analysis_type = AnalysisType.QC
    produces = {analysis_type}

    def _parse_one(
        self,
        source: StreamOrPath,
        *,
        strict: bool = False,
        **kwargs: Any,
    ) -> PostAlignQcResult | None:
        """Read JSON and return a PostAlignQcResult."""

        try:
            qc_dict = read_json(source)
        except Exception as exc:
            self.log_error("Failed to read PostAlignQC JSON", error=str(exc))
            if strict:
                raise
            return None

        if not isinstance(qc_dict, dict):
            msg = f"PostAlignQC JSON is not an object/dict, got {type(qc_dict)!r}"
            self.log_error(msg)
            if strict:
                raise ValueError(msg)
            return None

        _validate_keys(qc_dict, strict=strict)

        try:
            qc_res = _to_postalignqc_result(qc_dict, strict=strict)
        except Exception as exc:
            self.log_error("Failed to parse PostAlignQC metrics", error=str(exc))
            if strict:
                raise
            return None

        # Optional observability log
        self.log_info(
            "Parsed PostAlignQC",
            mean_cov=qc_res.mean_cov,
            n_reads=qc_res.n_reads,
            n_mapped_reads=qc_res.n_mapped_reads,
        )

        return qc_res
