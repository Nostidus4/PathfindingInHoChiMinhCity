"""Fixture dùng chung cho mọi test: mock graph, mock provider, config."""

import pytest

from src.config import SimConfig
from src.mocks import MockGraph, MockTrafficProvider


@pytest.fixture
def mock_graph() -> MockGraph:
    return MockGraph()


@pytest.fixture
def mock_provider() -> MockTrafficProvider:
    return MockTrafficProvider()


@pytest.fixture
def cfg() -> SimConfig:
    return SimConfig.load()
