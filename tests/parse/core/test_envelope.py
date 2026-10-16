"""Regression checks for parser exception envelopes."""

from bonsai_libs.parse.core.envelope import run_as_envelope
from bonsai_libs.parse.exceptions import InvalidDataFormat


def test_parser_error_preserves_reason_and_context():
    def fail():
        raise InvalidDataFormat("Broken input", context={"field": "alleles"})

    envelope = run_as_envelope("mlst", fail)
    assert envelope.status == "error"
    assert envelope.reason == "Broken input"
    assert envelope.meta["field"] == "alleles"
