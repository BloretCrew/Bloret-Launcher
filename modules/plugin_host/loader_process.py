"""外部进程插件兼容：main.exe -> Customize 启动项。"""

from __future__ import annotations

import os

from modules.log import log
from modules.plugin_host.manifest import resolve_path


def activate_process_plugin(manifest: dict) -> bool:
    """若存在 process 入口，确保已加入 Customize（幂等）。"""
    entry = (manifest.get("entry") or {}).get("process") or ""
    if not entry:
        return False
    path = resolve_path(manifest["path"], entry)
    if not os.path.isfile(path):
        log(f"[PluginHost] 进程入口不存在: {path}")
        return False
    try:
        from modules.customize import CustomizeAppAdd

        name = manifest.get("name") or manifest.get("id")
        result = CustomizeAppAdd(path, name)
        log(f"[PluginHost] 外部进程插件注册 Customize: {name} path={path} ok={result}")
        return bool(result)
    except Exception as e:
        log(f"[PluginHost] 注册外部进程插件失败: {e}")
        return False
