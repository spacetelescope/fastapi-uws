"""Basic in-memory store implementation"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi_uws.models import JobSummary, Parameter, Parameters
from fastapi_uws.models.types import ExecutionPhase
from fastapi_uws.settings import app_settings
from fastapi_uws.stores.base import BaseUWSStore


class InMemoryStore(BaseUWSStore):
    """
    Basic in-memory store implementation
    """

    def __init__(self):
        self.data = {}
        self.default_expiry = app_settings.store.DEFAULT_EXPIRY
        self.max_expiry = app_settings.store.MAX_EXPIRY

    def get_job(self, job_id):
        """Get a job by its ID."""
        current_time = datetime.now(timezone.utc)

        job: JobSummary = self.data.get(job_id)

        destruction = job.destruction_time
        if destruction and destruction < current_time:
            self.delete_job(job_id)

        return self.data.get(job_id)

    def get_jobs(self):
        """Get all jobs."""
        all_jobs: list[JobSummary] = list(self.data.values())
        return all_jobs

    def add_job(self, parameters: list[Parameter], owner_id: str = None, run_id: str = None):
        """Add a job to the store"""
        job_id = str(uuid4())

        job = JobSummary(
            job_id=job_id,
            owner_id=owner_id,
            run_id=run_id,
            phase=ExecutionPhase.PENDING,
            creation_time=datetime.now(timezone.utc),
            destruction_time=datetime.now(timezone.utc) + timedelta(seconds=self.default_expiry),
            parameters=Parameters(parameter=parameters),
        )

        self.data[job_id] = job

        return job_id

    def save_job(self, job: JobSummary):
        """Update a job in the store."""

        creation_time = job.creation_time
        destruction_time = job.destruction_time

        max_destruction_time = creation_time + timedelta(seconds=self.max_expiry)

        job.destruction_time = min(destruction_time, max_destruction_time)

        self.data[job.job_id] = job

    def delete_job(self, job_id):
        """Delete a job from the store."""
        if job_id in self.data:
            del self.data[job_id]
