"""Basic in-memory store implementation"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi_uws.models import JobSummary
from fastapi_uws.models.types import ExecutionPhase
from fastapi_uws.stores.base import BaseUWSStore

RESULT_EXPIRATION_SEC = 24 * 60 * 60  # 1 day in seconds
MAX_EXPIRATION_TIME = RESULT_EXPIRATION_SEC * 3  # the maximum time a job could be updated to


class InMemoryStore(BaseUWSStore):
    """
    Basic in-memory store implementation
    """

    def __init__(self, config, default_expiry=RESULT_EXPIRATION_SEC, max_expiry=MAX_EXPIRATION_TIME):
        self.data = {}
        self.default_expiry = default_expiry
        self.max_expiry = max_expiry

    def get_job(self, job_id):
        """Get a job by its ID."""
        current_time = datetime.now(timezone.utc)

        job: JobSummary = self.data.get(job_id)

        destruction = job.destruction_time
        if destruction and destruction < current_time:
            self.delete(job_id)

        return self.data.get(job_id)

    def get_jobs(self, owner_id=None):
        """Get all jobs. Optionally filter by owner_id."""
        all_jobs: list[JobSummary] = list(self.data.values())
        if owner_id:
            all_jobs = [job for job in all_jobs if job.owner_id == owner_id]
        return all_jobs

    def add_job(self, parameters, owner_id: str = None, run_id: str = None):
        """Add a job to the store"""
        job_id = str(uuid4())

        job = JobSummary(
            job_id=job_id,
            owner_id=owner_id,
            run_id=run_id,
            phase=ExecutionPhase.PENDING,
            creation_time=datetime.now(timezone.utc),
            destruction=datetime.now(timezone.utc) + timedelta(seconds=self.default_expiry),
        )

        self.data[job_id] = job

        return job_id

    def update_job(self, job: JobSummary):
        """Update a job in the store."""

        creation_time = job.creation_time
        destruction_time = job.destruction_time

        max_destruction_time = creation_time + timedelta(seconds=self.max_expiry)

        job.destruction_time = min(destruction_time, max_destruction_time)

        self.data[job.job_id] = job

    def delete(self, job_id):
        """Delete a job from the store."""
        if job_id in self.data:
            del self.data[job_id]
