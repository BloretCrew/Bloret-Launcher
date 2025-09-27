from PyQt5.QtWidgets import QLabel
from qfluentwidgets import SubtitleLabel,MessageBoxBase,InfoBar,InfoBarPosition,Dialog, LineEdit
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log, importlog
from modules.safe import handle_exception
from modules.i18n import i18nText

def Bloret_PassPort_Account_login(self, widget, server_ip, homeInterface):
    if not self.config.get('localmod', False):
        class CustomLoginDialog(MessageBoxBase):
            """ 自定义登录对话框 """
            def __init__(self, parent=None):
                super().__init__(parent)
                
                # 用户名组件
                self.usernameLabel = SubtitleLabel(i18nText('用户名'), self)
                self.usernameLineEdit = LineEdit(self)
                self.usernameLineEdit.setPlaceholderText(i18nText('请输入用户名'))
                
                # 密码组件
                self.passwordLabel = SubtitleLabel(i18nText('密码'), self)
                self.passwordLineEdit = LineEdit(self)
                self.passwordLineEdit.setPlaceholderText(i18nText('请输入密码'))
                self.passwordLineEdit.setEchoMode(LineEdit.Password)
                
                # 添加到布局
                self.viewLayout.addWidget(self.usernameLabel)
                self.viewLayout.addWidget(self.usernameLineEdit)
                self.viewLayout.addWidget(self.passwordLabel)
                self.viewLayout.addWidget(self.passwordLineEdit)
                
                self.widget.setMinimumWidth(350)

            def validate(self):
                """ 验证输入不能为空 """
                username = self.usernameLineEdit.text().strip()
                password = self.passwordLineEdit.text().strip()
                return bool(username and password)
        """ 登录账户方法 """
        dialog = CustomLoginDialog(self)
        if dialog.exec():  # 用户点击确认
            username = dialog.usernameLineEdit.text().strip()
            password = dialog.passwordLineEdit.text().strip()

            try:
                response = requests.get(
                    f"{server_ip}api/login",
                    params={"name": username, "password": password}
                )
                response_data = response.json()
                if response_data.get("status") is False:
                    error_message = response_data.get('message', i18nText('未知错误'))
                    log(f"登录失败:{error_message}", logging.ERROR)
                    InfoBar.error(
                        title=i18nText('❌ 登录失败'),
                        content=response_data.get("message", i18nText("未知错误")),
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                    return
                elif response_data.get("status") is True:
                    # 更新配置并记录日志
                    self.config['Bloret_PassPort_UserName'] = username
                    self.config['Bloret_PassPort_PassWord'] = password
                    self.config['Bloret_PassPort_Admin'] = response_data.get("admin", False)
                    log(f"登录成功: 用户名={username}", logging.INFO)
                    
                    # 更新界面显示
                    Bloret_PassPort_User_UserName = widget.findChild(QLabel, "Bloret_PassPort_UserName")
                    Bloret_PassPort_User_UserName.setText(username)

                    open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
                    InfoBar.success(
                        title=i18nText('✅ 登录成功'),
                        content="",
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                    Bloret_PassPort_Name = homeInterface.findChild(QLabel, "Bloret_PassPort_Name")
                    Bloret_PassPort_Name.setText(f"{username}")
            except Exception as e:
                handle_exception(e)
                log(i18nText("请求失败: %s") % str(e), logging.ERROR)
                InfoBar.error(
                    title=i18nText('❌ 登录失败'),
                    content=f"请求失败: {str(e)}",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
        else:
            log(i18nText("登录对话框被取消"), logging.INFO)
    else:
        log(i18nText("本地模式已启用，无法进行 Bloret 通行证登录。"))
        w = Dialog(i18nText("您已启用本地模式"), i18nText("Bloret Launcher 在本地模式下无法登录 Bloret 通行证，\n因为该操作需要互联网\n如果需要登录，请到设置界面关闭本地模式。"))
        if w.exec():
            print(i18nText('确认'))
        else:
            print(i18nText('取消'))
def Bloret_PassPort_Account_logout(self, homeInterface):
    self.config.update(Bloret_PassPort_UserName=i18nText('未登录'))
    self.config.update(Bloret_PassPort_PassWord='')
    self.config.update(Bloret_PassPort_Admin=False)
    
    open('config.json', 'w', encoding='utf-8').write(json.dumps(self.config, ensure_ascii=False, indent=4))
    # 更新界面显示
    Bloret_PassPort_User_UserName = homeInterface.findChild(QLabel, "Bloret_PassPort_UserName")
    Bloret_PassPort_User_UserName.setText(i18nText("未登录"))
    InfoBar.success(
        title=i18nText('⏫ 已退出登录'),
        content="",
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=5000,
        parent=self
    )
    Bloret_PassPort_Name = homeInterface.findChild(QLabel, "Bloret_PassPort_Name")
    Bloret_PassPort_Name.setText(f"未登录")
    log(i18nText("已退出登录"))

importlog("BLORET_PASSPORT.PY")