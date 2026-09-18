"""Tests for Bonsai API client models."""

import pytest
from pydantic import ValidationError

from bonsai_libs.api_client.bonsai.models import CreateGroupInput


def test_create_group_input_requires_group_id():
    """Groups are created with a readable ID such as ``saureus``, not a generated one."""
    with pytest.raises(ValidationError):
        CreateGroupInput(display_name="S. aureus")


def test_create_group_input_sends_group_id():
    group = CreateGroupInput(group_id="saureus", display_name="S. aureus")
    assert group.model_dump(mode="json")["group_id"] == "saureus"
