from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication
# 以下导入的部分是 Bloret Launcher 所有 © 2026 Bloret Launcher All rights reserved. © 2026 Bloret All rights reserved.的模块，位于 modules 中
from modules.log import log
from modules.i18n import i18nText

def open_github_bloret_Launcher():
    QDesktopServices.openUrl(QUrl("https://github.com/BloretCrew/Bloret-Launcher"))
    log(i18nText("打开该项目的 Github 页面"))
def open_qq_link():
    QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/iGw0GwUCiI"))
    log(i18nText("打开 Bloret QQ 群页面"))
def open_BLC_qq_link():
    QDesktopServices.openUrl(QUrl("https://qm.qq.com/q/kEt8fb41wc"))
    log(i18nText("打开 BLC QQ 群页面"))
def open_BBBS_link():
    QDesktopServices.openUrl(QUrl("https://bbs.bloret.net/"))
    log(i18nText("打开 BBBS 页面"))
def open_PassPort_link():
    QDesktopServices.openUrl(QUrl("https://passport.bloret.net/"))
    log(i18nText("打开 Bloret PassPort 页面"))
def open_BIMG_WEB_link():
    QDesktopServices.openUrl(QUrl("https://img.bloret.net/"))
    log(i18nText("打开 百络图床 页面"))
def open_BBBS_Reg_link():
    QDesktopServices.openUrl(QUrl("https://passport.bloret.net/register"))
    log(i18nText("打开 Bloret PassPort 注册页面"))
def open_bloret_web():
    QDesktopServices.openUrl(QUrl("https://launcher.bloret.net/"))
    log(i18nText("打开 Bloret Launcher 网页"))
def open_github_bloret():
    QDesktopServices.openUrl(QUrl("https://github.com/BloretCrew"))
    log(i18nText("打开 Bloret Github 组织页面"))
def copy_skin_to_clipboard(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.player_skin)
    log(f"皮肤URL {self.player_skin} 已复制到剪贴板")
def copy_cape_to_clipboard(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.player_cape)
    log(f"披风URL {self.player_cape} 已复制到剪贴板")
def open_skin_url(self):
    QDesktopServices.openUrl(QUrl(self.player_skin))
    log(f"打开皮肤URL: {self.player_skin}")
def open_cape_url(self):
    QDesktopServices.openUrl(QUrl(self.player_cape))
    log(f"打开披风URL: {self.player_cape}")
def copy_uuid_to_clipboard(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.player_uuid)
    log(f"UUID {self.player_uuid} 已复制到剪贴板")
def copy_name_to_clipboard(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.player_name)
    log(f"名称 {self.player_name} 已复制到剪贴板")

def Bloret_PassPort_Account_login(backend=None):
    from modules.passport_oauth import PassportOAuthCoordinator
    import modules.config as cfg

    def complete(result, userinfo):
        config = cfg.read()
        config.update({
            "Bloret_PassPort_Login": True,
            "Bloret_PassPort_UserName": str(userinfo.get("username") or userinfo.get("name") or ""),
            "Bloret_PassPort_NickName": str(userinfo.get("nickname") or userinfo.get("name") or ""),
            "Bloret_PassPort_OAuth": {
                "access_token": result["access_token"], "refresh_token": result.get("refresh_token", ""),
                "expires_in": result.get("expires_in"), "token_type": result.get("token_type", "Bearer"),
                "obtained_at": int(__import__("time").time()),
            },
            "Bloret_PassPort_PassWord": "",
        })
        cfg.write(config)
        if backend is not None:
            backend.passportLoginStatusChanged.emit("success")

    coordinator = PassportOAuthCoordinator(on_complete=complete)
    if backend is not None:
        backend._passport_oauth = coordinator
    try:
        coordinator.begin()
        log(i18nText("打开 Bloret PassPort 登录页面"))
        return coordinator
    except Exception as error:
        log(i18nText("打开 Bloret PassPort 登录页面失败"))
        return None

def openLink(url):
    QDesktopServices.openUrl(QUrl(url))
    log(i18nText(f"打开链接: {url}"))