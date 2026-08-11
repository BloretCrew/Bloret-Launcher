import json
import os
from modules.log import log
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QComboBox,
    QTextEdit,
    QPlainTextEdit,
    QLineEdit,
    QSpinBox,
)
import modules.globals as BLglobals
from modules.compat_widgets import SearchLineEdit, SwitchButton
from modules.paths import app_path
from modules.live_i18n import cached_language_path


def _lang_file_path(language):
    """内置只读语言资源路径（兼容 PyInstaller / Nuitka）。"""
    return app_path("lang", f"{language}.json")


def _cached_lang_file_path(language):
    """AppData 中由实时译文 API 保存的可写语言缓存路径。"""
    return str(cached_language_path(language))


def _read_language_path(lang_file_path):
    """读取并校验单个语言文件。"""
    with open(lang_file_path, 'r', encoding='utf-8') as f:
        lang = json.load(f)
    if not isinstance(lang, dict) or not isinstance(lang.get('texts'), dict):
        raise ValueError(f"语言文件缺少 texts 字典: {lang_file_path}")
    for key, value in lang['texts'].items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"语言文件 texts 必须为字符串映射: {lang_file_path}")
    return lang


def _read_language_file(language):
    return _read_language_path(_lang_file_path(language))


def _deep_merge_nonempty(base: dict, overlay: dict) -> dict:
    """递归合并；远程空字符串不覆盖有效的本地译文。"""
    if not isinstance(base, dict):
        base = {}
    result = dict(base)
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_nonempty(result[key], value)
        elif isinstance(value, str) and value == "":
            # BTC 尚无译文时 top_voted 导出空串，保留内置目标语言/中文。
            continue
        else:
            result[key] = value
    return result


