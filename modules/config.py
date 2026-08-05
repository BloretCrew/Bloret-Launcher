import os, shutil
import json
import sys
import tempfile
import threading
import modules.globals as BLglobals
from modules.log import log
from modules.paths import app_path

# 辅助函数：获取源配置文件的路径（兼容开发环境、PyInstaller、Nuitka）
def get_source_config_path():
    # 统一使用应用资源根目录，避免从快捷方式/其它 cwd 启动时找不到默认配置。
    return app_path('config.json')

# 获取默认配置文件的真实路径
source_config_path = get_source_config_path()

# config_path = %appdata%/Bloret-Launcher/config.json
config_path = os.path.join(BLglobals.datapath, 'config.json')
_config_lock = threading.RLock()


def _atomic_write_json(path, data):
    """Write JSON atomically so crashes cannot leave a partial config file."""
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".config-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=4)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


#先检查目标配置文件是否存在
log(f"正在检查配置文件路径: {config_path}")
log(f"源配置文件路径: {source_config_path}")
log(f"默认配置文件是否存在: {os.path.exists(source_config_path)}")

if not os.path.exists(config_path):
    log(f"目标配置文件未找到: {config_path}")

    # 确保目标目录存在
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        log(f"配置目录不存在，正在创建: {config_dir}")
        os.makedirs(config_dir, exist_ok=True)
        log(f"配置目录已创建: {config_dir}")

    # 首次运行不自动创建配置文件，等待 OOBE 完成后生成
    # 这样可以确保 config.json 是用户实际配置的结果
    log("首次运行：跳过默认配置文件复制，等待 OOBE 完成后生成")
    
