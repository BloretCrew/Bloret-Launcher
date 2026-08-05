"""
Modrinth Modpack Import Module

对齐官方 Modrinth App 导入行为（精简 Python 实现）：
1. 解析 modrinth.index.json
2. 按 dependencies 安装 Minecraft + 加载器
3. 下载 files[]（多镜像、sha1 校验；跳过 client unsupported）
4. 解压 overrides/ 与 client-overrides/
5. 兼容旧 Bloret 错误格式：ZIP 内 files/ 目录
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from modules.i18n import i18nText
from modules.log import log

ProgressCb = Optional[Callable[[str, int, int, str], None]]

_SESSION: Optional[requests.Session] = None


def _session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": "Bloret-Launcher/mrpack-import (https://github.com/Bloret-Crew/Bloret-Launcher)",
            }
        )
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _SESSION = s
    return _SESSION


def _emit(progress: ProgressCb, phase: str, current: int, total: int, message: str):
    if progress:
        try:
            progress(phase, current, total, message)
        except Exception:
            pass
    log(f"[mrpack-import] [{phase}] {current}/{total} {message}", logging.INFO)


def _safe_join(base: Path, rel: str) -> Path:
    """防止 zip-slip：相对路径必须落在 base 下。"""
    rel = rel.replace("\\", "/").lstrip("/")
    parts = []
    for p in rel.split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            raise ValueError(f"非法路径: {rel}")
        parts.append(p)
    target = base.joinpath(*parts) if parts else base
    base_resolved = base.resolve()
    # 目标可能尚不存在，用 parent 校验前缀
    try:
        target.resolve().relative_to(base_resolved)
    except ValueError:
        # 文件尚不存在时 resolve 仍可基于父目录
        if not str(target).startswith(str(base_resolved)):
            # 宽松：确保规范化后仍在 base 下
            norm = os.path.normpath(str(target))
            if not norm.startswith(str(base_resolved)):
                raise ValueError(f"路径越界: {rel}")
    return target


def _sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_mrpack_index(mrpack_path: str) -> Dict[str, Any]:
    """读取并校验 modrinth.index.json。"""
    path = Path(mrpack_path)
    if not path.is_file():
        raise FileNotFoundError(f"mrpack 不存在: {mrpack_path}")

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        manifest_name = None
        for n in names:
            if n.replace("\\", "/") == "modrinth.index.json":
                manifest_name = n
                break
        if not manifest_name:
            raise ValueError("整合包中未找到 modrinth.index.json")
        raw = zf.read(manifest_name)
        try:
            index = json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"modrinth.index.json 解析失败: {e}") from e

    if not isinstance(index, dict):
        raise ValueError("modrinth.index.json 格式无效")
    if index.get("game") != "minecraft":
        raise ValueError(f"不支持的 game 类型: {index.get('game')!r}")
    if not isinstance(index.get("files"), list):
        index["files"] = []
    if not isinstance(index.get("dependencies"), dict):
        index["dependencies"] = {}
    return index


def parse_dependencies(deps: Dict[str, Any]) -> Tuple[str, str, Optional[str]]:
    """
    返回 (minecraft_version, loader_type, loader_version)。
    loader_type: vanilla | fabric | forge | neoforge | quilt
    """
    mc = str(deps.get("minecraft") or "").strip()
    if not mc:
        raise ValueError("dependencies 缺少 minecraft 版本")
    # 去掉版本范围符号，取近似精确版本
    m = re.search(r"(\d+\.\d+(?:\.\d+)?)", mc)
    if m:
        mc = m.group(1)

    loader_type = "vanilla"
    loader_version = None
    mapping = (
        ("fabric-loader", "fabric"),
        ("quilt-loader", "quilt"),
        ("neoforge", "neoforge"),
        ("forge", "forge"),
    )
    for key, ltype in mapping:
        if key in deps and deps[key] not in (None, ""):
            loader_type = ltype
            ver = str(deps[key]).strip()
            # 去掉范围前缀
            vm = re.search(r"([\w.\-]+)", ver.lstrip(">=~*^"))
            loader_version = vm.group(1) if vm else ver
            break
    return mc, loader_type, loader_version


def suggest_instance_name(index: Dict[str, Any], mrpack_path: str) -> str:
    name = str(index.get("name") or "").strip()
    version_id = str(index.get("versionId") or "").strip()
    # 优先短名：整合包名；过长再截断。versionId 常含空格/特殊字符，仅作后缀兜底。
    if name:
        base = name
    elif version_id:
        base = version_id
    else:
        base = Path(mrpack_path).stem
    # 净化为安全目录名（与 install._is_safe_version_name 对齐）
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base)
    base = base.replace("\\", "_").replace("/", "_").strip(" .")
    # 空白压成下划线，避免部分平台路径问题
    base = re.sub(r"\s+", "_", base)
    if not base or base in (".", ".."):
        base = "ImportedModpack"
    return base[:64]


def _unique_instance_name(minecraft_dir: str, desired: str) -> str:
    versions = Path(minecraft_dir) / "versions"
    candidate = desired
    n = 2
    while (versions / candidate).exists():
        candidate = f"{desired}-{n}"
        n += 1
        if n > 999:
            candidate = f"{desired}-{int(time.time())}"
            break
    return candidate


def _client_unsupported(file_entry: dict) -> bool:
    env = file_entry.get("env") or {}
    if not isinstance(env, dict):
        return False
    return str(env.get("client") or "").lower() == "unsupported"


def _download_one(
    file_entry: dict,
    instance_dir: Path,
) -> Tuple[str, bool, str]:
    """下载单个 files[] 条目。返回 (path, ok, message)。"""
    rel = str(file_entry.get("path") or "").replace("\\", "/")
    if not rel:
        return "", False, "缺少 path"
    if _client_unsupported(file_entry):
        return rel, True, "skipped: unsupported on client"

    hashes = file_entry.get("hashes") or {}
    expected_sha1 = hashes.get("sha1")
    downloads = file_entry.get("downloads") or []
    if not downloads:
        return rel, False, "无 downloads 且非 overrides"

    target = _safe_join(instance_dir, rel)
    target.parent.mkdir(parents=True, exist_ok=True)

    # 已存在且哈希匹配则跳过
    if target.is_file() and expected_sha1:
        try:
            if _sha1_file(target) == expected_sha1:
                return rel, True, "already present"
        except Exception:
            pass

    last_err = "unknown"
    for url in downloads:
        try:
            resp = _session().get(url, timeout=120, stream=True)
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}"
                continue
            chunks = []
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    chunks.append(chunk)
            data = b"".join(chunks)
            if expected_sha1:
                actual = _sha1_bytes(data)
                if actual != expected_sha1:
                    last_err = f"sha1 mismatch: {actual} != {expected_sha1}"
                    continue
            tmp = target.with_suffix(target.suffix + ".part")
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, target)
            return rel, True, "downloaded"
        except Exception as e:
            last_err = str(e)
            continue
    return rel, False, last_err


def extract_overrides(
    mrpack_path: str,
    instance_dir: Path,
    progress: ProgressCb = None,
) -> int:
    """解压 overrides/、client-overrides/，以及兼容旧版 files/。"""
    extracted = 0
    prefixes = (
        ("overrides/", True),
        ("client-overrides/", True),
        ("files/", True),  # 旧 Bloret 错误格式兼容
    )
    with zipfile.ZipFile(mrpack_path, "r") as zf:
        entries = []
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.endswith("/"):
                continue
            for prefix, _ in prefixes:
                if name.startswith(prefix):
                    rel = name[len(prefix) :]
                    if rel:
                        entries.append((info, rel))
                    break

        total = len(entries)
        _emit(progress, "extract", 0, total, i18nText("正在解压覆盖文件..."))
        for i, (info, rel) in enumerate(entries, 1):
            try:
                target = _safe_join(instance_dir, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info, "r") as src, open(target, "wb") as dst:
                    while True:
                        chunk = src.read(65536)
                        if not chunk:
                            break
                        dst.write(chunk)
                extracted += 1
            except Exception as e:
                log(f"解压覆盖失败 {rel}: {e}", logging.WARNING)
            if i == total or i % 10 == 0:
                _emit(progress, "extract", i, total, rel)

    return extracted


def _install_minecraft_and_loader(
    minecraft_version: str,
    loader_type: str,
    instance_name: str,
    minecraft_dir: str,
    backend=None,
    progress: ProgressCb = None,
    timeout_sec: int = 3600,
) -> bool:
    """通过 DownloadManager 安装游戏与加载器（会弹出下载面板），阻塞直到完成。"""
    from modules.download_manager import DownloadManager
    from modules.install import _is_safe_version_name

    loader = loader_type if loader_type in ("vanilla", "fabric", "forge", "neoforge") else (
        "fabric" if loader_type == "quilt" else "vanilla"
    )
    if loader_type == "quilt":
        log("Quilt 加载器将尝试以 fabric 兼容路径安装（若失败请手动装加载器）", logging.WARNING)

    if not _is_safe_version_name(instance_name):
        raise ValueError(f"不安全的实例名: {instance_name!r}")

    _emit(
        progress,
        "install",
        0,
        1,
        f"正在安装 Minecraft {minecraft_version} ({loader})...",
    )

    dm = DownloadManager()
    task_id = dm.start_download(
        minecraft_version,
        instance_name,
        loader,
        backend,
        minecraft_dir=minecraft_dir,
    )
    # 打开下载管理面板，避免“选完文件无反应”
    if backend is not None:
        try:
            if hasattr(backend, "openDownloadManager"):
                backend.openDownloadManager()
            elif hasattr(backend, "downloadManagerOpenRequested"):
                backend.downloadManagerOpenRequested.emit()
        except Exception:
            pass
        try:
            backend.downloadNotify.emit(
                i18nText("正在导入整合包"),
                f"{instance_name} · Minecraft {minecraft_version} ({loader})",
                True,
            )
        except Exception:
            pass

    deadline = time.monotonic() + timeout_sec
    last_status = ""
    while time.monotonic() < deadline:
        task = dm.get_task(task_id)
        if task is None:
            time.sleep(0.5)
            continue
        status_text = task.status_text or ""
        if status_text and status_text != last_status:
            last_status = status_text
            try:
                pct = int(float(task.progress or 0))
            except (TypeError, ValueError):
                pct = 0
            _emit(progress, "install", pct, 100, status_text)
        if task.completed_event.is_set() or task.status in (
            "completed",
            "failed",
            "cancelled",
        ):
            # 再等一下确保 result 写完
            task.completed_event.wait(timeout=2.0)
            if task.status == "completed" and bool(task.result):
                _emit(progress, "install", 100, 100, i18nText("游戏与加载器安装完成"))
                return True
            raise RuntimeError(
                task.error_message
                or f"安装失败: status={task.status}"
            )
        time.sleep(0.8)

    try:
        dm.cancel_task(task_id)
    except Exception:
        pass
    raise TimeoutError("安装 Minecraft 超时")


def import_mrpack(
    mrpack_path: str,
    minecraft_dir: Optional[str] = None,
    instance_name: Optional[str] = None,
    backend=None,
    progress: ProgressCb = None,
    install_game: bool = True,
    max_download_workers: int = 4,
) -> Dict[str, Any]:
    """
    导入 .mrpack 到 versions/{instance_name}。

    Returns:
        dict: {ok, instance_name, instance_path, message, stats}
    """
    import modules.globals as BLglobals
    import modules.config as cfg

    if minecraft_dir is None:
        try:
            config_data = cfg.read()
            minecraft_dir = config_data.get("minecraft_dir") or BLglobals.minecraft_dir
        except Exception:
            minecraft_dir = getattr(BLglobals, "minecraft_dir", None)
    if not minecraft_dir:
        minecraft_dir = os.path.join(BLglobals.datapath, ".minecraft")

    result: Dict[str, Any] = {
        "ok": False,
        "instance_name": "",
        "instance_path": "",
        "message": "",
        "stats": {},
    }

    try:
        # 插件 pre hook
        try:
            from modules.plugin_host.dispatch import invoke_hook
            from modules.plugin_host import hooks as hook_names

            invoke_hook(
                hook_names.MRPACK_IMPORT_PRE,
                {"path": mrpack_path, "minecraft_dir": minecraft_dir},
            )
        except Exception:
            pass

        _emit(progress, "read", 0, 1, i18nText("正在读取整合包清单..."))
        index = read_mrpack_index(mrpack_path)
        deps = index.get("dependencies") or {}
        mc_ver, loader_type, loader_ver = parse_dependencies(deps)
        desired = instance_name or suggest_instance_name(index, mrpack_path)
        desired = _unique_instance_name(minecraft_dir, desired)
        instance_dir = Path(minecraft_dir) / "versions" / desired
        instance_dir.mkdir(parents=True, exist_ok=True)

        result["instance_name"] = desired
        result["instance_path"] = str(instance_dir)

        log(
            f"导入 mrpack: name={index.get('name')}, mc={mc_ver}, "
            f"loader={loader_type}:{loader_ver}, dest={instance_dir}",
            logging.INFO,
        )

        if install_game:
            _install_minecraft_and_loader(
                mc_ver,
                loader_type,
                desired,
                minecraft_dir,
                backend=backend,
                progress=progress,
            )

        # 下载 files[]
        files = [f for f in (index.get("files") or []) if isinstance(f, dict)]
        total = len(files)
        _emit(progress, "download", 0, total, i18nText("正在下载整合包内容..."))
        ok_count = 0
        fail_count = 0
        skip_count = 0
        errors: List[str] = []

        def _job(entry):
            return _download_one(entry, instance_dir)

        if total:
            workers = max(1, min(max_download_workers, total))
            done = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_job, e): e for e in files}
                for fut in as_completed(futures):
                    rel, ok, msg = fut.result()
                    done += 1
                    if ok:
                        if msg.startswith("skipped"):
                            skip_count += 1
                        else:
                            ok_count += 1
                    else:
                        fail_count += 1
                        errors.append(f"{rel}: {msg}")
                    _emit(progress, "download", done, total, rel or msg)

        # 解压 overrides
        extracted = extract_overrides(mrpack_path, instance_dir, progress=progress)

        # 写入导入元数据，便于后续识别
        meta = {
            "source": "mrpack",
            "pack_name": index.get("name"),
            "pack_version": index.get("versionId"),
            "minecraft": mc_ver,
            "loader": loader_type,
            "loader_version": loader_ver,
            "imported_at": int(time.time()),
            "mrpack_file": os.path.basename(mrpack_path),
        }
        try:
            with open(instance_dir / "bloret-mrpack-meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"写入 mrpack meta 失败: {e}", logging.DEBUG)

        stats = {
            "remote_ok": ok_count,
            "remote_fail": fail_count,
            "remote_skip": skip_count,
            "overrides": extracted,
            "minecraft": mc_ver,
            "loader": loader_type,
        }
        result["stats"] = stats

        if fail_count and ok_count == 0 and extracted == 0:
            result["message"] = i18nText("导入失败：无法下载任何内容")
            if errors:
                result["message"] += "\n" + "\n".join(errors[:5])
            result["ok"] = False
        else:
            msg = i18nText("整合包导入成功")
            if fail_count:
                msg += f"（{fail_count} 个文件下载失败）"
            result["message"] = msg
            result["ok"] = True

        try:
            from modules.plugin_host.dispatch import invoke_hook
            from modules.plugin_host import hooks as hook_names

            invoke_hook(hook_names.MRPACK_IMPORT_POST, result)
        except Exception:
            pass

        _emit(
            progress,
            "done",
            1 if result["ok"] else 0,
            1,
            result["message"],
        )
        return result

    except Exception as e:
        log(f"导入 mrpack 失败: {e}", logging.ERROR)
        import traceback

        log(traceback.format_exc(), logging.ERROR)
        result["message"] = str(e)
        result["ok"] = False
        _emit(progress, "error", 0, 1, str(e))
        return result


def import_mrpack_file_dialog(parent_widget=None, backend=None, progress: ProgressCb = None):
    """弹出文件选择并导入（供旧 Qt Widgets 路径使用）。"""
    from PySide6.QtWidgets import QFileDialog

    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        i18nText("选择 .mrpack 文件"),
        "",
        "Modrinth Modpack Files (*.mrpack)",
    )
    if not file_path:
        log(i18nText("未选择文件"))
        return {"ok": False, "message": i18nText("未选择文件"), "cancelled": True}

    return import_mrpack(file_path, backend=backend, progress=progress)
