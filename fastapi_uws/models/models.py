from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic.fields import Field

from fastapi_uws.models.types import ErrorType, ExecutionPhase, UWSVersion


class BaseUWSModel(BaseModel):
    """Base class for UWS models."""

    model_config = {
        "populate_by_name": True,
    }


class Parameter(BaseUWSModel):
    """A parameter for a UWS job."""

    id: str = Field(description="The identifier for the parameter.")
    by_reference: Optional[bool] = Field(
        default=False,
        description="Whether the value of the parameter represents a URL to retrieve the actual parameter value.",
    )
    value: Optional[str] = Field(default=None, description="The value of the parameter.")


class Parameters(BaseUWSModel):
    """The parameters of a job."""

    parameter: list[Parameter] = Field(description="The list of parameters.")


class ResultReference(BaseUWSModel):
    """A reference to a result."""

    id: str = Field(description="The identifier for the result.")
    href: Optional[str] = Field(default=None, description="The URL of the result.")
    mime_type: Optional[str] = Field(default=None, alias="mimeType", description="The MIME type of the result.")
    size: Optional[int] = Field(default=None, description="The size of the result in bytes.")


class Results(BaseUWSModel):
    """The results of a job."""

    result: Optional[list[ResultReference]] = Field(default=[], description="The list of results.")


class ErrorSummary(BaseUWSModel):
    """A short summary of an error."""

    has_detail: bool = Field(default=False, alias="hasDetail", description="Whether a detailed error is available.")
    message: Optional[str] = Field(default=None, description="A human-readable message describing the error.")
    type: ErrorType = Field(description="Characterization of the type of the error.")


class ShortJobDescription(BaseUWSModel):
    """A short description of a UWS job."""

    creation_time: datetime = Field(alias="creationTime", description="The instant at which the job was created.")
    href: Optional[str] = Field(default=None, description="The URL of the job.")
    job_id: str = Field(alias="jobId", description="The identifier for the job.")
    owner_id: Optional[str] = Field(default=None, alias="ownerId", description="The owner (creator) of the job.")
    phase: ExecutionPhase = Field(description="The current phase of the job.")
    run_id: Optional[str] = Field(default=None, alias="runId", description="A client supplied identifier for the job.")


class JobSummary(BaseUWSModel):
    """The complete representation of the state of a job."""

    job_id: str = Field(alias="jobId", description="The identifier for the job.")
    run_id: Optional[str] = Field(default=None, alias="runId", description="A client supplied identifier for the job.")
    owner_id: Optional[str] = Field(default=None, alias="ownerId", description="The owner (creator) of the job.")
    phase: ExecutionPhase = Field(description="The current phase of the job.")
    quote: Optional[datetime] = Field(default=None, description="When the job is likely to complete.")
    creation_time: datetime = Field(alias="creationTime", description="The instant at which the job was created.")
    start_time: Optional[datetime] = Field(
        default=None, alias="startTime", description="The instant at which the job started execution."
    )
    end_time: Optional[datetime] = Field(
        default=None, alias="endTime", description="The instant at which the job finished execution."
    )
    execution_duration: Optional[int] = Field(
        default=0,
        alias="executionDuration",
        description="The duration (in seconds) for which the job should be allowed to run. 0 means unlimited.",
    )
    destruction_time: Optional[datetime] = Field(
        default=None,
        alias="destructionTime",
        description="The time at which the job, records, and results will be destroyed.",
    )
    parameters: Parameters = Field(description="The parameters of the job.")
    results: Results = Field(default_factory=Results, description="The results of the job.")
    error_summary: Optional[ErrorSummary] = Field(
        default=None, alias="errorSummary", description="A summary of any errors that occurred."
    )
    job_info: Optional[list[str]] = Field(
        default=None, alias="jobInfo", description="Additional information about the job."
    )
    version: Optional[UWSVersion] = Field(
        default=None, description="The version of the UWS standard that the job complies with."
    )


class Jobs(BaseUWSModel):
    """The list of job references returned at /jobs."""

    jobref: list[ShortJobDescription] = Field(description="The list of job references.")
    version: UWSVersion = Field(description="The version of the UWS standard that the job references comply with.")
