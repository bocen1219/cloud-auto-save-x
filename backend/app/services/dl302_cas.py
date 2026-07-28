from __future__ import annotations

import logging
from pathlib import PurePosixPath

import grpc

from app.core.errors import ApiError, bad_request, not_found
from app.models.drive_account import DriveAccount
from app.services.drive_account_lsdir_refresh_status import KIND_CAS_OUTPUT, KIND_TARGETED
from app.services.drive_account_lsdir_scan import (
    refresh_drive_account_lsdir_paths,
    trigger_drive_account_lsdir_refresh_async,
)
from app.services.dl302_settings import extract_dl302_cas_base_paths


logger = logging.getLogger(__name__)


def _normalize_media_base_path(raw: object) -> str | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        normalized = str(PurePosixPath(text))
    except Exception:
        return None
    if not normalized.startswith("/"):
        normalized = "/" + normalized.lstrip("/")
    return normalized.rstrip("/") or "/"


def _extract_account_media_base_paths(account: DriveAccount) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for raw in extract_dl302_cas_base_paths(account):
        path = _normalize_media_base_path(raw)
        if not path or path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


def _is_within_any_base(path: str, base_paths: list[str]) -> bool:
    if not base_paths:
        return False
    normalized_path = _normalize_media_base_path(path)
    if not normalized_path:
        return False
    for base_path in base_paths:
        normalized_base = _normalize_media_base_path(base_path)
        if not normalized_base:
            continue
        if normalized_base == "/" or normalized_path == normalized_base or normalized_path.startswith(normalized_base + "/"):
            return True
    return False


def _wrap_dl302_rpc_error(exc: Exception, *, action: str) -> ApiError:
    if isinstance(exc, ApiError):
        return exc
    if isinstance(exc, grpc.RpcError):
        code_fn = getattr(exc, "code", None)
        status_code = code_fn() if callable(code_fn) else None
        detail = str(exc).strip() or None
        if status_code == grpc.StatusCode.DEADLINE_EXCEEDED:
            return ApiError(code="DL302_RPC_TIMEOUT", message=f"dl302 {action}超时", http_status=504, detail=detail)
        if status_code == grpc.StatusCode.UNAVAILABLE:
            return ApiError(code="DL302_RPC_UNAVAILABLE", message="dl302 服务不可用", http_status=503, detail=detail)
        return ApiError(code="DL302_RPC_FAILED", message=f"dl302 {action}失败", http_status=502, detail=detail)
    detail = str(exc).strip() or None
    if detail == "task not found":
        return not_found("DL302_CAS_TASK_NOT_FOUND", "CAS 任务不存在")
    return ApiError(code="DL302_RPC_FAILED", message=f"dl302 {action}失败", http_status=502, detail=detail)


def _normalize_relative_dir(raw: object) -> str | None:
    text = str(raw or "").strip().strip("/")
    if not text:
        return None
    try:
        normalized = str(PurePosixPath(text)).strip().strip("/")
    except Exception:
        return None
    if not normalized or normalized == ".":
        return None
    return normalized


def _task_to_dict(task) -> dict[str, object]:
    if task is None:
        return {}
    return {
        "id": int(getattr(task, "id", 0) or 0),
        "task_id": str(getattr(task, "task_id", "") or ""),
        "drive_type": str(getattr(task, "drive_type", "") or ""),
        "account": str(getattr(task, "account", "") or ""),
        "base_path": str(getattr(task, "base_path", "") or ""),
        "status": str(getattr(task, "status", "pending") or "pending"),
        "total_items": int(getattr(task, "total_items", 0) or 0),
        "done_items": int(getattr(task, "done_items", 0) or 0),
        "failed_items": int(getattr(task, "failed_items", 0) or 0),
        "skipped_items": int(getattr(task, "skipped_items", 0) or 0),
        "total_bytes": int(getattr(task, "total_bytes", 0) or 0),
        "done_bytes": int(getattr(task, "done_bytes", 0) or 0),
        "current_item_id": int(getattr(task, "current_item_id", 0) or 0),
        "last_error": str(getattr(task, "last_error", "") or ""),
        "created_at": str(getattr(task, "created_at", "") or "") or None,
        "updated_at": str(getattr(task, "updated_at", "") or "") or None,
        "finished_at": str(getattr(task, "finished_at", "") or "") or None,
    }


