from PySide6.QtWidgets import QLabel
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText
import modules.globals as BLglobals
import modules.config as cfg

def savedata(key, data, public=False):
    '''
    存储信息到 Bloret PassPort 服务器
    '''
    log(f"=== savedata 函数开始执行 ===")
    log(f"参数: key='{key}', public={public}")
    log(f"数据类型: {type(data)}")
    
    try:
        # 读取config.json获取用户信息
        log("正在读取 config.json 文件...")
        with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        log(f"成功读取 config.json，包含用户: {config_data.get('Bloret_PassPort_UserName', '未设置')}")
        
        user = config_data.get('Bloret_PassPort_UserName', '')
        usertoken = config_data.get('Bloret_PassPort_PassWord', '')
        
        # 如果 data 是字典或列表，转换为 JSON 字符串
        if isinstance(data, (dict, list)):
            log("数据是字典或列表类型，正在转换为 JSON 字符串...")
            data_str = json.dumps(data, ensure_ascii=False)
            log(f"JSON 转换完成，数据长度: {len(data_str)} 字符")
        elif isinstance(data, str):
            log("数据已经是字符串类型")
            data_str = data
        else:
            log(f"数据类型为 {type(data)}，强制转换为字符串")
            data_str = str(data)
        
        # 构建请求URL
        if public:
            log("使用公共模式存储数据")
            url = (f"{BLglobals.server_ip}:20000/app/data/save?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user=public&"
                    f"key={key}&"
                    f"data={data_str}")
            # 公共模式下 URL 不包含用户密码，直接记录部分信息
            log(f"请求URL(已脱敏): {BLglobals.server_ip}:20000/app/data/save?user=public&key={key}&data_length={len(data_str)}")
        else:
            log(f"使用用户模式存储数据，用户: {user}")
            url = (f"{BLglobals.server_ip}:20000/app/data/save?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user={user}&"
                    f"usertoken={usertoken}&"
                    f"key={key}&"
                    f"data={data_str}")
            # 用户模式下 URL 包含 usertoken，这里记录脱敏后的 URL 信息，避免泄露密码
            log(f"请求URL(已脱敏): {BLglobals.server_ip}:20000/app/data/save?user={user}&key={key}&data_length={len(data_str)}")
        
        response = requests.get(url, timeout=10)
        log(f"HTTP 响应状态码: {response.status_code}")
        log(f"HTTP 响应内容: {response.text}")
        
        if response.status_code == 200:
            log(i18nText("成功存储数据到 Bloret PassPort 服务器"))
            log(f"存储的 key: {key}")
            return True
        else:
            log(f"存储数据到 Bloret PassPort 服务器失败，状态码: {response.status_code}")
            return False
            
    except FileNotFoundError as e:
        log(f"savedata 错误: 找不到配置文件 - {str(e)}")
        return False
    except json.JSONDecodeError as e:
        log(f"savedata 错误: JSON 解析失败 - {str(e)}")
        return False
    except requests.exceptions.RequestException as e:
        log(f"savedata 错误: HTTP 请求失败 - {str(e)}")
        return False
    except Exception as e:
        log(f"savedata 错误: 未知异常 - {str(e)}")
        log(f"异常类型: {type(e)}")
        return False
    finally:
        log("=== savedata 函数执行结束 ===")

def readdata(key, public=False):
    '''
    从 Bloret PassPort 服务器读取信息
    '''
    log(f"=== readdata 函数开始执行 ===")
    log(f"参数: key='{key}', public={public}")
    
    try:
        # 读取config.json获取用户信息
        log("正在读取 config.json 文件...")
        with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        log(f"成功读取 config.json，包含用户: {config_data.get('Bloret_PassPort_UserName', '未设置')}")
        
        user = config_data.get('Bloret_PassPort_UserName', '')
        usertoken = config_data.get('Bloret_PassPort_PassWord', '')
        
        # 构建请求URL
        if public:
            log("使用公共模式读取数据")
            url = (f"{BLglobals.server_ip}:20000/app/data/read?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user=public&"
                    f"key={key}")
            # 公共模式下 URL 不包含用户密码
            log(f"请求URL: {url}")
        else:
            log(f"使用用户模式读取数据，用户: {user}")
            url = (f"{BLglobals.server_ip}:20000/app/data/read?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user={user}&"
                    f"usertoken={usertoken}&"
                    f"key={key}")
            # 用户模式下 URL 包含 usertoken，这里记录脱敏后的 URL 信息
            log(f"请求URL(已脱敏): {BLglobals.server_ip}:20000/app/data/read?user={user}&key={key}")
        
        response = requests.get(url, timeout=10)
        log(f"HTTP 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            log(i18nText("成功从 Bloret PassPort 服务器读取数据"))
            result = response.text
            # 尝试解析 JSON，如果不是 JSON 则直接返回字符串
            try:
                # 检查是否看起来像 JSON
                if (result.startswith('{') and result.endswith('}')) or (result.startswith('[') and result.endswith(']')):
                    json_result = json.loads(result)
                    log("数据已解析为 JSON 对象")
                    return json_result
            except json.JSONDecodeError:
                pass
            
            log("数据作为字符串返回")
            return result
        else:
            log(f"从 Bloret PassPort 服务器读取数据失败，状态码: {response.status_code}")
            return None
            
    except FileNotFoundError as e:
        log(f"readdata 错误: 找不到配置文件 - {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        log(f"readdata 错误: HTTP 请求失败 - {str(e)}")
        return None
    except Exception as e:
        log(f"readdata 错误: 未知异常 - {str(e)}")
        return None
    finally:
        log("=== readdata 函数执行结束 ===")

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
        user_token = config_data.get('Bloret_PassPort_PassWord')
        
        # 2. 向验证服务器发送请求获取 Minecraft 账户列表 (对齐 web.py 逻辑)
        verify_url = f"{BLglobals.server_ip}:20000/app/MinecraftAccounts"
        params = {
            'app_id': 'BloretLauncher',
            'app_secret': 's4d56f4a68sd46g54asd46f54a5dsf654asdf546',
            'user': username,
            'usertoken': user_token
        }
        
        log(f"正在请求接口: {verify_url}")
        response = requests.get(verify_url, params=params, timeout=30)
        api_result = response.json()
        log(f"接口返回状态: {api_result.get('status')}")
        
        if api_result.get('status') == 'success':
            # 3. 更新 config.json 中的 MinecraftAccount 字段
            accounts = api_result.get('accounts', [])
            
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
                log(f"已更新用户头像: {api_result['avatar']}")
            
            # 保存配置到 config.json
            cfg.write(config_data)
            
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
        else:
            message = api_result.get('message', '未知错误')
            raise Exception(f"服务器返回错误: {message}")

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

        username = config_data.get('Bloret_PassPort_UserName')
        if not username:
            log("未找到用户名，跳过 Token 刷新")
            return False

        url = f"{BLglobals.server_ip}:20000/api/login/Minecraft/Refresh"
        headers = {
            'Cookie': f'username={username}'
        }

        log(f"正在请求刷新 Token 接口: {url}")
        # 注意：这里不需要 json 数据，参数通过 Cookie 传递
        response = requests.post(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log(f"Token 刷新成功: {result.get('message')}")
                return True
            else:
                log(f"Token 刷新失败: {result.get('message')}")
                return False
        else:
            log(f"Token 刷新请求失败，状态码: {response.status_code}")
            try:
                log(f"响应内容: {response.text}")
            except:
                pass
            return False
            
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
