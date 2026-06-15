"""Compact Bonsai API client composing area-specific mixins.

The large implementation was split across smaller mixins for maintainability:
- `auth.py` (AuthMixin)
- `users.py` (UsersMixin)
- `groups.py` (GroupsMixin)
- `samples.py` (SamplesMixin)
- `reference.py` (ReferenceMixin)

This module composes those mixins with the shared `BaseClient`.
"""

from bonsai_libs.api_client.core.base import BaseClient

from .auth import AuthMixin
from .users import UsersMixin
from .groups import GroupsMixin
from .samples import SamplesMixin
from .reference import ReferenceMixin


class BonsaiApiClient(BaseClient, AuthMixin, UsersMixin, GroupsMixin, SamplesMixin, ReferenceMixin):
    """High-level interface to the Bonsai API composed from smaller mixins."""
