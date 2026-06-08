"""API interface to the Bonsai API."""

from typing import Any, BinaryIO
import logging
import mimetypes
from http import HTTPStatus

LOG = logging.getLogger(__name__)

from bonsai_libs.api_client.core.auth import BearerTokenAuth
from bonsai_libs.api_client.core.base import BaseClient
from bonsai_libs.api_client.core.exceptions import ClientError, UnauthorizedError

from .models import (
    CreateGroupInput,
    CreateSampleResponse,
    CreateUserInput,
    GenomicResourceInput,
    GroupResponse,
    OpHeaders,
    PipelineRunInput,
    SampleInfoInput,
    UploadAnalysisResultInput,
    UploadAnalysisResultResponse,
    UploadResultMeta,
    UserResponse,
)


class BonsaiApiClient(BaseClient):
    """High-level interface to the Bonsai API."""

    # ----------------------------
    # Authentication
    # ----------------------------
    def authenticate_user(self, username: str, password: str, *, headers: OpHeaders = None) -> bool:
        """Authenticate using username/password and configure bearer token.

        Returns True if login was successful.
        """
        try:
            resp = self.request_form(
                "POST",
                "token",
                data={"username": username, "password": password},
                headers=headers,
                expected_status=(HTTPStatus.OK,),
            )
        except UnauthorizedError:
            LOG.error("Invalid login credentials for user=%s", username)
            return False
        except ClientError as exc:
            LOG.error(
                "Something went wrong when authenticating user %s; %s",
                username,
                exc,
            )
            raise

        data = resp.data or {}
        token_type = str(data.get("token_type", "")).lower()
        access_token = data.get("access_token")

        if token_type == "bearer" and access_token:
            self.auth = BearerTokenAuth(token=access_token)
            return True

        LOG.error("Unexpected token response: %s", resp)
        return False

    # ----------------------------
    # Users
    # ----------------------------

    def create_user(self, user: CreateUserInput, *, headers: OpHeaders = None) -> UserResponse:
        resp = self.request_json(
            "POST",
            "users/",
            json=user.model_dump(mode="json"),
            headers=headers,
            expected_status=(HTTPStatus.CREATED,),
        )
        return UserResponse.model_validate(resp.data)

    def get_user(self, username: str, *, headers: OpHeaders = None) -> UserResponse:
        """Query the API for a user with username."""
        resp = self.request_json(
            "GET",
            f"users/{username}",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return UserResponse.model_validate(resp.data)

    def get_current_user(self, *, headers: OpHeaders = None) -> UserResponse:
        """Query the API for the current user."""
        resp = self.request_json(
            "GET",
            "users/me",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return UserResponse.model_validate(resp.data)

    def get_users(self, *, headers: OpHeaders = None) -> list[UserResponse]:
        """Query the API for all users."""
        resp = self.request_json(
            "GET",
            "users/",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        data = resp.data or []
        return [UserResponse.model_validate(user) for user in data]

    def update_user(
        self, username: str, user_data: dict[str, Any], *, headers: OpHeaders = None
    ) -> UserResponse:
        """Update user information."""
        resp = self.request_json(
            "PUT",
            f"users/{username}",
            json=user_data,
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return UserResponse.model_validate(resp.data)

    def delete_user(self, username: str, *, headers: OpHeaders = None) -> dict[str, Any]:
        """Delete a user."""
        resp = self.request_json(
            "DELETE",
            f"users/{username}",
            headers=headers,
            expected_status=(HTTPStatus.OK, HTTPStatus.NO_CONTENT),
        )
        return resp.data or {}

    # ----------------------------
    # Groups
    # ----------------------------

    def create_group(self, group: CreateGroupInput, *, headers: OpHeaders = None) -> GroupResponse:
        """Create a group in Bonsai."""

        payload = group.model_dump(mode="json")
        resp = self.request_json(
            "POST", "groups/", json=payload, headers=headers, expected_status=(HTTPStatus.CREATED,)
        )

        return GroupResponse.model_validate(resp.data)

    def get_group(self, group_id: str, *, headers: OpHeaders = None) -> GroupResponse:
        """Query the API for a group using group id."""
        resp = self.request_json(
            "GET",
            f"groups/{group_id}",
            headers=headers,
            expected_status=(HTTPStatus.OK,),
        )
        return GroupResponse.model_validate(resp.data)

    # ----------------------------
    # Samples
    # ----------------------------

    def create_sample(
        self, sample_info: SampleInfoInput, *, headers: OpHeaders = None
    ) -> CreateSampleResponse:
        """Create a new sample in Bonsai."""

        payload = sample_info.model_dump(mode="json")

        try:
            resp = self.request_json(
                "POST",
                "samples/",
                json=payload,
                headers=headers,
                expected_status=(HTTPStatus.CREATED,),
            )
        except ClientError as exc:
            LOG.error(
                "Something went wrong creating the sample; %s",
                exc,
                extra={"payload": payload},
            )
            raise

        return CreateSampleResponse.model_validate(resp.data)

    def add_samples_to_group(
        self, group_id: str, *, sample_ids: list[str], headers: OpHeaders = None
    ):
        """Add sample to group."""

        url = f"groups/{group_id}/samples"
        params = {"s": sample_ids}

        try:
            resp = self.put(
                url,
                params=params,
                headers=headers,
                expected_status=(HTTPStatus.OK,),
            )
        except ClientError as exc:
            LOG.error(
                "Something went wrong creating the sample; %s",
                exc,
                extra={"params": params},
            )
            raise

        return resp.data
    
    def add_reference_genome_to_sample(
        self, 
        sample_id: str, *, reference_genome_id: str, headers: OpHeaders = None,
    ) -> dict[str, Any]:
        """Associate a reference genome with a sample.
        
        Returns information of the reference genome."""
        try:
            resp = self.request_json(
                "PUT",
                f"samples/{sample_id}/reference-genome",
                headers=headers,
                json={"reference_genome_id": reference_genome_id},
            )
        except UnauthorizedError:
            LOG.error("Unauthorised when adding a reference genome for sample=%s", sample_id)
            raise
        except ClientError:
            LOG.error(
                "Something went wrong when associating reference genome id=%s to sample=%s",
                reference_genome_id,
                sample_id,
            )
            raise
        return resp.data
    
    def add_annotation_track_to_sample(
        self, sample_id: str, *, track: GenomicResourceInput, headers: OpHeaders = None,
    ) -> dict[str, Any]:
        """Add genomic resource to sample."""
        payload = track.model_dump(exclude_none=True)
        try:
            resp = self.request_json(
                "POST",
                f"samples/{sample_id}/resources",
                headers=headers,
                json=payload,
            )
        except UnauthorizedError:
            LOG.error("Unauthorised when adding a reference genome for sample=%s", sample_id)
            raise
        except ClientError:
            LOG.error(
                "Something went wrong when adding a genomic resource to sample; id=%s",
                sample_id,
            )
            raise
        return resp.data
    
    def upload_sourmash_signature(
        self, sample_id: str, *, signature_file: BinaryIO, filename: str = "signature.json", headers: OpHeaders = None
    ) -> str:
        """Upload sourmash signature to sample"""
        try:
            resp = self.request_multipart(
                f"samples/{sample_id}/signature",
                headers=headers,
                files={"signature": (filename, signature_file)},
                expected_status=(HTTPStatus.OK, HTTPStatus.CREATED),
            )
        except UnauthorizedError:
            LOG.error("Unauthorised when uploading sourmash signature for sample=%s", sample_id)
            raise
        except ClientError:
            LOG.error(
                "Something went wrong when uploading a sourmash signature for sample=%s",
                sample_id,
            )
            raise
        return resp.data

    def upload_ska_index(
        self, sample_id: str, *, index_path: str, force: bool = False, headers: OpHeaders = None
    ) -> str:
        """Upload sourmash signature to sample"""
        try:
            resp = self.request_json(
                "POST",
                f"samples/{sample_id}/ska_index",
                json={"index": index_path, "force": force},
                headers=headers,
            )
        except UnauthorizedError:
            LOG.error("Unauthorised when uploading ska index for sample=%s", sample_id)
            raise
        except ClientError:
            LOG.error("Something went wrong when uploading ska index for sample=%s", sample_id)
            raise
        return resp.data

    def add_pipeline_run(
        self, sample_id: str, *, pipeline_run: PipelineRunInput, headers: OpHeaders = None
    ) -> str:
        """Add a pipeline run ID to a sample."""
        payload = pipeline_run.model_dump(mode="json")
        try:
            resp = self.request_json(
                "POST",
                f"samples/{sample_id}/pipeline-runs",
                json=payload,
                headers=headers,
                expected_status=(HTTPStatus.OK, HTTPStatus.CREATED),
            )
        except UnauthorizedError:
            LOG.error("Unauthorised when creating a pipeline run for sample=%s", sample_id)
            raise
        except ClientError as exc:
            LOG.error(
                "Something went wrong when adding a pipeline run to sample=%s",
                sample_id,
                extra={"exception": exc, "payload": payload},
            )
            raise
        return resp.data  # return inserted pipeline run ID

    def upload_analysis_result(
        self, result: UploadAnalysisResultInput, *, headers: OpHeaders = None, force: bool = False
    ) -> UploadAnalysisResultResponse:
        """Upload a analysis results to a existing sample."""

        data = result.model_dump(exclude={"file"})
        data["force"] = force

        mime = mimetypes.guess_type(result.file.name)[0] or "application/octet-stream"

        with result.file.open("rb") as fh:
            files = {"file": (result.file.name, fh, mime)}

            try:
                resp = self.request_multipart(
                    "analysis/",
                    data=data,
                    files=files,
                    headers=headers,
                    expected_status=(HTTPStatus.CREATED,),
                )
            except UnauthorizedError as exc:
                LOG.error("Failed authenticating user=%s", result.sample_id, exc_info=exc)
                raise

            request_id = resp.headers.get("x-request-id") or resp.headers.get("X-Request-Id")
            meta = UploadResultMeta(status=resp.status, request_id=request_id)

            body = resp.data or {}
            return UploadAnalysisResultResponse(
                sample_id=result.sample_id,
                pipeline_run_id=result.pipeline_run_id,
                analysis_id=body.get("analysis_id"),
                software=result.software,
                software_version=result.software_version,
                envelopes=body.get("envelopes", {}),
                meta=meta,
            )
    
    def get_igv_config(self, sample_id: str, *, analysis_id: str | None = None, variant_id: str | None = None, headers: OpHeaders = None) -> dict[str, Any]:
        """Get a IGV configuration for a sample.
        
        Optional center the view on a variant by providing a analysis_id and variant_id
        """
        try:
            resp = self.request_json(
                "GET",
                f"samples/{sample_id}/igv-config",
                json={'analysis_id': analysis_id, 'variant_id': variant_id},
                headers=headers,
            )
        except UnauthorizedError as exc:
            LOG.error("Failed authenticating user", exc_info=exc)
            raise
        return resp.data