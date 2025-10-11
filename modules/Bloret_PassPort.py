from PyQt5.QtWidgets import QLabel
from qfluentwidgets import SubtitleLabel,MessageBoxBase,InfoBar,InfoBarPosition,Dialog, LineEdit, MessageBox
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText



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
    # 添加用户确认对话框
    if parent_window:
        w = MessageBox(i18nText("是否将本地 Minecraft 账户同步到Bloret Passport？"), i18nText("同步到云端后，您可以在其他设备上登录 Bloret PassPort，然后快速恢复 Minecraft 账户登录。"), parent_window)
        if not w.exec():
            log("用户取消了同步操作")
            return False
    
    try:
        # 读取config.json获取用户信息
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        user = config_data.get('Bloret_PassPort_UserName', '')
        usertoken = config_data.get('Bloret_PassPort_PassWord', '')
        
        # 读取cmcl.json获取Minecraft账户数据
        with open('cmcl.json', 'r', encoding='utf-8') as f:
            cmcl_data = json.load(f)
        
        # 将cmcl_data转换为字符串作为data参数
        data = json.dumps(cmcl_data, ensure_ascii=False)
        
        # 构建请求URL
        url = (f"http://pcfs.eno.ink:20000/app/data/save?"
               f"app_id=BloretLauncher&"
               f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
               f"user={user}&"
               f"usertoken={usertoken}&"
               f"key=MinecraftAccount&"
               f"data={requests.utils.quote(data)}")
        
        # 发送GET请求
        response = requests.get(url)
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
    except Exception as e:
        log(f"同步Minecraft账户到Bloret Passport时出错: {str(e)}")
        handle_exception(type(e), e, e.__traceback__)
        # 添加错误提示
        if parent_window:
            error_msg = MessageBox(i18nText("同步出错"), 
                                 f"{i18nText('同步过程中发生错误')}: {str(e)}", 
                                 parent_window)
            error_msg.exec()
        return False

def sync_bloret_passport_account_to_mc(parent_window=None):
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
        # 读取config.json获取用户信息
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        user = config_data.get('Bloret_PassPort_UserName', '')
        usertoken = config_data.get('Bloret_PassPort_PassWord', '')
        
        # 构建请求URL
        url = (f"http://pcfs.eno.ink:20000/app/data/read?"
               f"app_id=BloretLauncher&"
               f"app_secret=s4d56f4a68sd46g54asd46f54a5dsf654asdf546&"
               f"user={user}&"
               f"usertoken={usertoken}&"
               f"key=MinecraftAccount")
        
        # 发送GET请求
        response = requests.get(url)
        if response.status_code == 200:
            # 解析返回的JSON数据
            response_data = response.json()
            
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
                
                # 确保cmcl_data是dict类型而不是字符串
                if isinstance(cmcl_data, str):
                    cmcl_data = json.loads(cmcl_data)
                
                # 写入到cmcl.json
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
        else:
            log(f"从Bloret Passport获取Minecraft账户失败: {response.status_code} - {response.text}")
            # 添加失败提示
            if parent_window:
                error_msg = MessageBox(i18nText("同步失败"), 
                                     f"{i18nText('从Bloret Passport获取Minecraft账户失败')}: {response.status_code}", 
                                     parent_window)
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
        handle_exception(type(e), e, e.__traceback__)
        # 添加错误提示
        if parent_window:
            error_msg = MessageBox(i18nText("同步出错"), 
                                 f"{i18nText('同步过程中发生错误')}: {str(e)}", 
                                 parent_window)
            error_msg.exec()
        return False
