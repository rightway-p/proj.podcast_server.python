from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ... import crud, schemas
from ...database import get_session

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/", response_model=list[schemas.ChannelRead])
def list_channels(session: Session = Depends(get_session)):
    return crud.list_channels(session)


@router.post("/", response_model=schemas.ChannelRead, status_code=status.HTTP_201_CREATED)
def create_channel(payload: schemas.ChannelCreate, session: Session = Depends(get_session)):
    return crud.create_channel(session, payload)


@router.get("/{channel_id}", response_model=schemas.ChannelRead)
def get_channel(channel_id: int, session: Session = Depends(get_session)):
    return crud.get_channel(session, channel_id)


@router.patch("/{channel_id}", response_model=schemas.ChannelRead)
def update_channel(
    channel_id: int, payload: schemas.ChannelUpdate, session: Session = Depends(get_session)
):
    return crud.update_channel(session, channel_id, payload)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(channel_id: int, session: Session = Depends(get_session)):
    crud.delete_channel(session, channel_id)
    return None
