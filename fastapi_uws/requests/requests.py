from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from fastapi_uws.models import Parameters
from fastapi_uws.models.types import PhaseAction


class UpdateJobDestructionRequest(BaseModel):
    """Body of the request to update the destruction time of a job."""

    destruction: datetime = Field(alias="DESTRUCTION")


class UpdateJobExecutionDurationRequest(BaseModel):
    """Body of the request to update the execution duration of a job."""

    executionduration: int = Field(alias="EXECUTIONDURATION")


class UpdateJobPhaseRequest(BaseModel):
    """Body of the request to update the phase of a job."""

    phase: PhaseAction = Field(alias="PHASE")


class UpdateJobRequest(BaseModel):
    """Body of the request to update a job."""

    phase: Optional[PhaseAction] = Field(default=None, alias="PHASE")
    destruction: Optional[datetime] = Field(default=None, alias="DESTRUCTION")
    action: Optional[Literal["DELETE"]] = Field(default=None, alias="ACTION")


class CreateJobRequest(BaseModel):
    """Body of the request to create a new job."""

    parameters: Parameters
    owner_id: Optional[str] = Field(default=None, alias="ownerId")
    run_id: Optional[str] = Field(default=None, alias="runId")
