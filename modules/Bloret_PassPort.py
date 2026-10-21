from PySide6.QtWidgets import QLabel
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText
import modules.globals as BLglobals
import modules.config as cfg

def _public_data_url(operation):
    return f"{BLglobals.server_ip}:20000/app/data/{operation}"


def _oauth_headers():
    config_data = cfg.read()
    oauth = config_data.get("Bloret_PassPort_OAuth") or {}
    token = oauth.get("access_token")
    if not token:
        raise PermissionError("Passport OAuth authorization required")
    return {"Authorization": "Bearer " + token}


def savedata(key, data, public=False):
    """Save public data, or authenticated data with an OAuth bearer token."""
    data_str = json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
    params = {"app_id": "BloretLauncher", "user": "public", "key": key, "data": data_str}
    headers = {} if public else _oauth_headers()
    if not public:
        params.pop("app_id", None)
        params.pop("user", None)
    try:
        response = requests.get(_public_data_url("save"), params=params, headers=headers, timeout=10)
        return response.status_code == 200
    except (PermissionError, requests.exceptions.RequestException, ValueError, TypeError):
        return False


def readdata(key, public=False):
    """Read public data, or authenticated data with an OAuth bearer token."""
    params = {"app_id": "BloretLauncher", "user": "public", "key": key}
    headers = {} if public else _oauth_headers()
    if not public:
        params.pop("app_id", None)
        params.pop("user", None)
    try:
        response = requests.get(_public_data_url("read"), params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text
    except (PermissionError, requests.exceptions.RequestException, ValueError, TypeError):
        return None

def process_2fa_request(token, request_id, action):
    """
    处理 2FA 请求
    action: 'approve' or 'deny'
    """
    url = f"{BLglobals.server_ip}:20000/api/2fa/process"
    data = {
        "token": token,
        "requestId": request_id,
        "action": action
    }
    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            log(f"处理2FA请求返回非200状态: {response.status_code}, {response.text}")
    except Exception as e:
        log(f"处理2FA请求网络异常: {e}")
    return None

def Bloret_PassPort_Account_logout(self, homeInterface):
    self.config.update(Bloret_PassPort_Login=False)
    self.config.update(Bloret_PassPort_UserName=i18nText(''))
    self.config.update(Bloret_PassPort_PassWord='')
    self.config.update(Bloret_PassPort_Admin=False)

    cfg.write(self.config)
    # 更新界面显示
    Bloret_PassPort_User_UserName = homeInterface.findChild(QLabel, "Bloret_PassPort_UserName")
    if Bloret_PassPort_User_UserName:
        Bloret_PassPort_User_UserName.setText(i18nText("未登录"))
    else:
        log("警告: 未找到 Bloret_PassPort_UserName 控件")

    InfoBar.success(
        title=i18nText('⏫ 已退出登录'),
        content="",
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=5000,
        parent=self
    )
    Bloret_PassPort_Name = homeInterface.findChild(QLabel, "Bloret_PassPort_Name")
    if Bloret_PassPort_Name:
        Bloret_PassPort_Name.setText(i18nText("未登录"))
    else:
        log("警告: 未找到 Bloret_PassPort_Name 控件")
    log(i18nText("已退出登录"))

def normalize_minecraft_accounts(userinfo):
    """Accept only an explicit list under the agreed local OAuth fixture keys."""
    if not isinstance(userinfo, dict):
        raise ValueError("Invalid Passport userinfo response")
    if "accounts" in userinfo:
        accounts = userinfo["accounts"]
    elif "minecraft_accounts" in userinfo:
        accounts = userinfo["minecraft_accounts"]
    else:
        raise ValueError("Passport userinfo omitted Minecraft account data")
    if not isinstance(accounts, list) or not all(isinstance(account, dict) for account in accounts):
        raise ValueError("Invalid Passport Minecraft account data")
    return accounts


def sync_bloret_passport_account_to_mc(parent_window=None):
    log("=== sync_bloret_passport_account_to_mc 函数开始执行 (同步逻辑已对齐 web.py) ===")

    # 兼容处理传入的参数
    if isinstance(parent_window, str):
        parent_window = None

    try:
        log("正在读取 config.json 获取用户信息...")
        # 1. 读取 config.json
        config_data = cfg.read()

        # 检查是否已登录 Passport
        if not config_data.get('Bloret_PassPort_Login'):
            log("错误: 用户未登录 Bloret PassPort")
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), i18nText("请先登录 Bloret PassPort"), parent_window)
                error_msg.exec()
            return False

        username = config_data.get('Bloret_PassPort_UserName')
        oauth = config_data.get('Bloret_PassPort_OAuth') or {}
        from modules.passport_oauth import PassportOAuthCoordinator
        coordinator = PassportOAuthCoordinator()
        if coordinator.access_token_status(oauth) in {"expired", "reauthorization_required"}:
            log("Passport OAuth token expired; reauthorization required")
            return False
        access_token = oauth.get('access_token')
        if not access_token:
            log("错误: 缺少 Passport OAuth access token")
            return False

        # 2. Passport account synchronization uses the OAuth bearer token.
        verify_url = "https://passport.bloret.net/oauth/minecraft/accounts"
        log("正在请求 Passport OAuth Minecraft accounts")
        response = requests.get(verify_url, headers={"Authorization": "Bearer " + access_token}, timeout=30)
        if response.status_code == 401:
            log("Passport access token 无效或已过期")
            return False
        if response.status_code == 403:
            log("请重新登录 Bloret PassPort 并授权读取 Minecraft 档案")
            return False
        response.raise_for_status()
        api_result = response.json()
        log("Passport Minecraft accounts 请求成功")

        # 3. Preserve existing account selection while applying returned accounts.
        accounts = normalize_minecraft_accounts(api_result)

        # 获取旧的 chosen 值，如果不存在或越界，则默认为 0
        old_minecraft_account = config_data.get('MinecraftAccount', {})
        old_chosen = old_minecraft_account.get('chosen', 0)

        # 如果之前的 chosen 索引在新列表中仍然有效，则保持不变；否则重置为 0
        new_chosen = old_chosen if 0 <= old_chosen < len(accounts) else (0 if accounts else -1)

        new_account_data = {
            "logined": True if accounts else False,
            "chosen": new_chosen,
            "accounts": accounts
        }
        config_data['MinecraftAccount'] = new_account_data

        # 同时更新头像信息（如果服务器返回了 avatar 字段）
        if 'avatar' in api_result:
            config_data['Bloret_PassPort_Avatar'] = api_result['avatar']
            log(f"已更新用户头像: {api_result['avatar']}" )

        # 保存配置到 config.json
        if not cfg.write(config_data):
            log("Passport account sync persistence failed")
            return False

        # 关键补充：如果传入了 parent_window (MainWindow)，同步更新其内存中的 config
        if parent_window and hasattr(parent_window, 'config'):
            parent_window.config['MinecraftAccount'] = new_account_data
            log("已同步更新 MainWindow 内存配置")
        log(f"成功同步 {len(accounts)} 个账户到 config.json")
        try:
            from modules.plugin_host.dispatch import invoke_hook
            invoke_hook(
                "passport.sync",
                {
                    "username": username,
                    "account_count": len(accounts),
                    "source": "passport",
                },
            )
            # 仅在 Minecraft 账户从未登录变为已登录时广播生命周期转换。
            if accounts and not bool(old_minecraft_account.get("logined")):
                invoke_hook(
                    "account.login",
                    {
                        "username": username,
                        "account_count": len(accounts),
                        "source": "passport",
                    },
                )
                log(f"[PluginHost] account.login user={username} n={len(accounts)}")
            log(f"[PluginHost] passport.sync user={username} n={len(accounts)}")
        except Exception as plugin_err:
            log(f"[PluginHost] passport.sync 失败: {plugin_err}")

        return True

    except Exception as e:
        log(f"从 Bloret Passport 同步账户时出错: {str(e)}")
        log(f"异常类型: {type(e)}")
        handle_exception(type(e), e, e.__traceback__)
        return False
    finally:
        log("=== sync_bloret_passport_account_to_mc 函数执行结束 ===")

