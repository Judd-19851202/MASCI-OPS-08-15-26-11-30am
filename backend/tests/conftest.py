import pytest
import asyncio

# Use function-scoped event loop for proper teardown
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
