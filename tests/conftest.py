"""Pytest configuration and fixtures."""

import pytest


def pytest_configure(config):
    """Configure pytest with asyncio support."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
