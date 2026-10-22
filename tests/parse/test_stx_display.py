"""The STX display field survives serialization and derives only from hits."""

import json

import pytest

from bonsai_libs.parse import hydrate_result
from bonsai_libs.parse.models.base import GeneWithReference
from bonsai_libs.parse.models.typing import TypingResultStx


def hit(symbol, database="stx"):
    return GeneWithReference(
        gene_symbol=symbol,
        ref_database=database,
        element_type="VIRULENCE",
        element_subtype="VIRULENCE",
    )


@pytest.mark.parametrize(
    "symbols,expected",
    [
        (["stx2a", "stx1a", "stx2a"], "stx2, stx1"),
        (["stx2a"], "stx2"),
        (["stx1a", "stx1c-O157-FLY16"], "stx1"),
        (["stx1", "stx2c-O157-FLY16", "stx1a", "stx2d"], "stx1, stx2"),
        (["STX1a", "Stx2c", "stx1c"], "stx1, stx2"),
        (["other", "stx3", "prefix-stx1"], "-"),
        ([None, "", "-"], "-"),
    ],
)
def test_display_survives_json_and_hydration(symbols, expected):
    result = TypingResultStx(
        hits=[
            hit(symbol, "stx" if index % 2 == 0 else "virulence_ecoli")
            for index, symbol in enumerate(symbols)
        ]
    )
    original_hits = [gene.model_dump() for gene in result.hits]
    wire = json.loads(result.model_dump_json())
    assert wire["gene_symbol"] == expected
    assert wire["hits"] == original_hits
    wire["gene_symbol"] = "stale display value"
    loaded = hydrate_result(software="virulencefinder", analysis_type="stx", result=wire)
    assert isinstance(loaded, TypingResultStx)
    assert loaded.model_dump() == {"hits": original_hits, "gene_symbol": expected}
    assert TypingResultStx.model_json_schema(mode="serialization")["properties"]["gene_symbol"][
        "readOnly"
    ]


def test_display_tracks_changes_to_the_hits():
    result = TypingResultStx(hits=[hit("stx2a")])
    result.hits.append(hit("stx1a"))
    assert result.model_dump()["gene_symbol"] == "stx2, stx1"
