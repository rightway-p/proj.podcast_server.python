from fastapi import APIRouter, HTTPException, status

from ... import schemas
from ...pipeline_runner import pipeline_manager

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status", response_model=schemas.PipelineStatus)
def get_pipeline_status() -> schemas.PipelineStatus:
    return schemas.PipelineStatus(**pipeline_manager.status())


@router.post("/trigger", response_model=schemas.PipelineStatus, status_code=status.HTTP_202_ACCEPTED)
def trigger_pipeline_run() -> schemas.PipelineStatus:
    try:
        pipeline_manager.trigger()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return schemas.PipelineStatus(**pipeline_manager.status())
