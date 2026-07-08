"""Test functions relating to reading delimited files."""


import io
from pathlib import Path

import pytest

from bonsai_libs.parse.io.delimited import read_delimited


def test_csv_all_inputs(tmp_path: Path):
    """Test reading delimited files."""

    raw = "a,b\n1,2\n3,NA\n"
    expect = [{"a":"1","b":"2"}, {"a":"3","b":"NA"}]

    # path
    p = tmp_path / "data.csv"
    p.write_text(raw, encoding="utf-8", newline="\n")
    assert list(read_delimited(p, delimiter=",", has_header=True)) == expect

    # text stream
    assert list(read_delimited(io.StringIO(raw), delimiter=",", has_header=True)) == expect

    # binary stream
    assert list(read_delimited(io.BytesIO(raw.encode()), delimiter=",", has_header=True)) == expect

    # bytes
    assert list(read_delimited(raw.encode(), delimiter=",", has_header=True)) == expect


def test_csv_convert_null(tmp_path: Path):
    """Test reading a csv and converting nullish values to None."""

    raw = "a,b\n1,2\n3,NA\n"
    expect = [{"a": "1","b": "2"}, {"a": "3","b": None}]

    assert list(read_delimited(io.StringIO(raw), delimiter=",", has_header=True, none_values={"NA"})) == expect


def test_csv_without_header_needs_fieldnames():
    """Test reading delimited files without header row."""

    with pytest.raises(ValueError):
        list(read_delimited(io.StringIO("1,2\n"), delimiter=",", has_header=False))
    rows = list(read_delimited(io.StringIO("1,2\n"), delimiter=",", has_header=False, fieldnames=["a","b"]))
    assert rows == [{"a":"1","b":"2"}]