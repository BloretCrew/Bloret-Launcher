from PyQt5.QtWidgets import QLabel
from qfluentwidgets import SubtitleLabel,MessageBoxBase,InfoBar,InfoBarPosition,Dialog, LineEdit, MessageBox
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText


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
        with open('config.json', 'r', encoding='utf-8') as f:
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
        with open('config.json', 'r', encoding='utf-8') as f:
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
    
    open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
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

def sync_mc_account_to_bloret_passport(parent_window=None):
    log("=== sync_mc_account_to_bloret_passport 函数开始执行 ===")
    
    # 添加用户确认对话框
    if parent_window:
        w = MessageBox(i18nText("是否将本地 Minecraft 账户同步到Bloret Passport？"), i18nText("同步到云端后，您可以在其他设备上登录 Bloret PassPort，然后快速恢复 Minecraft 账户登录。"), parent_window)
        if not w.exec():
            log("用户取消了同步操作")
            return False
    
    try:
        log("正在读取 config.json 获取用户信息...")
        # 读取config.json获取用户信息
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        user = config_data.get('Bloret_PassPort_UserName', '')
        usertoken = config_data.get('Bloret_PassPort_PassWord', '')
        
        log(f"config.json 中的用户: {user}")
        
        if not user or not usertoken:
            log("错误: 用户未登录 Bloret PassPort")
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), i18nText("请先登录 Bloret PassPort"), parent_window)
                error_msg.exec()
            return False
        
        log("正在读取 cmcl.json 获取 Minecraft 账户数据...")
        # 读取cmcl.json获取Minecraft账户数据
        try:
            with open('cmcl.json', 'r', encoding='utf-8') as f:
                cmcl_data = json.load(f)
            log(f"成功读取 cmcl.json，包含 {len(cmcl_data)} 个账户")
            log(f"cmcl.json 内容预览: {str(cmcl_data)[:200]}...")
        except FileNotFoundError:
            log("错误: 找不到 cmcl.json 文件")
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), i18nText("未找到 Minecraft 账户数据文件"), parent_window)
                error_msg.exec()
            return False
        except json.JSONDecodeError as e:
            log(f"错误: cmcl.json 文件格式错误 - {str(e)}")
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), f"{i18nText('Minecraft 账户数据文件格式错误')}: {str(e)}", parent_window)
                error_msg.exec()
            return False
        
        # 将cmcl_data转换为字符串作为data参数
        data = json.dumps(cmcl_data, ensure_ascii=False)
        log(f"Minecraft 账户数据 JSON 字符串长度: {len(data)} 字符")
        
        # 构建请求URL
        url = (f"http://pcfs.eno.ink:20000/app/data/save?"
               f"app_id=BloretLauncher&"
               f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
               f"user={user}&"
               f"usertoken={usertoken}&"
               f"key=MinecraftAccount&"
               f"data={requests.utils.quote(data)}")
        
        log(f"请求 URL: {url[:150]}...")
        
        # 发送GET请求
        log("正在发送 HTTP 请求...")
        response = requests.get(url, timeout=30)
        log(f"HTTP 响应状态码: {response.status_code}")
        log(f"HTTP 响应内容: {response.text}")
        
        if response.status_code == 200:
            log(f"成功同步 Minecraft 账户到 Bloret Passport: {response.text}")
            # 添加成功提示
            if parent_window:
                success_msg = MessageBox(i18nText("同步成功"), i18nText("已成功将本地 Minecraft 账户同步到 Bloret Passport"), parent_window)
                success_msg.exec()
            return True
        else:
            log(f"同步Minecraft账户到Bloret Passport失败: {response.status_code} - {response.text}")
            # 添加失败提示
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), 
                                     f"{i18nText('同步 Minecraft 账户到 Bloret Passport失败')}: {response.status_code}", 
                                     parent_window)
                error_msg.exec()
            return False
    except requests.exceptions.Timeout:
        log("错误: 请求超时")
        if parent_window:
            error_msg = MessageBox(i18nText("同步失败"), i18nText("连接服务器超时，请检查网络连接"), parent_window)
            error_msg.exec()
        return False
    except requests.exceptions.ConnectionError as e:
        log(f"错误: 连接失败 - {str(e)}")
        if parent_window:
            error_msg = MessageBox(i18nText("同步失败"), i18nText("无法连接到服务器，请检查网络连接"), parent_window)
            error_msg.exec()
        return False
    except Exception as e:
        log(f"同步Minecraft账户到Bloret Passport时出错: {str(e)}")
        log(f"异常类型: {type(e)}")
        handle_exception(type(e), e, e.__traceback__)
        # 添加错误提示
        if parent_window:
            error_msg = MessageBox(i18nText("同步出错"), 
                                 f"{i18nText('同步过程中发生错误')}: {str(e)}", 
                                 parent_window)
            error_msg.exec()
        return False
    finally:
        log("=== sync_mc_account_to_bloret_passport 函数执行结束 ===")