def _task_item_to_dict(item) -> dict[str, object]:
    return {
        "id": int(getattr(item, "id", 0) or 0),
        "task_id": str(getattr(item, "task_id", "") or ""),
        "file_id": str(getattr(item, "file_id", "") or ""),
        "file_path": str(getattr(item, "file_path", "") or ""),
        "name": str(getattr(item, "name", "") or ""),
        "size": int(getattr(item, "size", 0) or 0),
        "status": str(getattr(item, "status", "pending") or "pending"),
        "stage": str(getattr(item, "stage", "") or ""),
        "stage_done": int(getattr(item, "stage_done", 0) or 0),
        "stage_total": int(getattr(item, "stage_total", 0) or 0),
        "retry_count": int(getattr(item, "retry_count", 0) or 0),
        "last_error": str(getattr(item, "last_error", "") or ""),
        "error_class": str(getattr(item, "error_class", "") or ""),
        "rapid_drive_types": str(getattr(item, "rapid_drive_types", "") or ""),
    }


def _resolve_account(
    account_id: int,
    db,
    *,
    require_media_base_path: bool = False,
    require_enabled: bool = False,
) -> DriveAccount:
    account = db.get(DriveAccount, int(account_id))
    if account is None:
        raise not_found("DL302_CAS_ACCOUNT_NOT_FOUND", "驱动账号不存在")
    drive_type = str(getattr(account, "drive_type", "") or "").strip()
    if drive_type not in {"115", "cloud139", "cloud189", "quark", "uc"}:
        raise bad_request("DL302_CAS_DRIVE_UNSUPPORTED", "当前账号类型不支持 dl302 CAS 生成")
    media_base_paths = _extract_account_media_base_paths(account)
    if require_media_base_path and not media_base_paths:
        raise bad_request("DL302_CAS_302_PATH_REQUIRED", "当前账号未配置 STRM 扫描路径")
    if require_enabled and not bool(getattr(account, "enabled", False)):
        raise bad_request("DL302_CAS_ACCOUNT_DISABLED", "当前账号未启用")
    return account


def _ensure_media_lsdir_cache_ready(
    db,
    account: DriveAccount,
    *,
    media_base_paths: list[str],
    source: str,
) -> None:

    from app.services.drive_account_lsdir_cache import get_drive_account_lsdir_cache_subtree_stats

    account_id = int(getattr(account, "id", 0) or 0)
    empty_paths: list[str] = []
    for base_path in media_base_paths:
        stats = get_drive_account_lsdir_cache_subtree_stats(db, account_id=account_id, full_path=base_path)
        if int(stats.get("file_total") or 0) <= 0:
            empty_paths.append(base_path)
    if not empty_paths:
        return

    queued = False
    for base_path in empty_paths:
        queued = trigger_drive_account_lsdir_refresh_async(
            account_id,
            savepath=base_path,
            relative_dir_paths=[],
            recursive_savepath=True,
            source=source,
            max_wait_seconds=1800.0,
            include_cas_root_dir=True,
            status_kind=KIND_TARGETED,
            skip_if_duplicate=True,
        ) or queued
    hint = "，已自动触发缓存刷新，请待账号缓存刷新完成后重试" if queued else "，账号缓存刷新正在进行中，请等待完成后重试"
    raise bad_request(
        "DL302_CAS_LSDIR_CACHE_NOT_READY",
        f"媒体目录缓存为空：{', '.join(empty_paths)}{hint}",
    )


