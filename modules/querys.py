from PyQt5.QtWidgets import QLineEdit, QLabel
import logging,requests,base64,json
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块，位于 modules 中
from modules.log import log
from modules.i18n import i18nText

def query_player_uuid(self, widget):
    player_name_edit = widget.findChild(QLineEdit, "name2uuid_player_uuid")
    uuid_result_label = widget.findChild(QLabel, "label_2")
    if player_name_edit and uuid_result_label:
        uuid_result_label.setText(i18nText("查询中，请稍等..."))
        player_name = player_name_edit.text()
        response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player_name}")
        if response.status_code == 200:
            player_data = response.json()
            self.player_uuid = player_data.get("id", i18nText("未找到UUID"))
            uuid_result_label.setText(self.player_uuid)
            log(f"查询玩家名称 {player_name} 的UUID: {self.player_uuid}")
        else:
            uuid_result_label.setText(i18nText("查询失败"))
            log(f"查询玩家名称 {player_name} 的UUID失败", logging.ERROR)
def query_player_skin(self, widget):
    skin_uuid_edit = widget.findChild(QLineEdit, "skin_uuid")
    skin_result_label = widget.findChild(QLabel, "search_skin")
    cape_result_label = widget.findChild(QLabel, "search_cape")
    if skin_uuid_edit and skin_result_label and cape_result_label:
        skin_result_label.setText(i18nText("查询中，请稍等..."))
        cape_result_label.setText(i18nText("查询中，请稍等..."))
        player_uuid = skin_uuid_edit.text()
        response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{player_uuid}")
        if response.status_code == 200:
            player_data = response.json()
            properties = player_data.get("properties", [])
            for prop in properties:
                if prop["name"] == "textures":
                    textures = json.loads(base64.b64decode(prop["value"]).decode("utf-8"))
                    self.player_skin = textures["textures"].get("SKIN", {}).get("url", i18nText("未找到皮肤"))
                    self.player_cape = textures["textures"].get("CAPE", {}).get("url", i18nText("未找到披风"))
                    skin_result_label.setText(self.player_skin[:12] + "..." if len(self.player_skin) > 12 else self.player_skin)
                    cape_result_label.setText(self.player_cape[:12] + "..." if len(self.player_cape) > 12 else self.player_cape)
                    log(f"查询玩家UUID {player_uuid} 的皮肤: {self.player_skin}")
                    log(f"查询玩家UUID {player_uuid} 的披风: {self.player_cape}")
                    break
        else:
            skin_result_label.setText(i18nText("查询失败"))
            cape_result_label.setText(i18nText("查询失败"))
            log(f"查询玩家UUID {player_uuid} 的皮肤和披风失败", logging.ERROR)
def query_player_name(self, widget):
    player_uuid_edit = widget.findChild(QLineEdit, "search_name_type")
    name_result_label = widget.findChild(QLabel, "search_name")
    if player_uuid_edit and name_result_label:
        name_result_label.setText(i18nText("查询中，请稍等..."))
        player_uuid = player_uuid_edit.text()
        response = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{player_uuid}")
        if response.status_code == 200:
            player_data = response.json()
            self.player_name = player_data.get("name", i18nText("未找到名称"))
            name_result_label.setText(self.player_name)
            log(f"查询UUID {player_uuid} 的名称: {self.player_name}")
        else:
            name_result_label.setText(i18nText("查询失败"))
            log(f"查询UUID {player_uuid} 的名称失败", logging.ERROR)

