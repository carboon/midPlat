"""
Pytest configuration and fixtures for Matchmaker Service tests
"""

import pytest
import sys
import os

# Add matchmaker service source directory to path for imports
# This allows tests to import from the matchmaker module
matchmaker_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'matchmaker_service',
    'matchmaker'
)
sys.path.insert(0, matchmaker_path)


@pytest.fixture(autouse=True)
def clear_server_store():
    """
    Automatically clear the global server store before and after each test.
    This prevents state pollution between tests.
    """
    from main import store
    
    # Clear before test
    store.servers.clear()
    
    yield
    
    # Clear after test
    store.servers.clear()


@pytest.fixture
def test_client():
    """
    Provide a FastAPI TestClient for making requests.
    """
    from fastapi.testclient import TestClient
    from main import app
    
    return TestClient(app)