def _ensure_delta_lsdir_cache_ready(
    db,
    account: DriveAccount,
    *,
    base_path: str,
    dir_paths: list[str],
    file_paths: list[str],
    source: str,
) -> None:

    from app.services.drive_account_lsdir_cache import get_drive_account_lsdir_cache_subtree_stats

    account_id = int(getattr(account, "id", 0) or 0)
    target_dirs: set[str] = {str(item or "").strip() for item in dir_paths if str(item or "").strip()}
    for raw in file_paths:
        text = str(raw or "").strip()
        if not text:
            continue
        target_dirs.add(str(PurePosixPath(text).parent))

    missing_relative_dirs: list[str] = []
    for full_path in sorted(target_dirs):
        stats = get_drive_account_lsdir_cache_subtree_stats(db, account_id=account_id, full_path=full_path)
        if int(stats.get("entry_total") or 0) > 0:
            continue
        relative = _relative_to_base(full_path, base_path)
        if relative is None:
            continue
        missing_relative_dirs.append(relative)
    if not missing_relative_dirs:
        return

    try:
        refresh_drive_account_lsdir_paths(
            account_id,
            savepath=base_path,
            relative_dir_paths=missing_relative_dirs,
            recursive_savepath=False,
            source=source,
            wait_if_busy=True,
            max_wait_seconds=300.0,
            include_cas_root_dir=False,
            status_kind=KIND_TARGETED,
        )
    except Exception as exc:
        logger.warning(
            "dl302 cas delta pre-refresh failed account_id=%s base_path=%s dirs=%s err=%s",
            account_id,
            base_path,
            missing_relative_dirs,
            str(exc).strip() or type(exc).__name__,
        )


def _relative_to_base(full_path: str, base_path: str) -> str | None:
    normalized_full = _normalize_media_base_path(full_path)
    normalized_base = _normalize_media_base_path(base_path)
    if not normalized_full or not normalized_base:
        return None
    if normalized_full == normalized_base:
        return ""
    prefix = normalized_base if normalized_base.endswith("/") else f"{normalized_base}/"
    if not normalized_full.startswith(prefix):
        return None
    return normalized_full[len(prefix):].strip("/") or ""


def submit_dl302_cas_task(account_id: int, db, *, fast_compute: bool = False) -> dict[str, object]:
    from app.thirdparty.dl302_grpc_client import submit_cas_task
    from app.services.dl302_settings import get_or_create_dl302_setting, load_dl302_config

    config = load_dl302_config(get_or_create_dl302_setting(db))
    if not str(config.get("cas_root_dir") or "").strip():
        raise bad_request("DL302_CAS_ROOT_DIR_REQUIRED", "请先配置 CAS 文件生成目录")
    account = _resolve_account(account_id, db, require_media_base_path=True, require_enabled=True)
    _ensure_media_lsdir_cache_ready(
        db,
        account,
        media_base_paths=_extract_account_media_base_paths(account),
        source=f"dl302.cas.submit:{int(account_id)}",
    )
    try:
        resp = submit_cas_task(
            drive_type=str(getattr(account, "drive_type", "") or ""),
            account=str(getattr(account, "name", "") or ""),
            fast_compute=bool(fast_compute),
        )
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务提交") from exc
    return _task_to_dict(getattr(resp, "task", None))


