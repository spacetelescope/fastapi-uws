"""Module implementing the service layer of the application."""

import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException

from fastapi_uws.models import Jobs, Parameter, ShortJobDescription
from fastapi_uws.models.types import ExecutionPhase, PhaseAction
from fastapi_uws.settings import get_store_instance, get_worker_instance
from fastapi_uws.stores import BaseUWSStore
from fastapi_uws.workers import BaseUWSWorker


class UWSService:
    """Service class implementing the business logic of the application."""

    def __init__(self):
        self.store: BaseUWSStore = get_store_instance()
        self.worker: BaseUWSWorker = get_worker_instance()

    def get_job_summary(self, job_id: str, phase: ExecutionPhase = None, wait: int = None):
        """Get a job by its ID.

        Args:
            job_id: The ID of the job to get.
            phase: The phase to monitor for changes.
            wait: The maximum time to wait for the phase to change.

        Returns:
            The job with the given ID.

        Raises:
            KeyError: If no job with the given ID exists.
        """

        summary = self.store.get_job(job_id)
        if not summary:
            raise HTTPException(404, "Job summary not found")

        if wait is None or summary.phase not in (
            ExecutionPhase.PENDING,
            ExecutionPhase.QUEUED,
            ExecutionPhase.EXECUTING,
        ):
            return summary

        if phase is not None:
            # if the phase we're monitoring is not the current phase, return immediately
            if summary.phase != phase:
                return summary

        current_phase = summary.phase
        start_time = time.monotonic()

        while (time.monotonic() - start_time) < wait:
            new_summary = self.store.get_job(job_id)

            if new_summary is None:
                raise HTTPException(404, "Job summary found missing while polling for phase change")

            if new_summary.phase != current_phase:
                return new_summary

            time.sleep(0.1)

        # we've reached maximum wait time, just return the job summary
        return summary

    def get_job_list(self, phase: list[ExecutionPhase] = None, after: datetime = None, last: int = None):
        """Get all jobs.

        Args:
            phase: The phase or list of phases to filter by.
            after: The date after which to filter.
            last: Return the last N jobs.

        Returns:
            A list of all jobs in the store, filtered by the given parameters.
        """

        all_jobs = self.store.get_jobs()

        # sort by creation time
        all_jobs.sort(key=lambda job: job.creation_time, reverse=True)

        job_list = Jobs(jobref=[], version="1.1")

        for job in all_jobs:
            # apply filters
            if after:
                if job.creation_time < after:
                    continue
            if phase:
                job_phase = ExecutionPhase(job.phase).value
                if job_phase not in phase:
                    continue
            else:
                if job.phase == ExecutionPhase.ARCHIVED:
                    # jobs with the phase "ARCHIVED" should not be returned for backwards compatibility
                    # they should be returned if specifically asked for
                    continue

            job_desc = ShortJobDescription(**job.model_dump())
            job_list.jobref.append(job_desc)

        # limit by last, if specified
        if last:
            job_list.jobref = job_list.jobref[:last]

        return job_list

    def get_job_detail(self, job_id: str, value: str):
        """Return one of the detail elements of the job summary.

        Args:
            job_id: The ID of the job to get.
            value: The value to return.

        """

        job = self.store.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        try:
            return getattr(job, value)
        except AttributeError:
            raise HTTPException(400, f"Job detail {value} not found")

    def delete_job(self, job_id):
        """Delete a job by its ID.

        Args:
            job_id: The ID of the job to delete.

        Raises:
            KeyError: If no job with the given ID exists.
        """

        job = self.store.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        self.store.delete_job(job_id)
        self.worker.cancel(job_id)

    def create_job(self, parameters: list[Parameter], owner_id: str = None, run_id: str = None) -> str:
        """Create a new job.

        Args:
            parameters: The service-specific paramters with which to create the job.

        Returns:
            The ID of the created job.
        """

        job_id = self.store.add_job(parameters, owner_id, run_id)
        return job_id

    def post_update_job(
        self, job_id: str, phase: PhaseAction = None, destruction: datetime = None, action: Literal["DELETE"] = None
    ):
        """Update a job.

        Args:
            job_id: The ID of the job to update.
            phase: The phase in which to put the job.
            destruction: The new destruction time of the job.
            action: The action to take on the job. Currently only "DELETE" is supported.
        """

        job = self.store.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        if action:
            # If they delete the job, there's nothing else to update
            self.delete_job(job_id)
            return None
        if destruction:
            if destruction < datetime.now(timezone.utc):
                raise HTTPException(400, "Destruction time must be in the future")
            job.destruction_time = destruction
        if phase:
            # Finally, update the phase - we can return right away
            self.update_job_phase(job_id, phase)

        return self.get_job_summary(job_id)

    def update_job_phase(self, job_id: str, phase: PhaseAction):
        """Update the phase of a job.

        Args:
            job_id: The ID of the job to update.
            phase: The new phase of the job.
        """

        job = self.store.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        if phase == PhaseAction.RUN:
            # Only run the job if PENDING or HELD
            if job.phase in (ExecutionPhase.PENDING, ExecutionPhase.HELD):
                uws_worker.run(job)
        elif phase == PhaseAction.ABORT:
            uws_worker.cancel(job)
            job.phase = ExecutionPhase.ABORTED
            self.store.save_job(job)
        else:
            return HTTPException(501, "Phase not supported.")

    def update_job_value(self, job_id: str, value: str, new_value):
        """Update a value of a job.

        Args:
            job_id: The ID of the job to update.
            value: The value to update.
            new_value: The new value of the job.
        """

        job = self.store.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")

        setattr(job, value, new_value)
        self.store.save_job(job)
