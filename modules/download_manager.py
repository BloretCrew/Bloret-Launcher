"""Multi-task download manager — replaces the single-task lock model.

Manages concurrent download tasks, each with independent state,
and a global semaphore limiting total concurrent file downloads
across all tasks.
"""

from __future__ import annotations

import threading
import time
import uuid
import modules.globals as BLglobals
from modules.log import log


class DownloadTask:
    """Single download task state, accessible from install.py & Backend."""

    __slots__ = (
        "task_id", "version", "version_name", "loader",
        "status", "progress", "status_text", "speed", "eta",
        "downloaded", "total", "error_message",
        "cancel_event", "pause_event", "backend",
        "thread", "result", "finished_at",
        "completed_event", "minecraft_dir",
        "_last_emit_ts", "_last_emit_progress",
    )

    def __init__(self, task_id, version, version_name, loader, backend, minecraft_dir=None):
        self.task_id = task_id
        self.version = version
        self.version_name = version_name
        self.loader = loader
        self.status = "queued"          # queued | downloading | paused | completed | failed | cancelled
        self.progress = 0.0
        self.status_text = ""
        self.speed = ""
        self.eta = ""
        self.downloaded = ""
        self.total = ""
        self.error_message = ""
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.backend = backend
        self.thread = None
        self.result = None
        self.finished_at = 0.0
        self.completed_event = threading.Event()
        self.minecraft_dir = minecraft_dir
        self._last_emit_ts = 0.0
        self._last_emit_progress = -1.0


