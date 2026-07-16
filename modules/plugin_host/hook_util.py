"""业务代码调用插件钩子的薄封装（避免各处重复 try/import）。"""

from __future__ import annotations

from typing import Any, List, Optional


def fire(name: str, *args, **kwargs) -> List[Any]:
    """派发钩子；失败时返回空列表，不打断主流程。"""
    try:
        from modules.plugin_host.dispatch import invoke_hook

        return invoke_hook(name, *args, **kwargs) or []
    except Exception as e:
        try:
            from modules.log import log

            log(f"[PluginHost] fire({name}) 失败: {e}")
        except Exception:
            pass
        return []


def any_cancel(results: List[Any], default_reason: str = "插件取消操作") -> Optional[str]:
    """若任一结果表示 cancel，返回 reason。"""
    for r in results or []:
        if isinstance(r, dict) and r.get("cancel"):
            return str(r.get("reason") or default_reason)
        if r is False:
            return default_reason
    return None


def merge_url_lists(base_urls: List[str], results: List[Any]) -> List[str]:
    """download.resolve_url 钩子：插件可返回 str 或 list 覆盖/追加 URL。"""
    urls = list(base_urls or [])
    for r in results or []:
        if isinstance(r, str) and r:
            # 单 URL：插入到最前（优先尝试插件镜像）
            if r not in urls:
                urls.insert(0, r)
        elif isinstance(r, (list, tuple)):
            extra = [str(x) for x in r if x]
            # 插件列表优先
            merged = []
            for u in extra + urls:
                if u and u not in merged:
                    merged.append(u)
            urls = merged
        elif isinstance(r, dict):
            if r.get("urls"):
                urls = merge_url_lists(urls, [r.get("urls")])
            elif r.get("url"):
                urls = merge_url_lists(urls, [r.get("url")])
    return urls
