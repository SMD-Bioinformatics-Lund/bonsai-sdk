"""Analysis uploads must transmit companion files as multipart file parts."""

from types import SimpleNamespace

import pytest

from bonsai_libs.api_client.bonsai.client import BonsaiApiClient
from bonsai_libs.api_client.bonsai.models import UploadAnalysisResultInput


@pytest.mark.parametrize("with_companion", [True, False])
def test_analysis_upload_multipart_files(tmp_path, monkeypatch, with_companion):
    main = tmp_path / "kleborate.tsv"
    main.write_bytes(b"main report")
    companion = tmp_path / "hamronization.tsv"
    companion.write_bytes(b"AMR report")
    coverage = tmp_path / "coverage.tsv"
    coverage.write_bytes(b"coverage report")
    bedcov = tmp_path / "bedcov.tsv"
    bedcov.write_bytes(b"bed coverage report")
    client = BonsaiApiClient(base_url="https://example.invalid")
    handles = []

    def capture_request(path, *, data, files, **kwargs):
        assert path == "analysis/"
        expected = {
            "file": b"main report",
            "coverage_file": b"coverage report",
            "bedcov_file": b"bed coverage report",
        }
        if with_companion:
            expected["hamronization_file"] = b"AMR report"
        assert set(files) == set(expected)
        assert all(
            field not in data
            for field in ("file", "coverage_file", "bedcov_file", "hamronization_file")
        )
        for field, (_, stream, _) in files.items():
            handles.append(stream)
            assert stream.read() == expected[field]
        return SimpleNamespace(
            status=201, headers={}, data={"analysis_id": "analysis-1", "envelopes": {}}
        )

    monkeypatch.setattr(client, "request_multipart", capture_request)
    result = client.upload_analysis_result(
        UploadAnalysisResultInput(
            sample_id="sample-1", software="kleborate", software_version="3.2.4",
            file=main, hamronization_file=companion if with_companion else None,
            coverage_file=coverage, bedcov_file=bedcov,
        )
    )

    assert result.analysis_id == "analysis-1"
    assert all(stream.closed for stream in handles)