def refresh_dl302_cas_output_directory_cache(
    db,
    *,
    drive_type: str,
    account: str,
    task_id: str = "",
    relative_dir_paths: list[str] | None = None,
) -> dict[str, object]:
    from app.services.dl302_settings import get_or_create_dl302_setting, load_dl302_config

    drive_type_text = str(drive_type or "").strip()
    account_name = str(account or "").strip()
    if not drive_type_text or not account_name:
        raise bad_request("DL302_CAS_REFRESH_ACCOUNT_REQUIRED", "驱动类型和账号名称不能为空")

    row = (
        db.query(DriveAccount)
        .filter(
            DriveAccount.drive_type == drive_type_text,
            DriveAccount.name == account_name,
        )
        .order_by(DriveAccount.enabled.desc(), DriveAccount.id.asc())
        .first()
    )
    if row is None:
        raise not_found("DL302_CAS_REFRESH_ACCOUNT_NOT_FOUND", "未找到对应的驱动账号")

    config = load_dl302_config(get_or_create_dl302_setting(db))
    cas_root_dir = _normalize_media_base_path(config.get("cas_root_dir"))
    if not cas_root_dir:
        raise bad_request("DL302_CAS_ROOT_DIR_REQUIRED", "请先配置 CAS 文件生成目录")

    normalized_relative_dirs: list[str] = []
    seen_relative_dirs: set[str] = set()
    for raw in relative_dir_paths or []:
        normalized = _normalize_relative_dir(raw)
        if not normalized or normalized in seen_relative_dirs:
            continue
        seen_relative_dirs.add(normalized)
        normalized_relative_dirs.append(normalized)

    recursive_savepath = not normalized_relative_dirs

    account_id = int(getattr(row, "id", 0) or 0)
    queued = trigger_drive_account_lsdir_refresh_async(
        account_id,
        savepath=cas_root_dir,
        relative_dir_paths=normalized_relative_dirs,
        recursive_savepath=recursive_savepath,
        source=f"dl302.cas.done:{str(task_id or '').strip() or 'unknown'}",
        max_wait_seconds=600.0,
        include_cas_root_dir=False,
        status_kind=KIND_CAS_OUTPUT,
        skip_if_duplicate=True,
    )
    return {
        "ok": True,
        "account_id": account_id,
        "drive_type": drive_type_text,
        "account": account_name,
        "savepath": cas_root_dir,
        "relative_dir_paths": normalized_relative_dirs,
        "queued": bool(queued),
        "recursive": bool(recursive_savepath),
        "scanned_dirs": 0,
        "cached_items": 0,
        "message": "CAS 输出目录缓存刷新已入队" if queued else "CAS 输出目录缓存刷新已在进行中，本次请求合并",
    }


def _is_cas_root_maintained_by_base_scan(
    cas_root_dir: str,
    *,
    cache_base_path: str | None,
    static_base_path: str | None,
) -> bool:
    from app.services.drive_account_lsdir_cache import is_same_or_child_path

    for base_path in (cache_base_path, static_base_path):
        normalized_base = _normalize_media_base_path(base_path)
        if not normalized_base:
            continue
        if is_same_or_child_path(parent_path=normalized_base, child_path=cas_root_dir):
            return True
    return False


