import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_uws.router.uws_router import uws_router
from fastapi_uws.settings import get_store_instance, get_worker_instance


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(uws_router)

    return app


@pytest.fixture
def store():
    """Fixture to get a fresh store instance for each test."""
    test_store = get_store_instance()
    test_store.data = {}
    return test_store


@pytest.fixture
def worker():
    """Fixture to get a fresh worker instance for each test."""
    return get_worker_instance()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