def sync_bloret_passport_account_to_mc(parent_window=None):
    log("=== sync_bloret_passport_account_to_mc 函数开始执行 ===")
    
    # 兼容处理传入的参数，如果是字符串则忽略
    if isinstance(parent_window, str):
        parent_window = None
    
    # 添加用户确认对话框
    if parent_window:
        w = MessageBox(i18nText("是否将 Bloret Passport 账户同步到本地 Minecraft 账户？"), i18nText("确定要从 Bloret Passport 同步 Minecraft 账户 到本地吗？这将覆盖本地账户数据。"), parent_window)
        if not w.exec():
            log("用户取消了同步操作")
            return False
    
    try:
        log("正在读取 config.json 获取用户信息...")
        # 读取config.json获取用户信息
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        user = config_data.get('Bloret_PassPort_UserName', '')
        usertoken = config_data.get('Bloret_PassPort_PassWord', '')
        
        log(f"config.json 中的用户: {user}")
        
        if not user or not usertoken:
            log("错误: 用户未登录 Bloret PassPort")
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), i18nText("请先登录 Bloret PassPort"), parent_window)
                error_msg.exec()
            return False
        
        # 构建请求URL
        url = (f"http://pcfs.eno.ink:20000/app/data/read?"
               f"app_id=BloretLauncher&"
               f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
               f"user={user}&"
               f"usertoken={usertoken}&"
               f"key=MinecraftAccount")
        
        log(f"请求 URL: {url}")
        
        # 发送GET请求
        log("正在发送 HTTP 请求...")
        response = requests.get(url, timeout=30)
        log(f"HTTP 响应状态码: {response.status_code}")
        log(f"HTTP 响应内容: {response.text}")
        
        if response.status_code == 200:
            # 解析返回的JSON数据
            try:
                response_data = response.json()
                log(f"成功解析 JSON 响应: {response_data}")
                
                # 检查是否有错误信息
                if 'error' in response_data:
                    log(f"从 Bloret Passport 获取 Minecraft 账户失败: {response_data['error']}")
                    # 添加失败提示
                    if parent_window:
                        error_msg = MessageBox(i18nText("同步失败"), 
                                             f"{i18nText('从 Bloret Passport 获取 Minecraft 账户失败')}: {response_data['error']}", 
                                             parent_window)
                        error_msg.exec()
                    return False
                
                # 获取data字段并写入cmcl.json
                if 'data' in response_data:
                    cmcl_data = response_data['data']
                    log(f"获取到数据，类型: {type(cmcl_data)}")
                    
                    # 确保cmcl_data是dict类型而不是字符串
                    if isinstance(cmcl_data, str):
                        log("数据是字符串类型，正在解析为 JSON...")
                        cmcl_data = json.loads(cmcl_data)
                        log("JSON 解析成功")
                    
                    # 写入到cmcl.json
                    log("正在写入 cmcl.json 文件...")
                    with open('cmcl.json', 'w', encoding='utf-8') as f:
                        json.dump(cmcl_data, f, ensure_ascii=False, indent=4)
                    
                    log("成功从 Bloret Passport 同步 Minecraft 账户到本地")
                    # 添加成功提示
                    if parent_window:
                        success_msg = MessageBox(i18nText("已成功从 Bloret Passport 同步 Minecraft 账户到本地"), i18nText("界面上可能不会及时刷新，但已经登录。"), parent_window)
                        success_msg.exec()
                    return True
                else:
                    log("从Bloret Passport返回的数据中未找到data字段")
                    # 添加失败提示
                    if parent_window:
                        error_msg = MessageBox(i18nText("同步失败"), i18nText("从Bloret Passport返回的数据中未找到账户信息"), parent_window)
                        error_msg.exec()
                    return False
            except json.JSONDecodeError as e:
                log(f"解析 JSON 响应失败: {str(e)}")
                log(f"原始响应内容: {response.text}")
                # 添加错误提示
                if parent_window:
                    error_msg = MessageBox(i18nText("同步出错"), 
                                         f"{i18nText('同步过程中JSON解析错误')}: {str(e)}", 
                                         parent_window)
                    error_msg.exec()
                return False
        else:
            log(f"从Bloret Passport获取Minecraft账户失败: {response.status_code} - {response.text}")
            # 添加失败提示
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), 
                                     f"{i18nText('从Bloret Passport获取Minecraft账户失败')}: {response.status_code}", 
                                     parent_window)
                error_msg.exec()
            return False
    except requests.exceptions.Timeout:
        log("错误: 请求超时")
        if parent_window:
            error_msg = MessageBox(i18nText("同步失败"), i18nText("连接服务器超时，请检查网络连接"), parent_window)
            error_msg.exec()
        return False
    except requests.exceptions.ConnectionError as e:
        log(f"错误: 连接失败 - {str(e)}")
        if parent_window:
            error_msg = MessageBox(i18nText("同步失败"), i18nText("无法连接到服务器，请检查网络连接"), parent_window)
            error_msg.exec()
        return False
    except json.JSONDecodeError as e:
        log(f"从Bloret Passport同步Minecraft账户到本地时JSON解析错误: {str(e)}")
        # 添加错误提示
        if parent_window:
            error_msg = MessageBox(i18nText("同步出错"), 
                                 f"{i18nText('同步过程中JSON解析错误')}: {str(e)}", 
                                 parent_window)
            error_msg.exec()
        return False
    except Exception as e:
        log(f"从Bloret Passport同步Minecraft账户到本地时出错: {str(e)}")
        log(f"异常类型: {type(e)}")
        handle_exception(type(e), e, e.__traceback__)
        # 添加错误提示
        if parent_window:
            error_msg = MessageBox(i18nText("同步出错"), 
                                 f"{i18nText('同步过程中发生错误')}: {str(e)}", 
                                 parent_window)
            error_msg.exec()
        return False
    finally:
        log("=== sync_bloret_passport_account_to_mc 函数执行结束 ===")