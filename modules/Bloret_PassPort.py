from PyQt5.QtWidgets import QLabel
from qfluentwidgets import SubtitleLabel,MessageBoxBase,InfoBar,InfoBarPosition,Dialog, LineEdit
import logging,requests,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块
from modules.log import log
from modules.safe import handle_exception
from modules.i18n import i18nText



def Bloret_PassPort_Account_logout(self, homeInterface):
    self.config.update(Bloret_PassPort_UserName=i18nText('未登录'))
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