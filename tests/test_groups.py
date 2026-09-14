"""Tests for group-related API client methods."""

from types import SimpleNamespace
from unittest.mock import Mock

from bonsai_libs.api_client.bonsai.groups import GroupsMixin
from bonsai_libs.api_client.bonsai.models import GroupColumnResponse


def test_get_valid_group_columns_parses_bare_list_response():
    """Group columns follow the API's top-level list response contract."""
    client = GroupsMixin()
    client.request_json = Mock(
        return_value=SimpleNamespace(
            data=[
                {
                    "id": "sample_id",
                    "type": "string",
                    "source": "static",
                    "default_visible": True,
                    "filterable": True,
                    "sortable": True,
                    "visible": True,
                    "searchable": True,
                    "order": 1,
                    "locked": False,
                    "label": "Sample ID",
                    "overridden_fields": [],
                }
            ]
        )
    )

    columns = client.get_valid_group_columns("group-1")

    assert columns == [
        GroupColumnResponse(
            id="sample_id",
            type="string",
            source="static",
            default_visible=True,
            filterable=True,
            sortable=True,
            visible=True,
            searchable=True,
            order=1,
            locked=False,
            label="Sample ID",
            overridden_fields=[],
        )
    ]
    client.request_json.assert_called_once_with(
        "GET",
        "groups/group-1/columns",
        params=None,
        headers=None,
        expected_status=(200,),
    )
