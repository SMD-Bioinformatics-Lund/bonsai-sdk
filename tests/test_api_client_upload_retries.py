"""Exercise retry behavior after Requests consumes multipart file streams."""

import json
from email import policy
from email.parser import BytesParser
from io import BytesIO, UnsupportedOperation

import pytest
import requests
from requests.adapters import BaseAdapter

from bonsai_libs.api_client.bonsai.client import BonsaiApiClient
from bonsai_libs.api_client.bonsai.models import UploadAnalysisResultInput
from bonsai_libs.api_client.core.base import BaseClient
from bonsai_libs.api_client.core.exceptions import ApiRequestFailed


class UploadAdapter(BaseAdapter):
    """Record real prepared multipart bodies, then simulate transport failures."""

    def __init__(self, error=requests.Timeout, failures=1):
        self.error = error
        self.failures = failures
        self.uploads = []

    def send(self, request, **kwargs):
        message = BytesParser(policy=policy.default).parsebytes(
            f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode() + request.body
        )
        self.uploads.append(
            [
                (
                    part.get_param("name", header="content-disposition"),
                    part.get_filename(),
                    part.get_payload(decode=True),
                )
                for part in message.iter_parts()
            ]
        )
        if len(self.uploads) <= self.failures:
            raise self.error("Simulated failure after preparing the upload")
        response = requests.Response()
        response.status_code = 201
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps({"analysis_id": "analysis-123"}).encode()
        response.request = request
        return response

    def close(self):
        pass


def upload_client(client_type=BaseClient, *, retries=2, **adapter_kwargs):
    adapter = UploadAdapter(**adapter_kwargs)
    session = requests.Session()
    session.mount("https://", adapter)
    client = client_type(
        base_url="https://bonsai.test", session=session, retries=retries, backoff=0
    )
    return client, adapter


@pytest.mark.parametrize("error", [requests.Timeout, requests.ConnectionError])
@pytest.mark.parametrize("failures", [1, 2])
def test_analysis_upload_retries_preserve_all_files(tmp_path, error, failures):
    client, adapter = upload_client(BonsaiApiClient, error=error, failures=failures)
    payloads = {
        "file": b"x" * 37099,
        "coverage_file": b"coverage\n1\t42\n",
        "bedcov_file": b"chr1\t0\t42\n",
    }
    paths = {}
    for field, payload in payloads.items():
        paths[field] = tmp_path / f"{field}.txt"
        paths[field].write_bytes(payload)

    response = client.upload_analysis_result(
        UploadAnalysisResultInput(
            sample_id="sample-123", software="samtools", software_version="1.0", **paths
        )
    )

    assert response.analysis_id == "analysis-123"
    assert len(adapter.uploads) == failures + 1
    for upload in adapter.uploads:
        assert {name: data for name, filename, data in upload if filename} == payloads
        assert ("sample_id", None, b"sample-123") in upload


@pytest.mark.parametrize("file_format", ["bare", "tuple2", "tuple3", "tuple4", "list"])
def test_retries_preserve_file_content_for_requests_file_formats(file_format):
    client, adapter = upload_client()
    stream = BytesIO(b"payload")
    value = {
        "bare": stream,
        "tuple2": ("result.txt", stream),
        "tuple3": ("result.txt", stream, "text/plain"),
        "tuple4": ("result.txt", stream, "text/plain", {"X-Part": "value"}),
        "list": ["result.txt", stream],
    }[file_format]

    client.request_multipart("analysis/", files={"file": value}, expected_status=(201,))

    assert [upload[0][2] for upload in adapter.uploads] == [b"payload", b"payload"]
    assert not stream.closed


def test_retry_rewinds_a_partially_read_stream_to_the_beginning():
    client, adapter = upload_client()
    stream = BytesIO(b"prefix:payload")
    stream.read(7)

    client.request_multipart("analysis/", files={"file": stream}, expected_status=(201,))

    assert [upload[0][2] for upload in adapter.uploads] == [b"payload", b"prefix:payload"]


def test_repeated_file_fields_and_immutable_parts():
    client, adapter = upload_client()
    files = [
        ("file", ("first.txt", BytesIO(b"first"))),
        ("file", ("second.txt", BytesIO(b"second"))),
        ("bytes", ("bytes.txt", b"bytes")),
        ("text", ("text.txt", "text")),
    ]

    client.post("analysis/", files=files, expected_status=(201,))

    assert (
        adapter.uploads
        == [
            [
                ("file", "first.txt", b"first"),
                ("file", "second.txt", b"second"),
                ("bytes", "bytes.txt", b"bytes"),
                ("text", "text.txt", b"text"),
            ]
        ]
        * 2
    )


class NonSeekableStream(BytesIO):
    def tell(self):
        raise UnsupportedOperation("Cannot tell")

    def seek(self, *args):
        raise UnsupportedOperation("Cannot seek")


class SeekableWithoutTellStream(BytesIO):
    def tell(self):
        raise UnsupportedOperation("Cannot tell")


def test_retry_does_not_require_tell():
    client, adapter = upload_client()
    client.request_multipart(
        "analysis/", files={"file": SeekableWithoutTellStream(b"payload")}, expected_status=(201,)
    )
    assert [upload[0][2] for upload in adapter.uploads] == [b"payload", b"payload"]


def test_unrewindable_stream_fails_without_sending_an_empty_retry():
    client, adapter = upload_client()
    stream = NonSeekableStream(b"payload")

    with pytest.raises(ApiRequestFailed, match="Cannot retry.*rewind"):
        client.request_multipart("analysis/", files={"file": stream}, expected_status=(201,))

    assert len(adapter.uploads) == 1
    assert adapter.uploads[0][0][2] == b"payload"
    assert not stream.closed


@pytest.mark.parametrize("retries", [0, 2])
def test_nonseekable_stream_can_succeed_without_a_retry(retries):
    client, adapter = upload_client(retries=retries, failures=0)
    client.request_multipart(
        "analysis/", files={"file": NonSeekableStream(b"payload")}, expected_status=(201,)
    )
    assert adapter.uploads[0][0][2] == b"payload"


@pytest.mark.parametrize("retries", [0, 1, 2])
def test_exhausted_upload_retries_raise_and_keep_the_full_payload(retries):
    client, adapter = upload_client(retries=retries, failures=retries + 1)
    with pytest.raises(ApiRequestFailed):
        client.request_multipart(
            "analysis/", files={"file": BytesIO(b"payload")}, expected_status=(201,)
        )
    assert [upload[0][2] for upload in adapter.uploads] == [b"payload"] * (retries + 1)


def test_sourmash_upload_retries_preserve_signature():
    client, adapter = upload_client(BonsaiApiClient)
    client.upload_sourmash_signature("sample-123", signature_file=BytesIO(b"signature"))
    assert [upload[0] for upload in adapter.uploads] == [
        ("signature", "signature.json", b"signature")
    ] * 2
