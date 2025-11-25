from urllib.parse import quote_plus

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine, text

from ...config import get_settings
from ...schemas import CastopodPodcastRead

router = APIRouter(prefix="/castopod", tags=["castopod"])

_castopod_engine = None


def _resolve_castopod_url() -> str | None:
    settings = get_settings()
    if settings.castopod_database_url:
        return settings.castopod_database_url

    if (
        settings.castopod_db_host
        and settings.castopod_db_username
        and settings.castopod_db_password
        and settings.castopod_db_name
    ):
        return (
            "mysql+pymysql://"
            f"{quote_plus(settings.castopod_db_username)}:"
            f"{quote_plus(settings.castopod_db_password)}@"
            f"{settings.castopod_db_host}:{settings.castopod_db_port}/"
            f"{settings.castopod_db_name}"
        )

    return None


def _get_castopod_engine():
    global _castopod_engine

    if _castopod_engine is not None:
        return _castopod_engine

    url = _resolve_castopod_url()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Castopod database connection is not configured.",
        )

    try:
        _castopod_engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Castopod database connection.",
        ) from exc

    return _castopod_engine


@router.get("/podcasts", response_model=list[CastopodPodcastRead])
def list_castopod_podcasts():
    engine = _get_castopod_engine()
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, guid AS uuid, title, handle AS slug FROM cp_podcasts ORDER BY id DESC")
            )
            return [CastopodPodcastRead(**row._mapping) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Castopod podcasts.",
        ) from exc