else:
    log(f"目标配置文件已存在: {config_path}")
    # 检查并执行版本更新逻辑
    try:
        log(f"正在读取配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        log(f"成功读取配置文件，正在检查版本字段...")

        # 检查默认配置文件是否存在
        if os.path.exists(source_config_path):
            with open(source_config_path, 'r', encoding='utf-8') as f:
                default_config = json.load(f)

            current_ver = config.get('ver')
            default_ver = default_config.get('ver')

            log(f"当前配置文件版本: {current_ver}")
            log(f"默认配置文件版本: {default_ver}")

            if current_ver != default_ver:
                log(f"配置文件版本不匹配（当前: {current_ver}, 目标: {default_ver}），正在执行增量更新...")
                # 备份
                shutil.copyfile(config_path, config_path + ".back")

                # 增量合并：以旧配置(config)为主，补全缺少的默认项(default_config)
                updated_config = default_config.copy()
                updated_config.update(config) # config 的内容会覆盖 default_config 的同名内容
                updated_config['ver'] = default_ver

                with _config_lock:
                    _atomic_write_json(config_path, updated_config)
                log(f"配置文件版本已从 {current_ver} 安全升级到 {default_ver}")
            else:
                log("配置文件版本匹配，无需更新")
        else:
            log("警告：默认配置文件 config.json 不存在，无法进行版本检查")

    except FileNotFoundError:
        log(f"错误：配置文件 {config_path} 不存在")
    except json.JSONDecodeError as e:
        log(f"错误：配置文件格式不正确: {str(e)}")
        # 如果配置文件损坏，尝试用默认配置替换
        if os.path.exists(source_config_path):
            log("尝试用默认配置文件替换损坏的配置文件...")
            shutil.copyfile(source_config_path, config_path)
            log("配置文件已替换")
    except Exception as e:
        log(f"读取配置文件时发生未知错误: {str(e)}")

BLglobals.config_path = config_path
log("配置文件路径: " + config_path)


def _summarize_config_for_log(config):
    """输出配置摘要，避免把账号令牌、密码和 session 写入日志。"""
    if not isinstance(config, dict):
        return config

    sensitive_markers = ("password", "token", "session", "sig", "passport")
    summary = {}
    for key, value in config.items():
        key_lower = str(key).lower()
        if any(marker in key_lower for marker in sensitive_markers):
            summary[key] = "***"
        elif isinstance(value, dict):
            summary[key] = f"<dict:{len(value)} keys>"
        elif isinstance(value, list):
            summary[key] = f"<list:{len(value)} items>"
        else:
            summary[key] = value
    return summary


def read():
    path = BLglobals.config_path
    with _config_lock:
        if not os.path.exists(path):
            log(f"读取时发现配置文件不存在: {path}，返回空配置")
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log(f"read() 读取配置文件失败: {str(e)}，返回空配置")
            return {}


def _sanitize_hook_value(key, value):
    """钩子 payload 脱敏：token/password/session 等不进入插件事件。"""
    key_lower = str(key or "").lower()
    sensitive_markers = ("password", "token", "session", "sig", "secret", "passport_password")
    if any(m in key_lower for m in sensitive_markers):
        return "***"
    if isinstance(value, dict):
        # MinecraftAccount 等：只给结构摘要，不泄露 accounts 内 token
        if "account" in key_lower or "passport" in key_lower:
            return {
                "logined": bool(value.get("logined")) if isinstance(value.get("logined"), (bool, int)) else value.get("logined"),
                "chosen": value.get("chosen"),
                "account_count": len(value.get("accounts") or []) if isinstance(value.get("accounts"), list) else None,
            }
        return f"<dict:{len(value)} keys>"
    if isinstance(value, list):
        return f"<list:{len(value)} items>"
    return value


def _fire_config_changed(changed_keys=None):
    """Dispatch plugin hooks after the config lock has been released."""
    try:
        from modules.plugin_host.hook_util import fire

        if isinstance(changed_keys, dict) and changed_keys:
            for key, value in changed_keys.items():
                fire("config.changed", key, _sanitize_hook_value(key, value))
        else:
            fire("config.changed", "*", None)
    except Exception as e:
        log(f"write() 派发 config.changed 失败: {e}")


def write(config, *, changed_keys=None, fire_hooks=True):
    """
    将配置写入磁盘，并（默认）派发 config.changed 钩子。

    所有设置页 / Backend / Web 保存应走此函数，避免直接 json.dump 绕过插件事件。

    Args:
        config: 完整配置 dict
        changed_keys: 可选 dict{key: new_value}；若提供则按键派发，否则派发 ("*", None)
        fire_hooks: 版本迁移等内部写入可设 False
    """
    if not isinstance(config, dict):
        raise TypeError("config must be a dict")
    path = getattr(BLglobals, "config_path", None) or config_path
    try:
        with _config_lock:
            _atomic_write_json(path, config)
    except Exception as e:
        log(f"write() 写入配置失败: {e}")
        return False

    if fire_hooks:
        _fire_config_changed(changed_keys)
    return True


def update_keys(**kwargs):
    """Atomically read, update and persist several configuration keys."""
    path = getattr(BLglobals, "config_path", None) or config_path
    try:
        with _config_lock:
            data = read() or {}
            data.update(kwargs)
            _atomic_write_json(path, data)
    except Exception as e:
        log(f"update_keys() 写入配置失败: {e}")
        return {}
    _fire_config_changed(dict(kwargs))
    return data

try:
    log(f"正在读取最终配置文件: {BLglobals.config_path}")
    config_data = read()
    log(f"成功读取配置文件内容摘要: {_summarize_config_for_log(config_data)}")

    BLglobals.minecraft_dir = config_data.get('minecraft_dir', '')
    log(f"Minecraft目录已设置为: '{BLglobals.minecraft_dir}'")

    BLglobals.download_source = config_data.get('download_source', 'gitcode')
    log(f"下载源: {BLglobals.download_source}")

    BLglobals.proxy = config_data.get('proxy', '')
    log(f"代理: {BLglobals.proxy or '(无)'}")

    # 检查minecraft目录是否存在
    if BLglobals.minecraft_dir:
        if os.path.exists(BLglobals.minecraft_dir):
            log(f"Minecraft目录存在: {BLglobals.minecraft_dir}")
        else:
            log(f"警告：Minecraft目录不存在: {BLglobals.minecraft_dir}")
    else:
        log("警告：Minecraft目录未设置（为空字符串）")

except Exception as e:
    log(f"读取配置文件失败: {str(e)}")
    BLglobals.minecraft_dir = ''
    log("Minecraft目录已设置为空字符串作为默认值")