def handle_dl302_cas_root_dir_change(
    db,
    *,
    previous_cas_root_dir: object,
    current_cas_root_dir: object,
    source: str = "dl302.config.cas_root_dir",
) -> dict[str, object]:

    from app.services.drive_account_lsdir_cache import delete_drive_account_lsdir_cache_subtree_by_path
    from app.services.dl302_settings import extract_dl302_cache_base_path, extract_dl302_static_cache_base_path

    previous_root = _normalize_media_base_path(previous_cas_root_dir)
    current_root = _normalize_media_base_path(current_cas_root_dir)
    result: dict[str, object] = {
        "changed": False,
        "previous_cas_root_dir": previous_root or "",
        "cas_root_dir": current_root or "",
        "purged_account_ids": [],
        "purged_entries": 0,
        "queued_account_ids": [],
        "skipped_account_ids": [],
    }
    if previous_root == current_root:
        return result
    result["changed"] = True

    accounts = db.query(DriveAccount).order_by(DriveAccount.id.asc()).all()
    account_scopes: list[tuple[int, DriveAccount, str | None, str | None]] = []
    for account in accounts:
        account_id = int(getattr(account, "id", 0) or 0)
        if account_id <= 0:
            continue
        account_scopes.append(
            (
                account_id,
                account,
                extract_dl302_cache_base_path(account),
                extract_dl302_static_cache_base_path(account),
            )
        )

    purged_entries = 0
    purged_account_ids: list[int] = []
    if previous_root and previous_root != "/":
        for account_id, _account, cache_base_path, static_base_path in account_scopes:
            if _is_cas_root_maintained_by_base_scan(
                previous_root,
                cache_base_path=cache_base_path,
                static_base_path=static_base_path,
            ):
                continue
            removed = delete_drive_account_lsdir_cache_subtree_by_path(
                db,
                account_id=account_id,
                full_path=previous_root,
            )
            if removed > 0:
                purged_entries += removed
                purged_account_ids.append(account_id)
        if purged_entries:
            db.commit()
    result["purged_entries"] = purged_entries
    result["purged_account_ids"] = purged_account_ids

    if not current_root or current_root == "/":
        return result

    queued_account_ids: list[int] = []
    skipped_account_ids: list[int] = []
    for account_id, account, cache_base_path, _static_base_path in account_scopes:
        if not bool(getattr(account, "enabled", False)):
            continue
        if not cache_base_path and not _extract_account_media_base_paths(account):
            continue
        queued = trigger_drive_account_lsdir_refresh_async(
            account_id,
            savepath=current_root,
            relative_dir_paths=[],
            recursive_savepath=True,
            source=source,
            max_wait_seconds=1800.0,
            include_cas_root_dir=False,
            status_kind=KIND_CAS_OUTPUT,
            skip_if_duplicate=True,
        )
        if queued:
            queued_account_ids.append(account_id)
        else:
            skipped_account_ids.append(account_id)
    result["queued_account_ids"] = queued_account_ids
    result["skipped_account_ids"] = skipped_account_ids
    return result


def submit_dl302_cas_task_delta(
    account_id: int,
    db,
    *,
    base_path: str | None = None,
    dir_paths: list[str] | None,
    file_paths: list[str] | None,
    fast_compute: bool = False,
) -> dict[str, object]:
    from app.thirdparty.dl302_grpc_client import submit_cas_task_delta
    from app.services.dl302_settings import get_or_create_dl302_setting, load_dl302_config

    config = load_dl302_config(get_or_create_dl302_setting(db))
    if not str(config.get("cas_root_dir") or "").strip():
        raise bad_request("DL302_CAS_ROOT_DIR_REQUIRED", "请先配置 CAS 文件生成目录")

    account = _resolve_account(account_id, db, require_media_base_path=True, require_enabled=True)
    media_base_paths = _extract_account_media_base_paths(account)
    effective_base_path = _normalize_media_base_path(base_path) or (media_base_paths[0] if media_base_paths else "/")
    base_scope = ",".join(media_base_paths) if media_base_paths else "/"
    if not _is_within_any_base(effective_base_path, media_base_paths or ["/"]):
        raise bad_request(
            "DL302_CAS_BASE_PATH_OUTSIDE_302_PATH",
            f"CAS base_path 不在账号 STRM 扫描路径范围内: base_path={effective_base_path} strm_scan_path={base_scope}",
        )
    input_dir_count = len([x for x in (dir_paths or []) if str(x or "").strip()])
    input_file_count = len([x for x in (file_paths or []) if str(x or "").strip()])

    def _filter_within_base(values: list[str] | None) -> list[str]:
        out: list[str] = []
        for raw in values or []:
            text = str(raw or "").strip()
            if not text:
                continue
            if not text.startswith("/"):
                text = "/" + text.lstrip("/")
            if not _is_within_any_base(text, [effective_base_path]):
                continue
            out.append(text)
        return out

    filtered_dirs = _filter_within_base(dir_paths)
    filtered_files = _filter_within_base(file_paths)

    if (input_dir_count > 0 or input_file_count > 0) and not filtered_dirs and not filtered_files:
        raise bad_request(
            "DL302_CAS_DELTA_OUTSIDE_302_PATH",
            f"增量路径不在账号 STRM 扫描路径范围内: strm_scan_path={base_scope}",
        )

    if len(filtered_files) > 5000:
        raise bad_request("DL302_CAS_DELTA_TOO_LARGE", "增量文件数过大，请改用目录增量或分批提交")

    _ensure_delta_lsdir_cache_ready(
        db,
        account,
        base_path=effective_base_path,
        dir_paths=filtered_dirs,
        file_paths=filtered_files,
        source=f"dl302.cas.delta:{int(account_id)}",
    )

    try:
        resp = submit_cas_task_delta(
            drive_type=str(getattr(account, "drive_type", "") or ""),
            account=str(getattr(account, "name", "") or ""),
            base_path=effective_base_path,
            dir_paths=filtered_dirs,
            file_paths=filtered_files,
            fast_compute=bool(fast_compute),
        )
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 增量任务提交") from exc
    return _task_to_dict(getattr(resp, "task", None))


