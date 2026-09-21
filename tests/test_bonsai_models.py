"""Tests for the Bonsai API client models."""

import pytest

from bonsai_libs.api_client.bonsai.models import SampleInfoInput


def test_sample_info_input_sends_groups():
    sample = SampleInfoInput(sample_name="s1", groups=["01a0b4de-fe36-7702-849d-c1790d12e29e"])
    assert sample.model_dump(mode="json")["groups"] == ["01a0b4de-fe36-7702-849d-c1790d12e29e"]


def test_sample_info_input_groups_default_empty():
    assert SampleInfoInput(sample_name="s1").groups == []


def test_create_group_requires_a_slug():
    from pydantic import ValidationError

    from bonsai_libs.api_client.bonsai.models import CreateGroupInput

    with pytest.raises(ValidationError):
        CreateGroupInput.model_validate({"display_name": "S. aureus"})
    group = CreateGroupInput.model_validate({"group": "saureus", "display_name": "S. aureus"})
    assert group.model_dump(mode="json")["group"] == "saureus"
