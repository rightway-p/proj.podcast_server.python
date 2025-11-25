from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ... import crud, schemas
from ...database import get_session

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[schemas.JobRead])
def list_jobs(session: Session = Depends(get_session)):
    return crud.list_jobs(session)


@router.get("/{job_id}", response_model=schemas.JobRead)
def get_job(job_id: int, session: Session = Depends(get_session)):
    return crud.get_job(session, job_id)


@router.post("/", response_model=schemas.JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: schemas.JobCreate, session: Session = Depends(get_session)):
    return crud.create_job(session, payload)


@router.patch("/{job_id}", response_model=schemas.JobRead)
def update_job(job_id: int, payload: schemas.JobUpdate, session: Session = Depends(get_session)):
    return crud.update_job(session, job_id, payload)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, session: Session = Depends(get_session)):
    crud.delete_job(session, job_id)
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_jobs(session: Session = Depends(get_session)):
    crud.delete_all_jobs(session)
    return None


@router.post(
    "/quick-create",
    response_model=schemas.JobQuickCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def quick_create_job(
    payload: schemas.JobQuickCreateRequest,
    session: Session = Depends(get_session),
):
    return crud.quick_create_job(session, payload)
