from datetime import datetime

from fastapi import APIRouter, Body, Path, Query
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi_restful.cbv import cbv

from fastapi_uws.models import ErrorSummary, Jobs, JobSummary, Parameters, Results
from fastapi_uws.models.types import ExecutionPhase
from fastapi_uws.requests import (
    CreateJobRequest,
    UpdateJobDestructionRequest,
    UpdateJobExecutionDurationRequest,
    UpdateJobPhaseRequest,
    UpdateJobRequest,
)
from fastapi_uws.responses import ErrorMessage
from fastapi_uws.service import UWSService

uws_router = APIRouter(tags=["UWS"])
uws_service = UWSService()


@cbv(uws_router)
class UWSAPIRouter:
    """Router for UWS endpoints."""

    @uws_router.delete(
        "/uws/{job_id}",
        responses={
            303: {"model": Jobs, "description": "Any response containing the UWS job list"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Deletes the job",
        response_model_by_alias=True,
    )
    def delete_job(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> None:
        uws_service.delete_job(job_id)
        return RedirectResponse(status_code=303, url="/uws/")  # Redirect to the job list

    @uws_router.get(
        "/uws/{job_id}/destruction",
        responses={
            200: {"model": datetime, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job destruction time",
        response_model_by_alias=True,
    )
    def get_job_destruction(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> datetime:
        return PlainTextResponse(uws_service.get_job_detail(job_id, "destruction_time").isoformat())

    @uws_router.get(
        "/uws/{job_id}/error",
        responses={
            200: {"model": ErrorSummary, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job error summary",
        response_model_by_alias=True,
    )
    def get_job_error_summary(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> ErrorSummary:
        return uws_service.get_job_detail(job_id, "error_summary")

    @uws_router.get(
        "/uws/{job_id}/executionduration",
        responses={
            200: {"model": int, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job execution duration",
        response_model_by_alias=True,
    )
    def get_job_execution_duration(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> int:
        return uws_service.get_job_detail(job_id, "execution_duration")

    @uws_router.get(
        "/uws/",
        responses={
            200: {"model": Jobs, "description": "Any response containing the UWS job list"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the list of UWS jobs",
        response_model_by_alias=True,
    )
    def get_job_list(
        self,
        phase: list[ExecutionPhase] = Query(
            None, description="Execution phase of the job to filter for", alias="PHASE"
        ),
        after: datetime = Query(None, description="Return jobs submitted after this date", alias="AFTER"),
        last: int = Query(None, description="Return only the last N jobs", alias="LAST", ge=1),
    ) -> Jobs:
        return uws_service.get_job_list(phase, after, last)

    @uws_router.get(
        "/uws/{job_id}/owner",
        responses={
            200: {"model": str, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job owner",
        response_model_by_alias=True,
    )
    def get_job_owner(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> str:
        return PlainTextResponse(uws_service.get_job_detail(job_id, "owner_id"))

    @uws_router.get(
        "/uws/{job_id}/parameters",
        responses={
            200: {"model": Parameters, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job parameters",
        response_model_by_alias=True,
    )
    def get_job_parameters(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> Parameters:
        return uws_service.get_job_detail(job_id, "parameters")

    @uws_router.get(
        "/uws/{job_id}/phase",
        responses={
            200: {"model": ExecutionPhase, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job phase",
        response_model_by_alias=True,
    )
    def get_job_phase(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> ExecutionPhase:
        return PlainTextResponse(uws_service.get_job_detail(job_id, "phase"))

    @uws_router.get(
        "/uws/{job_id}/quote",
        responses={
            200: {"model": datetime, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job quote",
        response_model_by_alias=True,
    )
    def get_job_quote(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> datetime:
        return PlainTextResponse(uws_service.get_job_detail(job_id, "quote"))

    @uws_router.get(
        "/uws/{job_id}/results",
        responses={
            200: {"model": Results, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job results",
        response_model_by_alias=True,
    )
    def get_job_results(
        self,
        job_id: str = Path(..., description="Job ID"),
    ) -> Results:
        return uws_service.get_job_detail(job_id, "results")

    @uws_router.get(
        "/uws/{job_id}",
        responses={
            200: {"model": JobSummary, "description": "Any response containing the job summary"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Returns the job summary",
        response_model_by_alias=True,
    )
    def get_job_summary(
        self,
        job_id: str = Path(..., description="Job ID"),
        phase: ExecutionPhase = Query(None, description="Phase of the job to poll for", alias="PHASE"),
        wait: int = Query(None, description="Maximum time to wait for the job to change phases.", alias="WAIT", ge=-1),
    ) -> JobSummary:
        return uws_service.get_job_summary(job_id, phase, wait)

    @uws_router.post(
        "/uws/",
        responses={
            303: {"model": JobSummary, "description": "Any response containing the job summary"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Submits a job",
        response_model_by_alias=True,
    )
    def post_create_job(
        self,
        create_job_request: CreateJobRequest = Body(None, description="Initial job values"),
    ) -> None:
        parameters = create_job_request.parameter
        owner_id = create_job_request.owner_id
        run_id = create_job_request.run_id
        job_id = uws_service.create_job(parameters, owner_id, run_id)
        return RedirectResponse(status_code=303, url=f"/uws/{job_id}")

    @uws_router.post(
        "/uws/{job_id}",
        responses={
            303: {"model": JobSummary, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Update job values",
        response_model_by_alias=True,
    )
    def post_update_job(
        self,
        job_id: str = Path(..., description="Job ID"),
        update_job_request: UpdateJobRequest = Body(None, description="Values to update"),
    ) -> None:
        phase = update_job_request.phase
        destruction = update_job_request.destruction
        action = update_job_request.action

        uws_service.post_update_job(job_id, phase, destruction, action)

        if action == "DELETE":
            return RedirectResponse(status_code=303, url="/uws/")
        return RedirectResponse(status_code=303, url=f"/uws/{job_id}")

    @uws_router.post(
        "/uws/{job_id}/destruction",
        responses={
            303: {"model": JobSummary, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Updates the job destruction time",
        response_model_by_alias=True,
    )
    def post_update_job_destruction(
        self,
        job_id: str = Path(..., description="Job ID"),
        post_update_job_destruction_request: UpdateJobDestructionRequest = Body(
            None, description="Destruction time to update"
        ),
    ) -> None:
        uws_service.update_job_value(job_id, "destruction_time", post_update_job_destruction_request.destruction)
        return RedirectResponse(status_code=303, url=f"/uws/{job_id}")

    @uws_router.post(
        "/uws/{job_id}/executionduration",
        responses={
            303: {"model": JobSummary, "description": "Any response containing the job summary"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Updates the job execution duration",
        response_model_by_alias=True,
    )
    def post_update_job_execution_duration(
        self,
        job_id: str = Path(..., description="Job ID"),
        post_update_job_execution_duration_request: UpdateJobExecutionDurationRequest = Body(
            None, description="Execution duration to update"
        ),
    ) -> None:
        uws_service.update_job_value(
            job_id, "execution_duration", post_update_job_execution_duration_request.executionduration
        )
        return RedirectResponse(status_code=303, url=f"/uws/{job_id}")

    @uws_router.post(
        "/uws/{job_id}/parameters",
        responses={
            303: {"model": JobSummary, "description": "Success"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Update job parameters",
        response_model_by_alias=True,
    )
    def post_update_job_parameters(
        self,
        job_id: str = Path(..., description="Job ID"),
        parameters: Parameters = Body(None, description="Parameters to update"),
    ) -> None:
        uws_service.update_job_value(job_id, "parameters", parameters)
        return RedirectResponse(status_code=303, url=f"/uws/{job_id}")

    @uws_router.post(
        "/uws/{job_id}/phase",
        responses={
            303: {"model": JobSummary, "description": "Any response containing the job summary"},
            403: {"model": object, "description": "Forbidden"},
            404: {"model": object, "description": "Job not found"},
        },
        tags=["UWS"],
        summary="Updates the job phase",
        response_model_by_alias=True,
    )
    def post_update_job_phase(
        self,
        job_id: str = Path(..., description="Job ID"),
        post_update_job_phase_request: UpdateJobPhaseRequest = Body(None, description="Phase to update"),
    ) -> None:
        uws_service.update_job_value(job_id, "phase", post_update_job_phase_request.phase)
