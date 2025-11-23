from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ... import crud, schemas
from ...database import get_session

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/", response_model=list[schemas.ScheduleRead])
def list_schedules(session: Session = Depends(get_session)):
    return crud.list_schedules(session)


@router.post("/", response_model=schemas.ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: schemas.ScheduleCreate, session: Session = Depends(get_session)):
    return crud.create_schedule(session, payload)


@router.get("/{schedule_id}", response_model=schemas.ScheduleRead)
def get_schedule(schedule_id: int, session: Session = Depends(get_session)):
    return crud.get_schedule(session, schedule_id)


@router.patch("/{schedule_id}", response_model=schemas.ScheduleRead)
def update_schedule(
    schedule_id: int, payload: schemas.ScheduleUpdate, session: Session = Depends(get_session)
):
    return crud.update_schedule(session, schedule_id, payload)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, session: Session = Depends(get_session)):
    crud.delete_schedule(session, schedule_id)
    return None
