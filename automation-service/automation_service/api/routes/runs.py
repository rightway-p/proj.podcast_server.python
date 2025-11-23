from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ... import crud, schemas
from ...database import get_session

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=list[schemas.RunRead])
def list_runs(session: Session = Depends(get_session)):
    return crud.list_runs(session)


@router.post("/", response_model=schemas.RunRead, status_code=status.HTTP_201_CREATED)
def create_run(payload: schemas.RunCreate, session: Session = Depends(get_session)):
    return crud.create_run(session, payload)


@router.get("/{run_id}", response_model=schemas.RunRead)
def get_run(run_id: int, session: Session = Depends(get_session)):
    return crud.get_run(session, run_id)


@router.patch("/{run_id}", response_model=schemas.RunRead)
def update_run(run_id: int, payload: schemas.RunUpdate, session: Session = Depends(get_session)):
    return crud.update_run(session, run_id, payload)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, session: Session = Depends(get_session)):
    crud.delete_run(session, run_id)
    return None