def list_dl302_cas_tasks(account_id: int, db, *, limit: int = 5) -> list[dict[str, object]]:
    from app.thirdparty.dl302_grpc_client import list_cas_tasks

    account = _resolve_account(account_id, db)
    try:
        resp = list_cas_tasks(
            drive_type=str(getattr(account, "drive_type", "") or ""),
            account=str(getattr(account, "name", "") or ""),
            limit=int(limit or 5),
        )
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务列表查询") from exc
    return [_task_to_dict(item) for item in list(getattr(resp, "tasks", []) or [])]


def get_dl302_cas_task(task_id: str) -> dict[str, object]:
    from app.thirdparty.dl302_grpc_client import get_cas_task

    try:
        resp = get_cas_task(task_id=str(task_id or ""))
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务详情查询") from exc
    return _task_to_dict(getattr(resp, "task", None))


def list_dl302_cas_task_items(task_id: str) -> list[dict[str, object]]:
    from app.thirdparty.dl302_grpc_client import list_cas_task_items

    try:
        resp = list_cas_task_items(task_id=str(task_id or ""))
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务明细查询") from exc
    return [_task_item_to_dict(item) for item in list(getattr(resp, "items", []) or [])]


def pause_dl302_cas_task(task_id: str) -> dict[str, object]:
    from app.thirdparty.dl302_grpc_client import pause_cas_task

    try:
        resp = pause_cas_task(task_id=str(task_id or ""))
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务暂停") from exc
    return _task_to_dict(getattr(resp, "task", None))


def resume_dl302_cas_task(task_id: str) -> dict[str, object]:
    from app.thirdparty.dl302_grpc_client import resume_cas_task

    try:
        resp = resume_cas_task(task_id=str(task_id or ""))
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务恢复") from exc
    return _task_to_dict(getattr(resp, "task", None))


def cancel_dl302_cas_task(task_id: str) -> dict[str, object]:
    from app.thirdparty.dl302_grpc_client import cancel_cas_task

    try:
        resp = cancel_cas_task(task_id=str(task_id or ""))
    except Exception as exc:
        raise _wrap_dl302_rpc_error(exc, action="CAS 任务取消") from exc
    return _task_to_dict(getattr(resp, "task", None))


def get_dl302_cas_task_summary(account_id: int, db) -> dict[str, object] | None:
    try:
        account = _resolve_account(int(account_id), db)
    except ApiError:
        return None
    try:
        from app.thirdparty.dl302_grpc_client import list_cas_tasks

        resp = list_cas_tasks(
            drive_type=str(getattr(account, "drive_type", "") or ""),
            account=str(getattr(account, "name", "") or ""),
            limit=1,
        )
    except Exception:
        return None
    tasks = [_task_to_dict(item) for item in list(getattr(resp, "tasks", []) or [])]
    return tasks[0] if tasks else None
