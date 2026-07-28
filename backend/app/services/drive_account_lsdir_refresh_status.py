from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from typing import Any

from app.services.drive_account_lsdir_static_state import (
    resolve_drive_account_lsdir_refresh_state_dir,
)


logger = logging.getLogger(__name__)

STATUS_IDLE = "idle"
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_INTERRUPTED = "interrupted"

ACTIVE_STATUSES = frozenset({STATUS_QUEUED, STATUS_RUNNING})

KIND_FULL = "full"
KIND_TARGETED = "targeted"
KIND_CAS_OUTPUT = "cas_output"

_states: dict[int, dict[str, Any]] = {}
_lock = threading.Lock()
_recovered = False


def _now_text() -> str:
    return datetime.now().isoformat()


def _state_path(account_id: int) -> str:
    directory = resolve_drive_account_lsdir_refresh_state_dir()
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f"account_{int(account_id)}.json")


def _persist(state: dict[str, Any]) -> None:
    """把状态跃迁落盘（进度 tick 不落盘，避免高频 IO）。"""
    account_id = int(state.get("account_id") or 0)
    if account_id <= 0:
        return
    path = _state_path(account_id)
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        logger.warning("lsdir refresh state persist failed account_id=%s err=%s", account_id, exc)


def _load_persisted(account_id: int) -> dict[str, Any] | None:
    path = _state_path(account_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    # 进程重启后落盘态里的"进行中"一定是被中断的，不能继续展示为刷新中。
    if str(payload.get("status") or "") in ACTIVE_STATUSES:
        payload["status"] = STATUS_INTERRUPTED
        payload["last_error"] = payload.get("last_error") or "刷新被进程重启中断"
        payload["finished_at"] = payload.get("finished_at") or _now_text()
    return payload


def _blank_state(account_id: int) -> dict[str, Any]:
    return {
        "account_id": int(account_id),
        "drive_type": "",
        "status": STATUS_IDLE,
        "kind": "",
        "source": "",
        "savepath": "",
        "target_dirs": 0,
        "queued_at": None,
        "started_at": None,
        "updated_at": None,
        "finished_at": None,
        "scanned_dirs": 0,
        "cached_items": 0,
        "current_path": "",
        "pending_dirs": 0,
        "duration_ms": 0,
        "waiting": False,
        "last_error": None,
        "pending_count": 0,
        "dedup_key": "",
    }


def _state_locked(account_id: int) -> dict[str, Any]:
    account_key = int(account_id)
    state = _states.get(account_key)
    if state is not None:
        return state
    state = _load_persisted(account_key) or _blank_state(account_key)
    merged = _blank_state(account_key)
    merged.update({key: value for key, value in state.items() if key in merged})
    _states[account_key] = merged
    return merged


def build_dedup_key(*, kind: str, savepath: str, relative_dirs: list[str] | None) -> str:
    dirs = sorted({str(item or "").strip().strip("/") for item in (relative_dirs or []) if str(item or "").strip()})
    return f"{str(kind or '').strip()}|{str(savepath or '').strip()}|{','.join(dirs)}"


def mark_queued(
    account_id: int,
    *,
    drive_type: str = "",
    kind: str,
    source: str,
    savepath: str = "",
    target_dirs: int = 0,
    dedup_key: str = "",
    skip_if_duplicate: bool = False,
) -> bool:
    with _lock:
        state = _state_locked(account_id)
        current_status = str(state.get("status") or "")
        is_duplicate = (
            current_status in ACTIVE_STATUSES
            and str(state.get("dedup_key") or "") == str(dedup_key or "")
            and str(dedup_key or "") != ""
        )
        if skip_if_duplicate and is_duplicate:
            return False
        if current_status == STATUS_RUNNING:
            state["pending_count"] = int(state.get("pending_count") or 0) + 1
            state["updated_at"] = _now_text()
            snapshot = dict(state)
            _persist(snapshot)
            return True
        state.update(
            {
                "drive_type": str(drive_type or state.get("drive_type") or ""),
                "status": STATUS_QUEUED,
                "kind": str(kind or ""),
                "source": str(source or ""),
                "savepath": str(savepath or ""),
                "target_dirs": int(target_dirs or 0),
                "queued_at": _now_text(),
                "started_at": None,
                "updated_at": _now_text(),
                "finished_at": None,
                "scanned_dirs": 0,
                "cached_items": 0,
                "current_path": "",
                "pending_dirs": 0,
                "duration_ms": 0,
                "waiting": False,
                "last_error": None,
                "dedup_key": str(dedup_key or ""),
            }
        )
        snapshot = dict(state)
    _persist(snapshot)
    return True


def mark_waiting(account_id: int, *, waiting: bool = True) -> None:
    with _lock:
        state = _state_locked(account_id)
        if str(state.get("status") or "") != STATUS_QUEUED:
            return
        state["waiting"] = bool(waiting)
        state["updated_at"] = _now_text()


def mark_running(
    account_id: int,
    *,
    drive_type: str = "",
    kind: str = "",
    source: str = "",
    savepath: str = "",
    target_dirs: int | None = None,
) -> None:
    with _lock:
        state = _state_locked(account_id)
        state.update(
            {
                "drive_type": str(drive_type or state.get("drive_type") or ""),
                "status": STATUS_RUNNING,
                "kind": str(kind or state.get("kind") or ""),
                "source": str(source or state.get("source") or ""),
                "savepath": str(savepath or state.get("savepath") or ""),
                "started_at": _now_text(),
                "updated_at": _now_text(),
                "finished_at": None,
                "waiting": False,
                "last_error": None,
                "pending_count": max(0, int(state.get("pending_count") or 0) - 1),
            }
        )
        if target_dirs is not None:
            state["target_dirs"] = int(target_dirs or 0)
        snapshot = dict(state)
    _persist(snapshot)


def update_progress(
    account_id: int,
    *,
    scanned_dirs: int,
    cached_items: int,
    current_path: str = "",
    pending_dirs: int = 0,
) -> None:
    """扫描进度只更新内存态，前端轮询即可看到，不落盘。"""
    with _lock:
        state = _state_locked(account_id)
        state.update(
            {
                "scanned_dirs": int(scanned_dirs or 0),
                "cached_items": int(cached_items or 0),
                "current_path": str(current_path or ""),
                "pending_dirs": int(pending_dirs or 0),
                "updated_at": _now_text(),
            }
        )


def mark_completed(
    account_id: int,
    *,
    scanned_dirs: int = 0,
    cached_items: int = 0,
    duration_ms: int = 0,
) -> None:
    with _lock:
        state = _state_locked(account_id)
        state.update(
            {
                "status": STATUS_COMPLETED,
                "scanned_dirs": int(scanned_dirs or 0),
                "cached_items": int(cached_items or 0),
                "current_path": "",
                "pending_dirs": 0,
                "duration_ms": int(duration_ms or 0),
                "updated_at": _now_text(),
                "finished_at": _now_text(),
                "waiting": False,
                "last_error": None,
                "dedup_key": "",
            }
        )
        snapshot = dict(state)
    _persist(snapshot)


def mark_failed(
    account_id: int,
    *,
    error: str,
    scanned_dirs: int = 0,
    cached_items: int = 0,
    duration_ms: int = 0,
) -> None:
    with _lock:
        state = _state_locked(account_id)
        state.update(
            {
                "status": STATUS_FAILED,
                "scanned_dirs": int(scanned_dirs or 0),
                "cached_items": int(cached_items or 0),
                "current_path": "",
                "pending_dirs": 0,
                "duration_ms": int(duration_ms or 0),
                "updated_at": _now_text(),
                "finished_at": _now_text(),
                "waiting": False,
                "last_error": str(error or "").strip()[:500] or "刷新失败",
                "dedup_key": "",
            }
        )
        snapshot = dict(state)
    _persist(snapshot)


def abandon_queued(account_id: int, *, error: str) -> None:
    with _lock:
        state = _state_locked(account_id)
        if str(state.get("status") or "") != STATUS_QUEUED:
            state["pending_count"] = max(0, int(state.get("pending_count") or 0) - 1)
            state["updated_at"] = _now_text()
            return
    mark_failed(account_id, error=error)


def _public(state: dict[str, Any]) -> dict[str, Any]:
    payload = dict(state)
    payload.pop("dedup_key", None)
    return payload


def get_status(account_id: int) -> dict[str, Any]:
    with _lock:
        return _public(_state_locked(account_id))


def list_statuses(account_ids: list[int] | None = None) -> list[dict[str, Any]]:
    if account_ids is None:
        with _lock:
            return [_public(state) for state in _states.values()]
    return [get_status(int(item)) for item in account_ids]


def has_active_refresh(account_id: int) -> bool:
    return str(get_status(account_id).get("status") or "") in ACTIVE_STATUSES


def clear_status(account_id: int) -> None:
    with _lock:
        _states.pop(int(account_id), None)
    path = _state_path(int(account_id))
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
