"""加载 Python 插件模块并调用 register(api)。"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType
from typing import Any, Optional

from modules.log import log
from modules.plugin_host.api import PluginAPI
from modules.plugin_host.hooks import parse_hook_ref, safe_call
from modules.plugin_host.manifest import resolve_path
from modules.plugin_host.registry import get_registry


def _module_name_for(plugin_id: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in plugin_id)
    return f"bloret_plugin_{safe}"


def load_python_module(plugin_id: str, plugin_dir: str, relative_entry: str) -> Optional[ModuleType]:
    entry_path = resolve_path(plugin_dir, relative_entry)
    if not entry_path or not os.path.isfile(entry_path):
        log(f"[PluginHost] Python 入口不存在: {entry_path}")
        return None

    mod_name = _module_name_for(plugin_id)
    # 卸载旧模块
    for key in list(sys.modules.keys()):
        if key == mod_name or key.startswith(mod_name + "."):
            del sys.modules[key]

    # 将插件目录加入 path，便于相对 import
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)

    try:
        spec = importlib.util.spec_from_file_location(mod_name, entry_path)
        if spec is None or spec.loader is None:
            log(f"[PluginHost] 无法创建 module spec: {entry_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        log(f"[PluginHost] 已加载 Python 模块 {mod_name} from {entry_path}")
        return module
    except Exception as e:
        log(f"[PluginHost] 加载 Python 插件失败 {plugin_id}: {e}")
        return None


def _resolve_attr(module: ModuleType, plugin_dir: str, ref: str):
    """解析 module:func 或 同目录其他 .py:func。"""
    parsed = parse_hook_ref(ref)
    if not parsed:
        # 直接在入口模块上找
        return getattr(module, ref, None) if module else None
    mod_name, func_name = parsed
    if mod_name in ("main", "plugin", "") and module is not None:
        return getattr(module, func_name, None)

    # 相对路径 .py
    candidate = resolve_path(plugin_dir, mod_name if mod_name.endswith(".py") else f"{mod_name}.py")
    if os.path.isfile(candidate):
        sub = load_python_module(f"{mod_name}_{func_name}", plugin_dir, os.path.relpath(candidate, plugin_dir))
        if sub:
            return getattr(sub, func_name, None)
    if module is not None:
        return getattr(module, func_name, None)
    return None


def activate_python_plugin(manifest: dict, api: PluginAPI) -> Optional[ModuleType]:
    """加载并 register，注册 manifest.hooks。"""
    plugin_id = manifest["id"]
    plugin_dir = manifest["path"]
    entry = (manifest.get("entry") or {}).get("python") or ""
    module = None
    if entry:
        module = load_python_module(plugin_id, plugin_dir, entry)
        if module is None:
            raise RuntimeError(f"Python 入口加载失败: {entry}")

    registry = get_registry()
    if module is not None:
        registry.plugin_modules[plugin_id] = module
        register_fn = getattr(module, "register", None)
        if callable(register_fn):
            try:
                register_fn(api)
                log(f"[PluginHost] register() 完成: {plugin_id}")
            except Exception as e:
                log(f"[PluginHost] register() 失败 {plugin_id}: {e}")
                raise RuntimeError(f"插件 register() 失败: {e}") from e
        else:
            log(f"[PluginHost] 插件 {plugin_id} 无 register()，仅使用 manifest hooks")

    # 注册 manifest 声明的 hooks（on_enable / on_disable 单独触发，不进通用 registry 广播）
    hooks = manifest.get("hooks") or {}
    enable_fn = None
    disable_fn = None
    for hook_name, ref in hooks.items():
        if not ref:
            continue
        fn = _resolve_attr(module, plugin_dir, str(ref))
        if not callable(fn):
            log(f"[PluginHost] 无法解析钩子 {hook_name}={ref} @ {plugin_id}")
            continue

        def make_wrapper(f):
            def wrapper(*args, **kwargs):
                try:
                    return f(api, *args, **kwargs)
                except TypeError:
                    return f(*args, **kwargs)

            return wrapper

        wrapped = make_wrapper(fn)
        if hook_name in ("on_enable", "on_load"):
            enable_fn = wrapped
        elif hook_name in ("on_disable", "on_unload"):
            disable_fn = wrapped
            # 存到 module 上供 deactivate 使用
            if module is not None:
                setattr(module, "_bloret_on_disable", wrapped)
        else:
            registry.add_hook(hook_name, plugin_id, wrapped)

    # 仅调用本插件的 on_enable
    if enable_fn:
        safe_call(enable_fn, plugin_id=plugin_id, hook="on_enable")
    elif module is not None:
        on_enable = getattr(module, "on_enable", None)
        if callable(on_enable):
            safe_call(on_enable, api, plugin_id=plugin_id, hook="on_enable")

    if disable_fn is not None and module is not None:
        setattr(module, "_bloret_on_disable", disable_fn)

    # 解析声明式 toolbar 的 python:action 回调（直接改 registry 内条目）
    try:
        with registry._lock:
            toolbar_list = registry.toolbar
            for item in toolbar_list:
                if item.get("plugin_id") != plugin_id:
                    continue
                if item.get("callback"):
                    continue
                action = str(item.get("action") or "")
                if not action.startswith("python:"):
                    continue
                ref = action[len("python:") :].strip()
                fn = _resolve_attr(module, plugin_dir, ref) if module else None
                if not callable(fn):
                    log(f"[PluginHost] 无法解析 toolbar python action: {action} @ {plugin_id}")
                    continue

                def _make_tb(f, a=api):
                    def _cb(*args, **kwargs):
                        try:
                            return f(a, *args, **kwargs)
                        except TypeError:
                            try:
                                return f(*args, **kwargs)
                            except TypeError:
                                return f()

                    return _cb

                item["callback"] = _make_tb(fn)
                log(f"[PluginHost] 已绑定 toolbar python action: {action} @ {plugin_id}")
    except Exception as e:
        log(f"[PluginHost] 解析 toolbar python action 失败 {plugin_id}: {e}")

    return module


def deactivate_python_plugin(plugin_id: str, module: Optional[ModuleType], api: Optional[PluginAPI] = None) -> None:
    if module is not None:
        on_disable = getattr(module, "_bloret_on_disable", None) or getattr(module, "on_disable", None)
        if callable(on_disable):
            try:
                on_disable(api)
            except TypeError:
                safe_call(on_disable, plugin_id=plugin_id, hook="on_disable")
            except Exception as e:
                log(f"[PluginHost] on_disable 失败 {plugin_id}: {e}")
    mod_name = _module_name_for(plugin_id)
    for key in list(sys.modules.keys()):
        if key == mod_name or key.startswith(mod_name + "."):
            del sys.modules[key]
    log(f"[PluginHost] 已卸载 Python 模块: {plugin_id}")
