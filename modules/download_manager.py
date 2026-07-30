"""Multi-task download manager — replaces the single-task lock model.

Manages concurrent download tasks, each with independent state,
and a global semaphore limiting total concurrent file downloads
across all tasks.
"""

import threading
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
        "thread", "result",
    )

    def __init__(self, task_id, version, version_name, loader, backend):
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


class DownloadManager:
    """Global singleton that manages all download tasks.

    Thread-safe: all task list mutations are guarded by a Lock.
    """

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
        self._rebuild_semaphore()
        log("[DownloadManager] initialized")

    def _rebuild_semaphore(self):
        """(Re)create the global semaphore with current MaxThread."""
        max_thread = self._get_max_thread_config()
        self.global_semaphore = threading.BoundedSemaphore(max_thread)
        log(f"[DownloadManager] semaphore set to {max_thread}")

    def _get_max_thread_config(self):
        """Read MaxThread from config, clamped [1, 64]."""
        try:
            import modules.config as cfg
            from modules.download import clamp_workers
            return int(clamp_workers(cfg.read().get("MaxThread", 16)))
        except Exception:
            return 16

    # ── task lifecycle ──

    def start_download(self, version, version_name, loader, backend) -> str:
        """Start a new download task. Returns task_id."""
        self._init()
        task_id = uuid.uuid4().hex[:12]
        task = DownloadTask(task_id, version, version_name, loader, backend)
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

                # Build task_state dict for backward compat with install.py
                completed_ev = threading.Event()
                task_state = {
                    "task_id": task_id,
                    "cancel_event": task.cancel_event,
                    "pause_event": task.pause_event,
                    "backend": backend,
                    "cancelled": False,
                    "is_paused": False,
                    "downloader": None,
                    "completed_event": completed_ev,
                    "result": None,
                    "cleanup_on_fail": True,
                    "version_dir": None,
                    "max_thread": per_task_threads,  # 每任务线程配额
                }

                result = bool(
                    _install_minecraft_version_threaded(
                        version,
                        minecraft_dir=None,
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
                    backend.downloadErrorOccurred.emit(
                        "Minecraft 下载失败",
                        task.error_message or "下载任务未完成",
                        version,
                        version_name,
                        loader,
                    )
                completed_ev.set()
                if backend:
                    backend.downloadTaskRemoved.emit(task_id)
                log(f"[DownloadManager] task {task_id} finished, status={task.status}")

        thread = threading.Thread(target=run, daemon=True, name=f"dl-{task_id}")
        task.thread = thread
        thread.start()
        log(f"[DownloadManager] started task {task_id}: {version} ({loader})")
        return task_id

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

    def update_progress(self, task_id, progress, status_text, speed="", downloaded="", total=""):
        """Called from install.py's progress callback to update task state."""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
        if task is None:
            return
        task.progress = progress
        task.status_text = status_text
        task.speed = speed
        # Parse speed field for ETA if present
        if speed and "·" in speed:
            parts = speed.split("·")
            speed = parts[0].strip() if parts else speed
        task.speed = speed
        task.downloaded = downloaded
        task.total = total
        # Forward the task-aware signal to QML without breaking the legacy
        # five-argument downloadProgressUpdated signal.
        if task.backend:
            task.backend.downloadTaskProgressUpdated.emit(
                task_id, progress, status_text, speed, downloaded, total
            )

    # ── queries ──

    def get_tasks(self) -> list:
        """Return snapshot of all tasks."""
        self._init()
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
