import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_uws.router.uws_router import uws_router


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(uws_router)

    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
