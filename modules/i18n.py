import json
import os
from modules.log import log
from PyQt5.QtWidgets import QLabel, QPushButton, QCheckBox, QRadioButton, QComboBox, QTextEdit, QLineEdit, QSpinBox
from qfluentwidgets import ComboBox, SwitchButton, TextEdit


def load_language():
    # 读取配置文件获取语言设置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            language = config.get('language', 'zh-cn')  # 默认使用中文
    except FileNotFoundError:
        language = 'zh-cn'  # 如果配置文件不存在，默认使用中文
    except json.JSONDecodeError:
        language = 'zh-cn'  # 如果配置文件格式错误，默认使用中文

    # 加载对应的语言文件
    lang_file_path = f'lang/{language}.json'
    try:
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            lang = json.load(f)
    except FileNotFoundError:
        # 如果指定的语言文件不存在，尝试加载默认的中文文件
        try:
            with open('lang/zh-cn.json', 'r', encoding='utf-8') as f:
                lang = json.load(f)
        except FileNotFoundError:
            lang = {}  # 如果连默认语言文件都不存在，则使用空字典
    except json.JSONDecodeError:
        lang = {}  # 如果语言文件格式错误，则使用空字典

    return lang


# 全局变量存储语言数据
lang_data = load_language()


def i18n(key):
    # 根据键路径查找翻译文本
    keys = key.split('.')
    value = lang_data
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return key  # 如果找不到对应键，则返回键本身


def i18n_label_text(widget, label_name):
    log(f"i18n_label_text: {label_name}")
    label = widget.findChild(QLabel, label_name)
    if label:
        label.setText(i18n(label_name))
    
    return False


