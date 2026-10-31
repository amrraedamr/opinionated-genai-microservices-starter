"""Fixtures shared by every suite that exercises the broker contract."""

import pytest

from base.services.broker.memory import InMemoryBroker
from base.services.common.meta import Singleton


@pytest.fixture
def broker() -> InMemoryBroker:
    """A clean in-memory broker, with singleton state from prior tests dropped."""
    Singleton.purge()
    return InMemoryBroker()
