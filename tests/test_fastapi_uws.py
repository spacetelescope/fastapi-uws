"""Tests for `fastapi_uws` package."""

import os
import time
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from fastapi_uws.models import ErrorSummary, JobSummary, ResultReference, Results
from fastapi_uws.stores import BaseUWSStore
from fastapi_uws.workers import BaseUWSWorker

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


def assert_id_in_joblist(job_id: str | list[str], job_list: dict):
    """Check if a job ID is in a job list"""
    if isinstance(job_id, str):
        job_id = [job_id]

    for job in job_id:
        assert job in [job["jobId"] for job in job_list["jobref"]]


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
        assert_id_in_joblist(job_id, job_list)

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

        resp = client.request("GET", f"/uws/{job_id}/destruction")
        assert resp.status_code == 200

        destruction = resp.text

        destruction_time = datetime.fromisoformat(destruction)

        assert destruction_time > datetime.now(timezone.utc)

    def test_get_error_summary(self, client: TestClient, store: BaseUWSStore):
        """Test job error summary"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = resp.json()

        assert job_summary["errorSummary"] is None

        # add an error summary
        job = JobSummary(**job_summary)
        job.error_summary = ErrorSummary(message="Something went wrong", type="fatal")

        store.save_job(job)

        # check the error summary
        resp = client.request("GET", f"/uws/{job_id}/error")
        assert resp.status_code == 200

        error_summary = resp.json()

        assert error_summary["message"] == "Something went wrong"
        assert error_summary["type"] == "fatal"

    def test_get_execution_duration(self, client: TestClient, store: BaseUWSStore):
        """Test job execution duration"""

        job_id = build_test_job(client)

        resp = client.request("GET", f"/uws/{job_id}")
        assert resp.status_code == 200

        job_summary = resp.json()

        assert job_summary["executionDuration"] == 0

        # add an execution duration
        job = JobSummary(**job_summary)
        job.execution_duration = 100

        store.save_job(job)

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

    def test_get_results(self, client: TestClient, store: BaseUWSStore):
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
        store.save_job(job_summary)

        # fetch the results
        resp = client.request("GET", f"/uws/{job_id}/results")
        assert resp.status_code == 200

        results = resp.json()

        assert results["result"] is not None
        assert len(results["result"]) == 2

        assert results["result"][0]["id"] == "result1"
        assert results["result"][0]["href"] == "/result1"
        assert results["result"][1]["id"] == "result2"
        assert results["result"][1]["href"] == "/result2"

    def test_get_quote(self, client: TestClient, store: BaseUWSStore):
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
        store.save_job(job_summary)

        # fetch the quote
        resp = client.request("GET", f"/uws/{job_id}/quote")
        assert resp.status_code == 200

        quote = resp.text
        assert quote == quote_time


class TestJobList:
    """Test fetching and filtering the job list"""

    def test_get_job_list(self, client: TestClient, store: BaseUWSStore):
        """Basic job list get"""

        job_ids = []

        for _ in range(10):
            job_ids.append(build_test_job(client))

        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 10
        assert_id_in_joblist(job_ids, job_list)

    def test_single_phase_filter(self, client: TestClient, store: BaseUWSStore):
        """Test filtering by a single phase"""

        pending_job_id = build_test_job(client)
        running_job_id = build_test_job(client)

        # check both jobs are in the list
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 2
        assert_id_in_joblist([pending_job_id, running_job_id], job_list)

        # move the running job to the running phase
        running_job = store.get_job(running_job_id)
        running_job.phase = "EXECUTING"
        store.save_job(running_job)

        resp = client.request("GET", "/uws", params={"PHASE": "EXECUTING"})
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 1
        assert_id_in_joblist(running_job_id, job_list)

    def test_multiple_phase_filter(self, client: TestClient, store: BaseUWSStore):
        """Test filtering by multiple phases"""

        pending_job_id = build_test_job(client)
        running_job_id = build_test_job(client)
        completed_job_id = build_test_job(client)

        # check all jobs are in the list
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 3
        assert_id_in_joblist([pending_job_id, running_job_id, completed_job_id], job_list)

        # move the running job to the running phase and the completed job to the completed phase
        running_job = store.get_job(running_job_id)
        running_job.phase = "EXECUTING"
        store.save_job(running_job)
        completed_job = store.get_job(completed_job_id)
        completed_job.phase = "COMPLETED"
        store.save_job(completed_job)

        # try querying by executing and completed
        resp = client.request("GET", "/uws", params={"PHASE": ["EXECUTING", "COMPLETED"]})
        assert resp.status_code == 200

        job_list = resp.json()

        assert len(job_list["jobref"]) == 2
        assert_id_in_joblist([running_job_id, completed_job_id], job_list)

        # try by pending and completed
        resp = client.request("GET", "/uws", params={"PHASE": ["PENDING", "COMPLETED"]})
        assert resp.status_code == 200

        job_list = resp.json()

        assert len(job_list["jobref"]) == 2
        assert_id_in_joblist([pending_job_id, completed_job_id], job_list)

    def test_last_filter(self, client: TestClient):
        """Test filtering by last N jobs"""

        job_ids = []

        for _ in range(10):
            job_ids.append(build_test_job(client))

        resp = client.request("GET", "/uws", params={"LAST": 5})
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 5
        for job in job_list["jobref"]:
            assert job["jobId"] in job_ids[-5:]

        # check that the creationTime order is correct
        creation_times = [job["creationTime"] for job in job_list["jobref"]]
        assert creation_times == sorted(creation_times, reverse=True)

    def test_after_filter(self, client: TestClient, store: BaseUWSStore):
        """Test filtering by jobs after a certain time"""

        before_filter_id = build_test_job(client)

        time.sleep(1)
        filter_time = datetime.now(timezone.utc)
        time.sleep(1)

        after_filter_id = build_test_job(client)

        # check both jobs are in the list
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 2
        assert_id_in_joblist([before_filter_id, after_filter_id], job_list)

        resp = client.request("GET", "/uws", params={"AFTER": filter_time.isoformat()})
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 1
        assert_id_in_joblist(after_filter_id, job_list)

    def test_phase_after_filter(self, client: TestClient, store: BaseUWSStore):
        """Test filtering by phase and after time.

        Per UWS spec, PHASE/AFTER should be combined with AND logic.
        """

        pending_job_id = build_test_job(client)
        before_filter_running_id = build_test_job(client)

        time.sleep(1)
        filter_time = datetime.now(timezone.utc)
        time.sleep(1)

        after_filter_running_id = build_test_job(client)

        # check all jobs are in the list
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()

        assert len(job_list["jobref"]) == 3
        assert_id_in_joblist([pending_job_id, before_filter_running_id, after_filter_running_id], job_list)

        # move the running jobs to the running phase
        before_filter_running_job = store.get_job(before_filter_running_id)
        before_filter_running_job.phase = "EXECUTING"
        store.save_job(before_filter_running_job)

        after_filter_running_job = store.get_job(after_filter_running_id)
        after_filter_running_job.phase = "EXECUTING"
        store.save_job(after_filter_running_job)

        # try querying by executing and after filter time
        resp = client.request(
            "GET",
            "/uws",
            params={"PHASE": "EXECUTING", "AFTER": filter_time.isoformat()},
        )
        assert resp.status_code == 200

        job_list = resp.json()

        assert len(job_list["jobref"]) == 1
        assert_id_in_joblist(after_filter_running_id, job_list)

    def test_phase_last_filter(self, client: TestClient, store: BaseUWSStore):
        """Test filtering by phase and last N jobs

        Per UWS spec, LAST should be applied after PHASE/AFTER.
        """

        # 3 running jobs, 1 pending job
        # if filtered correctly, we should get the last 2 running jobs, job2 and job3
        # if LAST is incorrectly applied before PHASE, we would only get job3
        running_job1 = build_test_job(client)
        running_job2 = build_test_job(client)
        pending_job = build_test_job(client)
        running_job3 = build_test_job(client)

        # move the running jobs to the running phase
        for job_id in [running_job1, running_job2, running_job3]:
            job = store.get_job(job_id)
            job.phase = "EXECUTING"
            store.save_job(job)

        # check all jobs are in the list
        resp = client.request("GET", "/uws")
        assert resp.status_code == 200

        job_list = resp.json()
        assert len(job_list["jobref"]) == 4
        assert_id_in_joblist([running_job1, running_job2, pending_job, running_job3], job_list)

        resp = client.request("GET", "/uws", params={"PHASE": "EXECUTING", "LAST": 2})
        assert resp.status_code == 200

        job_list = resp.json()

        assert len(job_list["jobref"]) == 2
        assert_id_in_joblist([running_job2, running_job3], job_list)


class TestUpdateJob:
    """Tests updating job properties"""

    def test_post_update_job(self, client: TestClient):
        """Test updating the /{job} endpoint via POST

        Clients may update PHASE, DESTRUCTION, and submit an ACTION.
        """

        # TODO: figure out test worker config

        job_id = build_test_job(client)

        # move the job to the running phase
        resp = client.request("POST", f"/uws/{job_id}", json={"PHASE": "RUN"}, follow_redirects=False)
        assert resp.status_code == 303

        # check the phase
        resp = client.request("GET", f"/uws/{job_id}/phase")
        assert resp.status_code == 200
        assert resp.text == "EXECUTING"

    def test_update_job_destruction(self, client: TestClient):
        """Test updating the job destruction time"""

        job_id = build_test_job(client)

        # get the current destruction time
        resp = client.request("GET", f"/uws/{job_id}/destruction")
        assert resp.status_code == 200

        destruction_time = resp.text

        # update the destruction time
        new_destruction_time = datetime.now(timezone.utc) + timedelta(minutes=5)

        resp = client.request(
            "POST",
            f"/uws/{job_id}/destruction",
            json={"DESTRUCTION": new_destruction_time.isoformat()},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        # check the new destruction time
        resp = client.request("GET", f"/uws/{job_id}/destruction")
        assert resp.status_code == 200

        destruction_time = resp.text
        assert destruction_time == new_destruction_time.isoformat()

    def test_update_job_execution_duration(self, client: TestClient):
        """Test updating the job execution duration"""

        job_id = build_test_job(client)

        # get the current execution duration
        resp = client.request("GET", f"/uws/{job_id}/executionduration")
        assert resp.status_code == 200

        execution_duration = resp.text

        # update the execution duration
        new_execution_duration = "100"

        resp = client.request(
            "POST",
            f"/uws/{job_id}/executionduration",
            json={"EXECUTIONDURATION": new_execution_duration},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        # check the new execution duration
        resp = client.request("GET", f"/uws/{job_id}/executionduration")
        assert resp.status_code == 200

        execution_duration = resp.text
        assert execution_duration == new_execution_duration

    def test_update_job_phase(self, client: TestClient):
        """Test updating the job phase"""
        pass

    def test_update_job_parameters(self, client: TestClient):
        """Test updating the job parameters"""
        pass


class Test404Responses:
    """Test accessing non-existent resources"""
