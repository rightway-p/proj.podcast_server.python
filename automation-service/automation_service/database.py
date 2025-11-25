from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

from .config import get_settings


_settings = get_settings()
_engine = create_engine(
    _settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {},
)


def init_db() -> None:
    """Create database tables if they do not exist."""

    SQLModel.metadata.create_all(_engine)
    _ensure_job_upload_column()
    _ensure_run_progress_columns()
    _ensure_schedule_columns()


def _ensure_job_upload_column() -> None:
    """Ensure the jobs table contains the new progress columns."""

    if not _settings.database_url.startswith("sqlite"):
        return
    with _engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(job)"))
        columns = {row[1] for row in result}
        if "should_castopod_upload" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE job ADD COLUMN should_castopod_upload INTEGER DEFAULT 0"
                )
            )
        if "progress_total" not in columns:
            conn.execute(text("ALTER TABLE job ADD COLUMN progress_total INTEGER DEFAULT 0"))
        if "progress_completed" not in columns:
            conn.execute(text("ALTER TABLE job ADD COLUMN progress_completed INTEGER DEFAULT 0"))
        if "current_task" not in columns:
            conn.execute(text("ALTER TABLE job ADD COLUMN current_task TEXT"))
        if "progress_message" not in columns:
            conn.execute(text("ALTER TABLE job ADD COLUMN progress_message TEXT"))


def _ensure_run_progress_columns() -> None:
    """Ensure the run table contains progress tracking columns."""

    if not _settings.database_url.startswith("sqlite"):
        return
    with _engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(run)"))
        columns = {row[1] for row in result}
        if "progress_total" not in columns:
            conn.execute(text("ALTER TABLE run ADD COLUMN progress_total INTEGER DEFAULT 0"))
        if "progress_completed" not in columns:
            conn.execute(text("ALTER TABLE run ADD COLUMN progress_completed INTEGER DEFAULT 0"))
        if "current_task" not in columns:
            conn.execute(text("ALTER TABLE run ADD COLUMN current_task TEXT"))
        if "progress_message" not in columns:
            conn.execute(text("ALTER TABLE run ADD COLUMN progress_message TEXT"))


def _ensure_schedule_columns() -> None:
    """Ensure schedule table has day/time fields."""

    if not _settings.database_url.startswith("sqlite"):
        return
    with _engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(schedule)"))
        columns = {row[1] for row in result}
        if "days_of_week" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE schedule ADD COLUMN days_of_week TEXT DEFAULT "
                    "'[\"mon\",\"tue\",\"wed\",\"thu\",\"fri\",\"sat\",\"sun\"]'"
                )
            )
        if "run_time" not in columns:
            conn.execute(text("ALTER TABLE schedule ADD COLUMN run_time TEXT DEFAULT '07:00'"))


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    with Session(_engine) as session:
        yield session


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLModel session."""

    with Session(_engine) as session:
        yield session
