"""Shared test fixtures for solidea-sizing-assistant."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from app.main import app

    return TestClient(app)
