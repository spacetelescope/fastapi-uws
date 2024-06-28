"""Tests for `fastapi_uws` package."""

import time
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from fastapi_uws.models import ErrorSummary, JobSummary, ResultReference, Results
from fastapi_uws.service import uws_store

SIMPLE_PARAMETERS = [
    {"value": "SELECT * FROM TAP_SCHEMA.tables", "id": "QUERY", "by_reference": False},
    {"value": "ADQL", "id": "LANG", "by_reference": False},
]


def build_test_job(client: TestClient, owner_id: str = None, run_id: str = None):
    response = client.request(
        "POST",
        "/uws",
        json={"parameter": SIMPLE_PARAMETERS, "ownerId": owner_id, "runId": run_id},
    )

    assert response.status_code == 200
    assert response.json()["jobId"] is not None
    return response.json()["jobId"]


class TestUWSAPI:
    """Test basic API functionality"""

    def test_create_job(self, client: TestClient):
        """Test simple job creation works"""
        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")

        job_summary = resp.json()

        assert resp.status_code == 200
        assert job_summary["jobId"] == job_id
        assert job_summary["phase"] == "PENDING"

        assert job_id is not None

    def test_delete_job(self, client: TestClient):
        """Test job deletion"""

        job_id = build_test_job(client)

        # make sure the job appears in the list
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert job_id in [job["jobId"] for job in job_list["jobref"]]

        # delete the job
        resp = client.request("DELETE", f"/uws/{job_id}", follow_redirects=False)
        assert resp.status_code == 303

        # make sure the job is gone
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert job_id not in [job["jobId"] for job in job_list["jobref"]]

    def test_get_destruction(self, client: TestClient):
        """Test job destruction time"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = resp.json()

        destruction_time = datetime.fromisoformat(job_summary["destructionTime"])

        assert destruction_time > datetime.now(timezone.utc)

    def test_get_error_summary(self, client: TestClient):
        """Test job error summary"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = resp.json()

        assert job_summary["errorSummary"] is None

        # add an error summary
        job = JobSummary(**job_summary)
        job.error_summary = ErrorSummary(message="Something went wrong", type="fatal")

        uws_store.update_job(job)

        # check the error summary
        resp = client.request("GET", f"/uws/{job_id}/error")
        assert resp.status_code == 200

        error_summary = resp.json()

        assert error_summary["message"] == "Something went wrong"
        assert error_summary["type"] == "fatal"

    def test_get_execution_duration(self, client: TestClient):
        """Test job execution duration"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = resp.json()

        assert job_summary["executionDuration"] == 0

        # add an execution duration
        job = JobSummary(**job_summary)
        job.execution_duration = 100

        uws_store.update_job(job)

        # check the execution duration
        resp = client.request("GET", f"/uws/{job_id}/executionduration")
        assert resp.status_code == 200

        execution_duration = resp.json()

        assert execution_duration == 100

    def test_get_owner_id(self, client: TestClient):
        """Test job owner ID"""

        job_id = build_test_job(client, owner_id="anonuser")

        resp = client.request("GET", f"/uws/{job_id}/owner")
        assert resp.status_code == 200
        assert resp.text == "anonuser"

    def test_get_parameters(self, client: TestClient):
        """Test fetching job parameters endpoint"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}/parameters")
        assert resp.status_code == 200

        parameters = resp.json()

        assert parameters["parameter"] is not None

        param_list = parameters["parameter"]

        assert len(param_list) == len(SIMPLE_PARAMETERS)

        for param in param_list:
            assert param["id"] in ["QUERY", "LANG"]
            assert param["value"] in ["SELECT * FROM TAP_SCHEMA.tables", "ADQL"]

    def test_get_phase(self, client: TestClient):
        """Test getting the job phase"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}/phase")
        assert resp.status_code == 200
        assert resp.text == "PENDING"

    def test_get_results(self, client: TestClient):
        """Test getting the job results"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = JobSummary(**resp.json())

        # Add some results
        result_list = [
            ResultReference(id="result1", href="/result1"),
            ResultReference(id="result2", href="/result2"),
        ]
        job_summary.results = Results(result=result_list)
        uws_store.update_job(job_summary)

        # fetch the results
        resp = client.request("GET", f"/uws/{job_id}/results")
        assert resp.status_code == 200

        results = resp.json()

        assert results["result"] != None
        assert len(results["result"]) == 2

        assert results["result"][0]["id"] == "result1"
        assert results["result"][0]["href"] == "/result1"
        assert results["result"][1]["id"] == "result2"
        assert results["result"][1]["href"] == "/result2"

    def test_get_quote(self, client: TestClient):
        """Test get the job quote"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = resp.json()
        assert job_summary["quote"] is None

        # add a quote
        quote_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        quote_time = quote_time.isoformat()

        job_summary = JobSummary(**job_summary)
        job_summary.quote = quote_time
        uws_store.update_job(job_summary)

        # fetch the quote
        resp = client.request("GET", f"/uws/{job_id}/quote")
        assert resp.status_code == 200

        quote = resp.text
        assert quote == quote_time


class TestJobList:
    """Test fetching and filtering the job list"""

    def test_get_job_list(self, client: TestClient):
        """Basic job list get"""
        pass

    def test_single_phase_filter(self, client: TestClient):
        """Test filtering by a single phase"""
        pass

    def test_multiple_phase_filter(self, client: TestClient):
        """Test filtering by multiple phases"""
        pass

    def test_last_filter(self, client: TestClient):
        """Test filtering by last N jobs"""
        pass

    def test_after_filter(self, client: TestClient):
        """Test filtering by jobs after a certain time"""
        pass

    def test_phase_after_filter(self, client: TestClient):
        """Test filtering by phase and after time"""
        pass

    def test_phase_last_filter(self, client: TestClient):
        """Test filtering by phase and last N jobs"""
        pass

    def test_phase_after_last_filter(self, client: TestClient):
        """Test filtering by phase, after time, and last N jobs"""
        pass


class TestUpdateJob:
    """Tests updating job properties"""

    def test_post_update_job(self, client: TestClient):
        """Test updating the /{job} endpoint"""
        pass

    def test_update_job_destruction(self, client: TestClient):
        """Test updating the job destruction time"""
        pass

    def test_update_job_execution_duration(self, client: TestClient):
        """Test updating the job execution duration"""
        pass

    def test_update_job_phase(self, client: TestClient):
        """Test updating the job phase"""
        pass

    def test_update_job_parameters(self, client: TestClient):
        """Test updating the job parameters"""
        pass
