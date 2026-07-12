"""示例插件：启动/下载钩子 + JVM 参数。"""


def register(api):
    api.log("Launch Banner 插件 register()")

    def on_toolbar_click(version=None, hwnd=None):
        api.log(f"toolbar click version={version}")
        api.notify("Launch Banner", f"当前版本: {version or '?'}")

    try:
        api.register_toolbar("launch_banner_btn", "Banner", on_toolbar_click)
    except Exception as e:
        api.log(f"register_toolbar 跳过: {e}")


def on_enable(api):
    api.log("Launch Banner 已启用")


def on_disable(api):
    api.log("Launch Banner 已禁用")


def before_launch(api, version, context=None):
    api.log(f"launch.pre version={version} context={context}")
    # 返回 None 或 {} 表示不取消；返回 {"cancel": True, "reason": "..."} 可取消
    return None


def jvm_args(api, version, base_args=None):
    api.log(f"launch.jvm_args version={version}")
    return ["-Dbloret.plugin.banner=1"]


def after_launch(api, version, pid):
    api.log(f"launch.post version={version} pid={pid}")
    try:
        api.notify("游戏已启动", f"{version} (pid={pid})")
    except Exception:
        pass


def after_download(api, version, loader=None, path=None):
    api.log(f"download.post version={version} loader={loader} path={path}")
