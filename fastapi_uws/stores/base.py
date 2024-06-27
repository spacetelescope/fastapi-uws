"""Base class for storing UWS jobs / results."""

from datetime import datetime
from typing import Any

from fastapi_uws.models import JobSummary, Parameters


class UWSStore:
    """Base class for storing UWS jobs / results."""

    def get_job(self, job_id: str) -> JobSummary:
        """Get a job by its ID.

        Args:
            job_id: The ID of the job to get.

        Returns:
            The job with the given ID.

        Raises:
            KeyError: If no job with the given ID exists.
        """
        raise NotImplementedError

    def get_jobs(self) -> list[JobSummary]:
        """Get all jobs.

        Returns:
            A list of all jobs.
        """
        raise NotImplementedError

    def add_job(self, parameters: Parameters) -> JobSummary.job_id:
        """Add a job.

        Args:
            parameters: The service-specific parameters with which to create the job.
        """
        raise NotImplementedError

    def update_job(self, job: JobSummary) -> None:
        """Update a job.

        Args:
            job: The job to update.
        """
        raise NotImplementedError

    def delete_job(self, job_id: str) -> None:
        """Delete a job by its ID.

        Args:
            job_id: The ID of the job to delete.
        """
        raise NotImplementedError
