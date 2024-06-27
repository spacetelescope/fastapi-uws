"""Base UWS worker class."""

from fastapi_uws.models import JobSummary


class BaseUWSWorker:
    """Base UWS worker class."""

    def run(self, job: JobSummary) -> None:
        """Run the worker on the given job.

        Args:
            job: The job to run the worker on.
        """
        raise NotImplementedError

    def cancel(self, job: JobSummary) -> None:
        """Cancel the worker on the given job.

        Args:
            job: The job to cancel the worker on.
        """
        raise NotImplementedError
