import pytest
import asyncio
from services.api.db.database import engine

# 1. Force a single, stable event loop for the entire test runtime session
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

# 2. Automatically dispose and clean up stale DB pool connections after the suite finishes
@pytest.fixture(scope="session", autouse=True)
async def cleanup_database_pool():
    yield
    # Explicitly clear out all connection fairies attached to previous loops
    await engine.dispose()