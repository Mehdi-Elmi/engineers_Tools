"""Runtime logging setup."""

from __future__ import annotations

import atexit
import base64
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import TracebackType


REPOSITORY = "Mehdi-Elmi/engineers_Tools"
BRANCH = "main"
REMOTE_LOG_PATH = "log/runtime.log"
TOKEN_FILE_NAME = "token.txt"
FALLBACK_TOKEN_FILE_NAME = "testdoctoken.txt"


def setup_runtime_logging() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    log_path = log_dir / "runtime.log"
    log_path.write_text("", encoding="utf-8")

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        encoding="utf-8",
        force=True,
    )
    logging.info("Runtime log started.")
    logging.info("Runtime log path: %s", log_path)

    def log_uncaught_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = log_uncaught_exception
    atexit.register(_upload_runtime_log_if_needed, log_path)
    return log_path


def _upload_runtime_log_if_needed(log_path: Path) -> None:
    logging.shutdown()
    if not log_path.exists():
        return

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    if not _has_actionable_log(log_text):
        return

    token = _read_desktop_token()
    if token is None:
        _append_local_log_note(log_path, "GitHub log upload skipped: desktop token file was not found.")
        return

    try:
        _put_github_file(token, REMOTE_LOG_PATH, log_text)
    except Exception as exc:  # noqa: BLE001
        _append_local_log_note(log_path, f"GitHub log upload failed: {exc.__class__.__name__}.")


def _has_actionable_log(log_text: str) -> bool:
    markers = ("| WARNING |", "| ERROR |", "| CRITICAL |", "Traceback")
    return any(marker in log_text for marker in markers)


def _read_desktop_token() -> str | None:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    desktop = home / "Desktop"
    for token_path in (desktop / TOKEN_FILE_NAME, desktop / FALLBACK_TOKEN_FILE_NAME):
        if not token_path.exists():
            continue
        token = token_path.read_text(encoding="utf-8", errors="ignore").strip()
        token = token.lstrip("\ufeff").strip().strip('"').strip("'")
        for prefix in ("bearer ", "token "):
            if token.lower().startswith(prefix):
                token = token[len(prefix) :].strip()
        if token:
            return token
    return None


def _put_github_file(token: str, path: str, content: str) -> None:
    current_sha = _get_github_file_sha(token, path)
    payload = {
        "message": "Upload runtime log",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": BRANCH,
    }
    if current_sha:
        payload["sha"] = current_sha

    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/contents/{path}",
        data=json.dumps(payload).encode("utf-8"),
        method="PUT",
        headers=_github_headers(token),
    )
    _open_github_request(request)


def _get_github_file_sha(token: str, path: str) -> str | None:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/contents/{path}?ref={BRANCH}",
        headers=_github_headers(token),
    )
    try:
        response = _open_github_request(request)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise

    data = json.loads(response.decode("utf-8"))
    return data.get("sha")


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "EngineerToolsRuntimeLogger",
    }


def _open_github_request(request: urllib.request.Request) -> bytes:
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def _append_local_log_note(log_path: Path, message: str) -> None:
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"\nLOCAL | {message}\n")