class DownloadManager:
    """Global singleton that manages all download tasks.

    Thread-safe: all task list mutations are guarded by a Lock.
    """

    MAX_FINISHED_TASKS = 50
    FINISHED_TASK_TTL = 30 * 60
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _init(self):
        if self._initialized:
            return
        self._initialized = True
        self.tasks: dict[str, DownloadTask] = {}
        self.tasks_lock = threading.Lock()
        from modules.download import set_global_download_limit
        max_thread = self._get_max_thread_config()
        set_global_download_limit(max_thread)
        log(f"[DownloadManager] initialized with global limit={max_thread}")

    def _get_max_thread_config(self):
        """Read MaxThread from config, clamped [1, 64]."""
        try:
            import modules.config as cfg
            from modules.download import clamp_workers
            return int(clamp_workers(cfg.read().get("MaxThread", 16)))
        except Exception:
            return 16

    # ── task lifecycle ──

    def start_download(self, version, version_name, loader, backend, minecraft_dir=None) -> str:
        """Start a new download task. Returns task_id.

        minecraft_dir: optional override for install target root (e.g. mrpack import).
        """
        self._init()
        task_id = uuid.uuid4().hex[:12]
        task = DownloadTask(
            task_id, version, version_name, loader, backend, minecraft_dir=minecraft_dir
        )
        with self.tasks_lock:
            self.tasks[task_id] = task

        # 计算此任务可用线程数：总 MaxThread / 活跃任务数
        max_thread = self._get_max_thread_config()
        active_now = self.active_count() + 1  # 包括当前任务
        per_task_threads = max(1, max_thread // max(1, active_now))

        from modules.install import _install_minecraft_version_threaded

        def run():
            try:
                task.status = "downloading"
                if backend:
                    backend.downloadTaskAdded.emit(task_id)

                task_state = {
                    "task_id": task_id,
                    "cancel_event": task.cancel_event,
                    "pause_event": task.pause_event,
                    "backend": backend,
                    "cancelled": False,
                    "is_paused": False,
                    "downloader": None,
                    "completed_event": task.completed_event,
                    "result": None,
                    "cleanup_on_fail": True,
                    "version_dir": None,
                    "max_thread": per_task_threads,  # 每任务线程配额
                }

                result = bool(
                    _install_minecraft_version_threaded(
                        version,
                        minecraft_dir=task.minecraft_dir,
                        Fabric_Loader=(loader == "fabric"),
                        VersionName=version_name,
                        backend=backend,
                        Loader_Type=loader,
                        task_state=task_state,
                    )
                )
                task.result = result
                if task.cancel_event.is_set():
                    task.status = "cancelled"
                elif result:
                    task.status = "completed"
                else:
                    task.status = "failed"
                    task.error_message = task_state.get("_fail_reason", "")
            except Exception as exc:
                task.status = "failed"
                task.error_message = str(exc)
                log(f"[DownloadManager] task {task_id} exception: {exc}", exc_info=True)
            finally:
                if task.status == "failed" and backend:
                    try:
                        backend.downloadErrorOccurred.emit(
                            "Minecraft 下载失败",
                            task.error_message or "下载任务未完成",
                            version,
                            version_name,
                            loader,
                        )
                    except Exception:
                        pass
                task.completed_event.set()
                if backend:
                    try:
                        backend.downloadTaskRemoved.emit(task_id)
                    except Exception:
                        pass
                task.finished_at = time.monotonic()
                task.thread = None
                # 保留 backend 引用到任务被 prune 前，便于失败通知；此处清空避免泄漏
                task.backend = None
                self._prune_finished_tasks()
                log(f"[DownloadManager] task {task_id} finished, status={task.status}")

        thread = threading.Thread(target=run, daemon=True, name=f"dl-{task_id}")
        task.thread = thread
        thread.start()
        log(f"[DownloadManager] started task {task_id}: {version} ({loader})")
        return task_id

    def wait_task(self, task_id, timeout: float | None = None) -> bool:
        """Block until task finishes. Returns True if completed within timeout."""
        task = self.get_task(task_id)
        if task is None:
            return False
        return task.completed_event.wait(timeout=timeout)

    def cancel_task(self, task_id):
        """Cancel a task by ID."""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
        if task is None:
            return
        task.cancel_event.set()
        # unblock pause so cancel can proceed
        task.pause_event.clear()
        task.status = "cancelled"
        # If there's a LibraryDownloader, cancel it
        # (accessed via task_state which is kept on the task)
        log(f"[DownloadManager] cancelled task {task_id}")

    def pause_task(self, task_id):
        """Pause a task (set pause_event)."""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
        if task is None:
            return
        task.pause_event.set()
        task.status = "paused"
        log(f"[DownloadManager] paused task {task_id}")

    def resume_task(self, task_id):
        """Resume a paused task (clear pause_event)."""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
        if task is None:
            return
        task.pause_event.clear()
        task.status = "downloading"
        log(f"[DownloadManager] resumed task {task_id}")

    def remove_task(self, task_id):
        """Remove a completed/failed task from the list."""
        with self.tasks_lock:
            self.tasks.pop(task_id, None)
        log(f"[DownloadManager] removed task {task_id}")

    def _prune_finished_tasks(self):
        """Bound retained history and release stale completed task objects."""
        now = time.monotonic()
        with self.tasks_lock:
            finished = [
                task for task in self.tasks.values()
                if task.status in ("completed", "failed", "cancelled")
                and task.finished_at > 0
            ]
            expired_ids = {
                task.task_id for task in finished
                if now - task.finished_at >= self.FINISHED_TASK_TTL
            }
            retained = sorted(
                (task for task in finished if task.task_id not in expired_ids),
                key=lambda task: task.finished_at,
                reverse=True,
            )
            expired_ids.update(
                task.task_id for task in retained[self.MAX_FINISHED_TASKS:]
            )
            for task_id in expired_ids:
                self.tasks.pop(task_id, None)
        if expired_ids:
            log(f"[DownloadManager] pruned {len(expired_ids)} finished tasks")

    def update_progress(self, task_id, progress, status_text, speed="", downloaded="", total=""):
        """Called from install.py's progress callback to update task state.

        UI 信号节流：最多约 5 次/秒，或进度变化 ≥1%，避免切页时主线程被进度洪水卡死。
        任务字典字段仍每次更新，轮询 getDownloadTasks 总能读到最新值。
        """
        with self.tasks_lock:
            task = self.tasks.get(task_id)
        if task is None:
            return
        task.progress = progress
        task.status_text = status_text
        # Parse speed field for ETA if present
        if speed and "·" in speed:
            parts = speed.split("·")
            speed = parts[0].strip() if parts else speed
        task.speed = speed
        task.downloaded = downloaded
        task.total = total
        if not task.backend:
            return
        now = time.monotonic()
        try:
            prog = float(progress or 0)
        except (TypeError, ValueError):
            prog = 0.0
        if prog > 0 and prog <= 1.0:
            prog *= 100.0
        last_ts = task._last_emit_ts or 0.0
        last_prog = task._last_emit_progress if task._last_emit_progress is not None else -1.0
        if (now - last_ts) < 0.2 and abs(prog - last_prog) < 1.0:
            return
        task._last_emit_ts = now
        task._last_emit_progress = prog
        task.backend.downloadTaskProgressUpdated.emit(
            task_id, progress, status_text, speed, downloaded, total
        )

    # ── queries ──

    def get_tasks(self) -> list:
        """Return snapshot of all tasks (cheap; prune only occasionally)."""
        self._init()
        # 避免每次 UI 轮询都做 prune（持锁扫表），降低切页卡顿概率
        now = time.monotonic()
        last = getattr(self, "_last_prune_ts", 0.0)
        if now - last >= 5.0:
            self._last_prune_ts = now
            self._prune_finished_tasks()
        with self.tasks_lock:
            return list(self.tasks.values())

    def get_task(self, task_id) -> DownloadTask | None:
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def active_count(self) -> int:
        """Number of tasks in downloading/paused state."""
        n = 0
        with self.tasks_lock:
            for t in self.tasks.values():
                if t.status in ("downloading", "paused"):
                    n += 1
        return n
