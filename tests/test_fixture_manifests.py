"""Check that the sample manifests under tests/fixtures can be uploaded as they are."""

from pathlib import Path

import pytest
import yaml

from bonsai_libs.parse.core.registry import get_parser

MANIFESTS = sorted((Path(__file__).parent / "fixtures").glob("*/sample_1.manifest.yml"))
AUXILIARY_RESULTS = {("samtools", "bedcov")}


def _referenced_paths(manifest: dict) -> list[str]:
    paths = [manifest.get(key) for key in ("nextflow_run_info", "ref_genome_sequence", "ref_genome_annotation")]
    for track in manifest.get("igv_annotations") or []:
        paths += [track.get("uri"), track.get("index_uri")]
    paths += [result["uri"] for result in manifest.get("analysis_result") or []]
    paths += list((manifest.get("index_artifacts") or {}).values())
    paths += [entry["value"] for entry in manifest.get("metadata") or [] if entry.get("type") == "table"]
    return [path for path in paths if path]


@pytest.mark.parametrize("manifest_path", MANIFESTS, ids=lambda path: path.parent.name)
def test_manifest_files_exist(manifest_path: Path):
    manifest = yaml.safe_load(manifest_path.read_text())
    missing = [path for path in _referenced_paths(manifest) if not (manifest_path.parent / path).is_file()]
    assert missing == []


@pytest.mark.parametrize("manifest_path", MANIFESTS, ids=lambda path: path.parent.name)
def test_manifest_results_have_parsers(manifest_path: Path):
    manifest = yaml.safe_load(manifest_path.read_text())
    for result in manifest["analysis_result"]:
        software, subcommand = result["software"], result.get("subcommand")
        if (software, subcommand) in AUXILIARY_RESULTS:
            continue
        get_parser(software, version=str(result["software_version"]), subcommand=subcommand)
