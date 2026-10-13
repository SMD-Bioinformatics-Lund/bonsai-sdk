"""Test Kraken report parser."""

from bonsai_libs.parse import hydrate_result, run_parser
from bonsai_libs.parse.models.bracken import BrackenSpeciesPrediction
from bonsai_libs.parse.models.enums import AnalysisType, TaxLevel
from bonsai_libs.parse.parsers.kraken import KrakenParser


def _species(path, **kwargs):
    return KrakenParser().parse(path, **kwargs).results[AnalysisType.SPECIES].value


def test_only_species_with_reads_are_kept(streptococcus_kraken_path):
    """Strains, genera and species without reads are dropped."""
    names = [spp.scientific_name for spp in _species(streptococcus_kraken_path)]

    assert names == [
        "Streptococcus pyogenes",
        "Streptococcus dysgalactiae",
        "Streptococcus canis",
        "Enterococcus faecalis",
        "Streptococcus pseudopneumoniae",
        "Streptococcus sp. 'group B'",
    ]


def test_species_are_in_the_bracken_format(streptococcus_kraken_path):
    top = _species(streptococcus_kraken_path)[0]

    assert isinstance(top, BrackenSpeciesPrediction)
    assert top.taxonomy_id == 1314
    assert top.taxonomy_lvl == TaxLevel.S
    assert top.kraken_assigned_reads == 2501957
    assert top.added_reads == 0


def test_fractions_are_of_species_level_reads(streptococcus_kraken_path):
    species = _species(streptococcus_kraken_path)

    assert abs(sum(spp.fraction_total_reads for spp in species) - 1) < 1e-9
    assert round(species[0].fraction_total_reads, 3) == 0.984


def test_cutoff_drops_low_fractions(streptococcus_kraken_path):
    names = [spp.scientific_name for spp in _species(streptococcus_kraken_path, cutoff=0.01)]

    assert names == ["Streptococcus pyogenes", "Streptococcus dysgalactiae"]


def test_kraken_is_registered_and_hydrates(streptococcus_kraken_path):
    """The Bonsai API parses and stores kraken uploads through the registry."""
    out = run_parser(software="kraken", version="2.1.3", data=streptococcus_kraken_path)
    stored = out.results[AnalysisType.SPECIES].value
    raw = [spp.model_dump(mode="json") for spp in stored]

    hydrated = hydrate_result(
        software="kraken", analysis_type=AnalysisType.SPECIES.value, result=raw
    )

    assert [spp.scientific_name for spp in hydrated] == [spp.scientific_name for spp in stored]
