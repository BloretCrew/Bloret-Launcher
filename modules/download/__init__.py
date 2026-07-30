"""Minecraft / general download utilities shared by install & launch."""

from modules.download.constants import (
    DEFAULT_MAX_THREAD,
    MAX_THREAD_CAP,
    FASTDOWNLOAD_TTL_SEC,
    clamp_workers,
)
from modules.download.session import get_session
from modules.download.limits import (
    get_download_limiter,
    set_global_download_limit,
    get_global_download_limit,
)
from modules.download.secure import (
    DownloadCancelled,
    verify_file,
    strict_hash_verify_enabled,
    secure_download,
    download_file,
)
from modules.download.mirrors import (
    dl_source_launcher_or_meta_get,
    dl_source_library_get,
    dl_source_assets_get,
)

__all__ = [
    "DEFAULT_MAX_THREAD",
    "MAX_THREAD_CAP",
    "FASTDOWNLOAD_TTL_SEC",
    "clamp_workers",
    "get_session",
    "get_download_limiter",
    "set_global_download_limit",
    "get_global_download_limit",
    "DownloadCancelled",
    "verify_file",
    "strict_hash_verify_enabled",
    "secure_download",
    "download_file",
    "dl_source_launcher_or_meta_get",
    "dl_source_library_get",
    "dl_source_assets_get",
]
