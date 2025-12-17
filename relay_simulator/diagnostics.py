"""Diagnostics helpers for Relay Simulator III.

This module provides optional logging + a GUI watchdog that can dump stack
traces when the Tkinter event loop becomes unresponsive.

Enablement:
- Logging is always configured (low overhead).
- Watchdog is enabled by default; override with env var:
  - RSIM_WATCHDOG=0  (disable)
  - RSIM_WATCHDOG_TIMEOUT=8.0  (seconds)

Logs (Windows): %LOCALAPPDATA%\\RelaySimulatorIII\\logs
"""

from __future__ import annotations

import faulthandler
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import threading
import time
from typing import Optional


_LOGGER_NAME = "relay_simulator"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    value = str(value).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def get_log_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    base = Path(local_app_data) if local_app_data else Path.cwd()
    return base / "RelaySimulatorIII" / "logs"


def setup_diagnostics() -> Path:
    """Configure file logging + faulthandler.

    Returns:
        Path to the main log file.
    """
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "relay_simulator.log"

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup is called more than once.
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        handler = RotatingFileHandler(
            log_file,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(threadName)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Best-effort: also send warnings/errors to stderr (helpful when launching from terminal).
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stderr_handler = logging.StreamHandler()
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(stderr_handler)

    # Enable faulthandler dumping all threads.
    try:
        fh_file = (log_dir / "faulthandler.log").open("a", encoding="utf-8")
        faulthandler.enable(file=fh_file, all_threads=True)
    except Exception:
        # If faulthandler can't be enabled (rare), continue without it.
        pass

    logger.info("Diagnostics initialized; log_file=%s", str(log_file))
    return log_file


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)


class UiWatchdog:
    """Detect Tkinter event-loop hangs and dump thread stack traces.

    Implementation:
    - A heartbeat runs via root.after() every 250ms updating a timestamp.
    - A background thread checks the timestamp.
    - If heartbeat stalls longer than timeout, dump all thread traces.

    This cannot *prevent* a hang, but it makes them explainable.
    """

    def __init__(
        self,
        root,
        *,
        enabled: Optional[bool] = None,
        timeout_seconds: Optional[float] = None,
        min_dump_interval_seconds: float = 30.0,
    ) -> None:
        self._root = root
        self._enabled = _env_bool("RSIM_WATCHDOG", True) if enabled is None else bool(enabled)
        self._timeout = (
            _env_float("RSIM_WATCHDOG_TIMEOUT", 8.0) if timeout_seconds is None else float(timeout_seconds)
        )
        self._min_dump_interval = float(min_dump_interval_seconds)

        self._logger = get_logger()
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

        self._last_heartbeat = time.monotonic()
        self._last_dump = 0.0
        self._heartbeat_scheduled = False

        self._dump_lock = threading.Lock()
        self._dump_file_path = get_log_dir() / "watchdog_dumps.log"

    def start(self) -> None:
        if not self._enabled:
            self._logger.info("UI watchdog disabled (RSIM_WATCHDOG=0)")
            return

        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._logger.info("UI watchdog starting (timeout=%.2fs)", self._timeout)
        self._stop_event.clear()

        # Start heartbeat on GUI thread.
        if not self._heartbeat_scheduled:
            self._heartbeat_scheduled = True
            try:
                self._root.after(250, self._heartbeat)
            except Exception:
                self._heartbeat_scheduled = False

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="UIWatchdog",
            daemon=True,
        )
        self._monitor_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._logger.info("UI watchdog stopping")

    def _heartbeat(self) -> None:
        if self._stop_event.is_set():
            self._heartbeat_scheduled = False
            return

        self._last_heartbeat = time.monotonic()
        try:
            self._root.after(250, self._heartbeat)
        except Exception:
            self._heartbeat_scheduled = False

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            now = time.monotonic()
            stalled_for = now - self._last_heartbeat

            if stalled_for >= self._timeout:
                # Rate limit dumps.
                if (now - self._last_dump) >= self._min_dump_interval:
                    self._last_dump = now
                    self._dump_traces(stalled_for)

            time.sleep(1.0)

    def _dump_traces(self, stalled_for: float) -> None:
        self._logger.warning("UI appears hung (%.2fs since heartbeat); dumping thread traces", stalled_for)

        try:
            with self._dump_lock:
                with self._dump_file_path.open("a", encoding="utf-8") as f:
                    f.write("\n" + "=" * 100 + "\n")
                    f.write(f"UI watchdog dump: stalled_for={stalled_for:.2f}s time={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("\n")
                    faulthandler.dump_traceback(file=f, all_threads=True)
                    f.write("\n")
        except Exception as e:
            self._logger.error("Failed to dump traces: %s", e)
