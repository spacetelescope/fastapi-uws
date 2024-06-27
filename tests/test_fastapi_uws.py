"""Tests for `fastapi_uws` package."""

import time
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

SIMPLE_PARAMETERS = {
    "parameter": [
        {"value": "SELECT * FROM TAP_SCHEMA.tables", "id": "QUERY", "by_reference": False},
        {"value": "ADQL", "id": "LANG", "by_reference": False},
    ]
}


def build_test_job(client: TestClient):
    response = client.request(
        "POST",
        "/uws",
        json=SIMPLE_PARAMETERS,
    )

    assert response.status_code == 200
    assert response.json()["jobId"] is not None
    return response.json()["jobId"]


class UWSTests:

    def test_create_job(self, client: TestClient):
        """Test simple job creation works"""
        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")

        job_summary = resp.json()

        assert resp.status_code == 200
        assert job_summary["jobId"] == job_id
        assert job_summary["phase"] == "PENDING"

        assert job_id is not None

# get job
# delete job
# get destruction
# get error summary
# get execution duration
# get job list
# job list filtering
# get owner
# get parameters
# get phase
# get results
# get quote
# 404's for the above
# post update job
# post update job destruction
# post update job execution duration
# post update job phase
# post update job parameters