def i18n_label_widget_label(widget, widget_name):
    """
    按照语言文件内容，翻译整个 widget
    从 lang_data 中获取 widget_name 对应的翻译内容，并应用到 widget 的子控件上
    """
    # 构造查找路径
    widget_path = f"widgets.{widget_name}"
    
    # 获取 widget 对应的翻译数据
    keys = widget_path.split('.')
    trans_data = lang_data
    try:
        for k in keys:
            trans_data = trans_data[k]
    except (KeyError, TypeError):
        log(f"No translation data found for widget: {widget_name}")
        return False
    
    # 遍历翻译数据中的各个控件类型
    for control_type, controls in trans_data.items():
        if control_type == "Labels":
            # 处理 QLabel 控件
            for label_name, translation_key in controls.items():
                label = widget.findChild(QLabel, label_name)
                if label and isinstance(translation_key, str):
                    label.setText(i18n(f"{widget_path}.{control_type}.{label_name}"))
                    
        elif control_type == "buttons":
            # 处理 QPushButton 控件
            for button_name, translation_key in controls.items():
                button = widget.findChild(QPushButton, button_name)
                if button and isinstance(translation_key, str):
                    button.setText(i18n(f"{widget_path}.{control_type}.{button_name}"))
                    
        elif control_type == "ComboBox":
            # 处理 QComboBox 控件
            for combobox_name, translation_key in controls.items():
                combobox = widget.findChild(QComboBox, combobox_name)
                if combobox and isinstance(translation_key, list):
                    # 清空现有项目
                    combobox.clear()
                    # 添加翻译后的项目
                    translated_items = [i18n(f"{widget_path}.{control_type}.{combobox_name}.{i}") 
                                      if isinstance(i18n(f"{widget_path}.{control_type}.{combobox_name}.{i}"), str)
                                      else item 
                                      for i, item in enumerate(translation_key)]
                    combobox.addItems(translated_items)
                    
        elif control_type == "SwitchButton":
            # 处理 SwitchButton 控件
            for switch_name, switch_data in controls.items():
                switch = widget.findChild(SwitchButton, switch_name)
                if switch and isinstance(switch_data, dict):
                    if 'onText' in switch_data:
                        switch.onText = i18n(f"{widget_path}.{control_type}.{switch_name}.onText")
                    if 'offText' in switch_data:
                        switch.offText = i18n(f"{widget_path}.{control_type}.{switch_name}.offText")
                        
        elif control_type == "SpinBox":
            # 处理 QSpinBox 控件
            for spinbox_name, suffix in controls.items():
                spinbox = widget.findChild(QSpinBox, spinbox_name)
                if spinbox and isinstance(suffix, str):
                    spinbox.setSuffix(i18n(f"{widget_path}.{control_type}.{spinbox_name}"))
                    
        elif control_type == "LineEdit":
            # 处理 QLineEdit 控件
            for lineedit_name, placeholder in controls.items():
                lineedit = widget.findChild(QLineEdit, lineedit_name)
                if lineedit and isinstance(placeholder, str):
                    lineedit.setPlaceholderText(i18n(f"{widget_path}.{control_type}.{lineedit_name}"))
                    
        elif control_type == "SearchLineEdit":
            # 处理 SearchLineEdit 控件
            for lineedit_name, placeholder in controls.items():
                lineedit = widget.findChild(QLineEdit, lineedit_name)
                if lineedit and isinstance(placeholder, str):
                    lineedit.setPlaceholderText(i18n(f"{widget_path}.{control_type}.{lineedit_name}"))
                    
        elif control_type == "PlainTextEdit":
            # 处理 QPlainTextEdit 控件
            for plain_text_edit_name, placeholder in controls.items():
                plain_text_edit = widget.findChild(QTextEdit, plain_text_edit_name)
                if plain_text_edit and isinstance(placeholder, str):
                    plain_text_edit.setPlaceholderText(i18n(f"{widget_path}.{control_type}.{plain_text_edit_name}"))
                    
        elif control_type == "TextEdit":
            # 处理 TextEdit 控件
            for text_edit_name, placeholder in controls.items():
                text_edit = widget.findChild(TextEdit, text_edit_name)
                if text_edit and isinstance(placeholder, str):
                    text_edit.setPlaceholderText(i18n(f"{widget_path}.{control_type}.{text_edit_name}"))
                    
        elif control_type == "CheckBox":
            # 处理 QCheckBox 控件
            for checkbox_name, translation_key in controls.items():
                checkbox = widget.findChild(QCheckBox, checkbox_name)
                if checkbox and isinstance(translation_key, str):
                    checkbox.setText(i18n(f"{widget_path}.{control_type}.{checkbox_name}"))
                    
        elif control_type == "RadioButton":
            # 处理 QRadioButton 控件
            for radiobutton_name, translation_key in controls.items():
                radiobutton = widget.findChild(QRadioButton, radiobutton_name)
                if radiobutton and isinstance(translation_key, str):
                    radiobutton.setText(i18n(f"{widget_path}.{control_type}.{radiobutton_name}"))
                    
        elif isinstance(controls, str):
            # 处理直接的标题或文本字段（如 TitleLabel, SubtitleLabel 等）
            label = widget.findChild(QLabel, control_type)
            if label:
                label.setText(i18n(f"{widget_path}.{control_type}"))
                
        elif isinstance(controls, dict):
            # 处理嵌套结构，如 SubtitleLabel 等
            for sub_label, translation_key in controls.items():
                label = widget.findChild(QLabel, sub_label)
                if label and isinstance(translation_key, str):
                    label.setText(i18n(f"{widget_path}.{control_type}.{sub_label}"))

def i18n_widgets(self):
    i18n_label_widget_label(self.homeInterface, "home")
    i18n_label_widget_label(self.multiplayerInterface, "client")
    i18n_label_widget_label(self.downloadInterface, "download")
    i18n_label_widget_label(self.toolsInterface, "tools")
    i18n_label_widget_label(self.versionInterface, "version")
    i18n_label_widget_label(self.BBSInterface, "bbs")
    i18n_label_widget_label(self.modInterface, "mods")
    i18n_label_widget_label(self.passportInterface, "passport")
    i18n_label_widget_label(self.settingsInterface, "settings")
    i18n_label_widget_label(self.infoInterface, "info")
    
    return True

def i18nText(key):
    """
    根据键值从语言数据中获取对应的国际化文本
    
    Args:
        key: 用于查找对应文本的键值，可以是字符串或列表
        
    Returns:
        对应的国际化文本字符串，如果找不到则返回原始键值
    """
    # 处理键值可能是包含单个字符串元素的列表的情况
    if isinstance(key, list):
        # 如果列表只包含一个字符串元素，则使用该字符串作为键值
        if len(key) == 1 and isinstance(key[0], str):
            key = key[0]
        else:
            # 如果列表包含多个元素或元素不是字符串，则直接返回原列表
            return key  
    
    # 原始功能：从语言数据中获取对应文本
    try:
        # 尝试从语言数据中获取对应键值的文本
        return lang_data["texts"][key]
    except KeyError:
        # 如果在语言数据中找不到对应键值，则返回原始键值
        # log(f"[i18n][i18nText] 发现未翻译的值: {key}")
        return key