def _current_language_code(language=None):
    if language is None:
        try:
            with open(BLglobals.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                language = config.get('language') or config.get('Language') or 'zh-cn'
        except (OSError, json.JSONDecodeError) as error:
            log(f"读取语言配置失败，回退到 zh-cn: {error}")
            language = 'zh-cn'
    if not isinstance(language, str):
        language = 'zh-cn'
    return language.strip() or 'zh-cn'


def _deep_merge_dict(base: dict, overlay: dict) -> dict:
    """递归合并 overlay 到 base（overlay 优先）。"""
    if not isinstance(base, dict):
        base = {}
    result = dict(base)
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def merge_plugin_i18n(language=None, base_data=None):
    """
    将插件 contributes.i18n 合并进当前语言数据。
    插件 JSON 可为完整 lang 结构 {texts: {...}} 或仅 texts 字典。
    """
    global lang_data, _active_language
    target_lang = _current_language_code(language if language is not None else _active_language)
    if base_data is None:
        # 每次从启动器原始语言文件重新开始，避免禁用/卸载插件后旧翻译残留。
        base_data = load_language(target_lang)
    merged = dict(base_data)
    if "texts" not in merged or not isinstance(merged.get("texts"), dict):
        merged["texts"] = dict(merged.get("texts") or {})

    try:
        from modules.plugin_host.registry import get_registry

        entries = get_registry().get_i18n()
    except Exception as e:
        log(f"[i18n] 读取插件 i18n 失败: {e}")
        entries = []

    def _locale_matches(locale: str, target: str) -> bool:
        loc = (locale or "zh-cn").lower()
        tgt = (target or "zh-cn").lower()
        if loc in ("*", "default", "all"):
            return True
        if loc == tgt:
            return True
        # en 匹配 en-GB / en-US
        if "-" not in loc and tgt.startswith(loc + "-"):
            return True
        return False

    # 通配 < 语言前缀 < 精确区域（后写入覆盖）。
    def _locale_priority(entry: dict) -> int:
        loc = str(entry.get("locale") or "zh-cn").lower()
        tgt = target_lang.lower()
        if loc in ("*", "default", "all"):
            return 0
        if loc == tgt:
            return 2
        return 1

    ordered = sorted(entries, key=_locale_priority)
    applied = 0
    for entry in ordered:
        locale = str(entry.get("locale") or "zh-cn")
        if not _locale_matches(locale, target_lang):
            continue
        data = entry.get("data")
        if not isinstance(data, dict):
            continue
        # 完整语言文件 or 纯 texts
        if "texts" in data and isinstance(data["texts"], dict):
            overlay = data
        else:
            overlay = {"texts": data}
        merged = _deep_merge_dict(merged, overlay)
        applied += 1
        log(f"[i18n] 合并插件语言 plugin={entry.get('plugin_id')} locale={locale} keys={len(overlay.get('texts') or {})}")

    lang_data = merged
    _active_language = target_lang
    if applied:
        log(f"[i18n] 插件语言合并完成 language={target_lang} plugins={applied}")
    return lang_data


def load_language(language=None):
    """加载中文结构 + 内置目标语言 + AppData 实时缓存。

    任何缓存读取失败都不会影响内置语言；远程空串不会覆盖已有译文。
    """
    language = _current_language_code(language)

    try:
        base = _read_language_file('zh-cn')
    except (OSError, json.JSONDecodeError, ValueError) as error:
        log(f"默认语言 zh-cn 无法加载: path={_lang_file_path('zh-cn')}, error={error}")
        base = {"texts": {}}

    if language != 'zh-cn':
        try:
            bundled = _read_language_file(language)
            base = _deep_merge_nonempty(base, bundled)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            log(f"内置语言加载失败，使用中文结构: language={language}, path={_lang_file_path(language)}, error={error}")

    # zh-cn 是源语言，不使用 translated API 缓存；其它语言允许 AppData 覆盖。
    if language != 'zh-cn':
        cache_path = _cached_lang_file_path(language)
        try:
            cached = _read_language_path(cache_path)
            base = _deep_merge_nonempty(base, cached)
            log(f"[i18n] 已合并 AppData 实时语言缓存: language={language}, path={cache_path}")
        except FileNotFoundError:
            pass
        except (OSError, json.JSONDecodeError, ValueError) as error:
            log(f"[i18n] AppData 语言缓存不可用，保留内置内容: language={language}, path={cache_path}, error={error}")

    if not isinstance(base, dict) or not isinstance(base.get('texts'), dict):
        log("无可用语言文件，使用安全空翻译表")
        return {"texts": {}}
    return base

def reload_language(language=None):
    """手动重新加载语言数据，并合并插件 i18n。"""
    global lang_data, _active_language
    lang_data = load_language(language)
    _active_language = _current_language_code(language)
    try:
        merge_plugin_i18n(_active_language, lang_data)
    except Exception as e:
        log(f"[i18n] reload 合并插件语言失败: {e}")
    log(f"Language reloaded: {language if language else 'default'}")


# 全局变量存储语言数据
_active_language = _current_language_code(None)
lang_data = load_language(_active_language)


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
                plain_text_edit = widget.findChild(QPlainTextEdit, plain_text_edit_name)
                if plain_text_edit and isinstance(placeholder, str):
                    plain_text_edit.setPlaceholderText(i18n(f"{widget_path}.{control_type}.{plain_text_edit_name}"))
                    
        elif control_type == "TextEdit":
            # 处理 TextEdit 控件
            for text_edit_name, placeholder in controls.items():
                text_edit = widget.findChild(QTextEdit, text_edit_name)
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
    
    # 原始功能：从语言数据中获取对应文本（含插件合并后的 texts）
    try:
        texts = lang_data.get("texts") if isinstance(lang_data, dict) else None
        if isinstance(texts, dict) and key in texts:
            return texts[key]
        return lang_data["texts"][key]
    except (KeyError, TypeError):
        # 如果在语言数据中找不到对应键值，则返回原始键值
        # log(f"[i18n][i18nText] 发现未翻译的值: {key}")
        return key