def refresh_minecraft_token():
    """
    刷新 Minecraft Token
    """
    log("=== refresh_minecraft_token 函数开始执行 ===")
    try:
        config_data = cfg.read()
        if not config_data.get('Bloret_PassPort_Login'):
            log("用户未登录 Bloret PassPort，跳过 Token 刷新")
            return False

        oauth = config_data.get('Bloret_PassPort_OAuth') or {}
        from modules.passport_oauth import PassportOAuthCoordinator
        coordinator = PassportOAuthCoordinator()
        status = coordinator.access_token_status(oauth)
        if status == "expired":
            refresh_token = oauth.get("refresh_token")
            if not refresh_token:
                log("Passport OAuth token expired; reauthorization required")
                return False
            try:
                refreshed = coordinator.refresh_access_token(oauth)
            except PermissionError:
                log("Passport refresh rejected; reauthorization required")
                return False
            config_data["Bloret_PassPort_OAuth"] = refreshed
            if not cfg.write(config_data):
                log("Passport token refresh persistence failed")
                return False
            return True
        if status == "reauthorization_required":
            log("缺少 Passport OAuth access token，需重新授权")
            return False
        if status == "unknown_expiry":
            log("Passport OAuth token expiry metadata unavailable; reauthorization required")
            return False
        return True

    except Exception as e:
        log(f"刷新 Minecraft Token 时发生异常: {e}")
        return False
    finally:
        log("=== refresh_minecraft_token 函数执行结束 ===")

def prepare_minecraft_launch_account():
    """
    在启动 Minecraft 前调用的准备函数
    1. 刷新 Minecraft Token
    2. 同步最新的账户信息
    """
    log("正在准备 Minecraft 启动账户...")

    # 1. 刷新 Token
    refresh_result = refresh_minecraft_token()
    if not refresh_result:
        log("Minecraft Token 刷新失败或不需要刷新，尝试继续同步...", logging.WARNING)

    # 2. 同步账户信息 (不显示弹窗)
    # 注意：sync_bloret_passport_account_to_mc 会更新 config.json
    # 后续的 Get_Run_Script 会读取最新的 config.json
    sync_result = sync_bloret_passport_account_to_mc(parent_window=None)
    if not sync_result:
        log("Minecraft 账户同步失败，将使用本地缓存的账户信息启动", logging.WARNING)

    log("Minecraft 启动账户准备完成")

def get_pending_2fa_requests(username, token):
    """
    获取待处理的 2FA 请求
    """
    url = f"{BLglobals.server_ip}:20000/api/2fa/pending"
    params = {
        'username': username,
        'token': token
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log(f"获取2FA请求失败: {e}")
    return None

def handle_2fa_request_action(username, token, request_id, action):
    """
    处理 2FA 请求动作 (同意/拒绝)
    """
    return process_2fa_request(token, request_id, action)
