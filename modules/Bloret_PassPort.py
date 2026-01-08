from PyQt5.QtWidgets import QLabel
from qfluentwidgets import SubtitleLabel,MessageBoxBase,InfoBar,InfoBarPosition,Dialog, LineEdit, MessageBox
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
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
            url = (f"http://pcfs.eno.ink:20000/app/data/save?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user=public&"
                    f"key={key}&"
                    f"data={data_str}")
        else:
            log(f"使用用户模式存储数据，用户: {user}")
            url = (f"http://pcfs.eno.ink:20000/app/data/save?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user={user}&"
                    f"usertoken={usertoken}&"
                    f"key={key}&"
                    f"data={data_str}")
        
        log(f"请求URL: {url[:100]}...")  # 只记录前100个字符避免日志过长
        
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
            url = (f"http://pcfs.eno.ink:20000/app/data/read?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user=public&"
                    f"key={key}")
        else:
            log(f"使用用户模式读取数据，用户: {user}")
            url = (f"http://pcfs.eno.ink:20000/app/data/read?"
                    f"app_id=BloretLauncher&"
                    f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
                    f"user={user}&"
                    f"usertoken={usertoken}&"
                    f"key={key}")
        
        log(f"请求URL: {url}")
        
        response = requests.get(url, timeout=10)
        log(f"HTTP 响应状态码: {response.status_code}")
        log(f"HTTP 响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                log(f"成功解析 JSON 响应: {response_json}")
                
                if "data" in response_json:
                    data_content = response_json["data"]
                    log(f"成功读取数据，数据类型: {type(data_content)}")
                    if isinstance(data_content, str) and len(data_content) > 100:
                        log(f"数据内容(前100字符): {data_content[:100]}...")
                    else:
                        log(f"数据内容: {data_content}")
                    return data_content
                else:
                    log("响应中未找到 'data' 字段")
                    return None
            except json.JSONDecodeError as e:
                log(f"解析 JSON 响应失败: {str(e)}")
                log(f"原始响应内容: {response.text}")
                return None
        else:
            log(f"读取数据失败，状态码: {response.status_code}")
            return None
            
    except FileNotFoundError as e:
        log(f"readdata 错误: 找不到配置文件 - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log(f"readdata 错误: JSON 解析失败 - {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        log(f"readdata 错误: HTTP 请求失败 - {str(e)}")
        return None
    except Exception as e:
        log(f"readdata 错误: 未知异常 - {str(e)}")
        log(f"异常类型: {type(e)}")
        return None
    finally:
        log("=== readdata 函数执行结束 ===")


def Bloret_PassPort_Account_logout(self, homeInterface):
    self.config.update(Bloret_PassPort_Login=False)
    self.config.update(Bloret_PassPort_UserName=i18nText(''))
    self.config.update(Bloret_PassPort_PassWord='')
    self.config.update(Bloret_PassPort_Admin=False)
    
    open(BLglobals.config_path, 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
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
    
    # 添加用户确认对话框
    if parent_window:
        w = MessageBox(i18nText("是否从 Bloret Passport 同步账户？"), 
                      i18nText("确定要从云端同步 Minecraft 账户到本地配置吗？"), parent_window)
        if not w.exec():
            log("用户取消了同步操作")
            return False
    
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
        verify_url = "http://pcfs.eno.ink:20000/app/MinecraftAccounts"
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
            # 3. 更新 config.json 中的 MinecraftAccount 字段 (对齐 web.py 逻辑)
            accounts = api_result.get('accounts', [])
            
            new_account_data = {
                "logined": True if accounts else False,
                "chosen": 0 if accounts else -1,
                "accounts": accounts
            }
            config_data['MinecraftAccount'] = new_account_data
            
            # 保存配置到 config.json
            with open(BLglobals.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            
            # 关键补充：如果传入了 parent_window (MainWindow)，同步更新其内存中的 config
            # 这样用户不重启程序也能直接看到更新，且防止 save_config 覆盖
            if parent_window and hasattr(parent_window, 'config'):
                parent_window.config['MinecraftAccount'] = new_account_data
                log("已同步更新 MainWindow 内存配置")

            log(f"成功同步 {len(accounts)} 个账户到 config.json")
        else:
            message = api_result.get('message', '未知错误')
            raise Exception(f"服务器返回错误: {message}")

    except Exception as e:
        log(f"从 Bloret Passport 同步账户时出错: {str(e)}")
        log(f"异常类型: {type(e)}")
        handle_exception(type(e), e, e.__traceback__)
        if parent_window:
            error_msg = MessageBox(i18nText("同步失败"), f"{i18nText('同步过程中发生错误')}: {str(e)}", parent_window)
            error_msg.exec()
        return False
    finally:
        log("=== sync_bloret_passport_account_to_mc 函数执行结束 ===")

