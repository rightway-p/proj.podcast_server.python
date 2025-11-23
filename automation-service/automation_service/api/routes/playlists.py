from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ... import crud, schemas
from ...database import get_session

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/", response_model=list[schemas.PlaylistRead])
def list_playlists(session: Session = Depends(get_session)):
    return crud.list_playlists(session)


@router.post("/", response_model=schemas.PlaylistRead, status_code=status.HTTP_201_CREATED)
def create_playlist(payload: schemas.PlaylistCreate, session: Session = Depends(get_session)):
    return crud.create_playlist(session, payload)


@router.get("/{playlist_id}", response_model=schemas.PlaylistRead)
def get_playlist(playlist_id: int, session: Session = Depends(get_session)):
    return crud.get_playlist(session, playlist_id)


@router.patch("/{playlist_id}", response_model=schemas.PlaylistRead)
def update_playlist(
    playlist_id: int, payload: schemas.PlaylistUpdate, session: Session = Depends(get_session)
):
    return crud.update_playlist(session, playlist_id, payload)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(playlist_id: int, session: Session = Depends(get_session)):
    crud.delete_playlist(session, playlist_id)
    return None
