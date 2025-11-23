from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
import shlex
import subprocess
from threading import Lock, Thread
from zoneinfo import ZoneInfo

from .config import get_settings


class PipelineProcessManager:
    """Simple singleton that spawns and tracks pipeline-run subprocesses."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._process: subprocess.Popen[str] | None = None
        self._started_at: datetime | None = None
        self._last_started_at: datetime | None = None
        self._last_finished_at: datetime | None = None
        self._last_exit_code: int | None = None
        self._log_handle: object | None = None
        self._log_thread: Thread | None = None
        self._settings = get_settings()
        try:
            self._local_tz = ZoneInfo("Asia/Seoul")
        except Exception:  # pragma: no cover - fallback if tz database missing
            self._local_tz = UTC

    def _cleanup_finished_process(self) -> None:
        if self._process is None:
            return
        returncode = self._process.poll()
        if returncode is None:
            return
        if self._log_thread and self._log_thread.is_alive():
            self._log_thread.join(timeout=1)
        self._log_thread = None
        if self._log_handle:
            try:
                self._log_handle.write(
                    f"[{self._log_timestamp()}] ===== pipeline-run finished (exit: {returncode}) =====\n"
                )
                self._log_handle.flush()
            except Exception:  # pragma: no cover - best effort logging
                pass
            try:
                self._log_handle.close()
            except Exception:  # pragma: no cover - best effort logging
                pass
            finally:
                self._log_handle = None
        self._last_exit_code = returncode
        self._last_finished_at = datetime.now(UTC)
        self._process = None
        self._started_at = None

    def _open_log(self):
        log_path = self._settings.pipeline_log_path or "pipeline-run.log"
        log_file = Path(log_path).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        return log_file.open("a", encoding="utf-8")

    def _log_timestamp(self) -> str:
        now = datetime.now(self._local_tz)
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def _pump_output(
        self,
        process: subprocess.Popen[str],
        log_handle,
    ) -> None:
        if process.stdout is None:
            return
        for raw_line in process.stdout:
            line = raw_line.rstrip("\n")
            log_handle.write(f"[{self._log_timestamp()}] {line}\n")
            log_handle.flush()

    def trigger(self) -> None:
        with self._lock:
            self._cleanup_finished_process()
            if self._process is not None:
                msg = "Pipeline is already running"
                raise RuntimeError(msg)
            command = self._settings.pipeline_command.strip()
            if not command:
                msg = "Pipeline command is empty"
                raise RuntimeError(msg)
            cmd = shlex.split(command)
            workdir = (
                Path(self._settings.pipeline_workdir).expanduser()
                if self._settings.pipeline_workdir
                else None
            )
            env = os.environ.copy()
            if self._settings.api_base_url:
                env["AUTOMATION_API_BASE_URL"] = self._settings.api_base_url
            if self._settings.pipeline_skip_configuration:
                env["PIPELINE_SKIP_CONFIGURATION"] = "true"
            if self._settings.castopod_api_base_url:
                env["CASTOPOD_API_BASE_URL"] = self._settings.castopod_api_base_url
            if self._settings.castopod_api_username:
                env["CASTOPOD_API_USERNAME"] = self._settings.castopod_api_username
            if self._settings.castopod_api_password:
                env["CASTOPOD_API_PASSWORD"] = self._settings.castopod_api_password
            if self._settings.castopod_api_user_id:
                env["CASTOPOD_API_USER_ID"] = self._settings.castopod_api_user_id
            if self._settings.castopod_api_timezone:
                env["CASTOPOD_API_TIMEZONE"] = self._settings.castopod_api_timezone
            if self._settings.castopod_api_publication_method:
                env["CASTOPOD_API_PUBLICATION_METHOD"] = (
                    self._settings.castopod_api_publication_method
                )
            if self._settings.castopod_api_episode_type:
                env["CASTOPOD_API_EPISODE_TYPE"] = (
                    self._settings.castopod_api_episode_type
                )
            if self._settings.castopod_api_verify_ssl is not None:
                env["CASTOPOD_API_VERIFY_SSL"] = (
                    "true" if self._settings.castopod_api_verify_ssl else "false"
                )
            log_handle = self._open_log()
            log_handle.write(
                f"[{self._log_timestamp()}] ===== pipeline-run start (command: {command}) =====\n"
            )
            log_handle.flush()
            process = subprocess.Popen(
                cmd,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1,
            )
            self._process = process
            self._log_handle = log_handle
            log_thread = Thread(
                target=self._pump_output,
                args=(process, log_handle),
                daemon=True,
            )
            log_thread.start()
            self._log_thread = log_thread
            started_at = datetime.now(UTC)
            self._started_at = started_at
            self._last_started_at = started_at
            self._last_finished_at = None
            self._last_exit_code = None

    def status(self) -> dict[str, object | None]:
        with self._lock:
            self._cleanup_finished_process()
            running = self._process is not None
            pid = self._process.pid if running and self._process else None
            return {
                "running": running,
                "pid": pid,
                "command": self._settings.pipeline_command,
                "started_at": self._started_at,
                "last_started_at": self._last_started_at,
                "last_finished_at": self._last_finished_at,
                "last_exit_code": self._last_exit_code,
                "log_path": self._settings.pipeline_log_path or "pipeline-run.log",
            }


pipeline_manager = PipelineProcessManager()
