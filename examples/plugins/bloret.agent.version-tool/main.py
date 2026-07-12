"""示例：为络可注册 list_local_mc_versions 工具。"""


def register(api):
    api.log("Version Tool 插件 register()")

    def list_local_mc_versions(working_dir=None, **kwargs):
        versions = api.list_versions()
        mc_dir = api.get_minecraft_dir()
        api.log(f"list_local_mc_versions count={len(versions)}")
        if not versions:
            return f"未找到本地版本（minecraft_dir={mc_dir or '未设置'}）"
        lines = [f"Minecraft 目录: {mc_dir}", f"共 {len(versions)} 个版本:"]
        lines.extend(f"- {v}" for v in versions)
        return "\n".join(lines)

    definition = {
        "type": "function",
        "function": {
            "name": "list_local_mc_versions",
            "description": "列出用户本地已安装的 Minecraft 版本名称列表",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }
    api.register_agent_tool("bloriko", definition, list_local_mc_versions, kind="read")
    api.append_system_prompt(
        "bloriko",
        "你可以使用 list_local_mc_versions 工具查询本地 Minecraft 版本。",
    )
