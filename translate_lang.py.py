import json
import os
import time
from deep_translator import GoogleTranslator
from requests.exceptions import RequestException

# --- 配置区 ---
BASE_PATH = "lang/"
SOURCE_FILE = "zh-cn.json"
# 如果你有代理（如 Clash 默认 7890），取消下面两行的注释并填入：
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
# proxies = None

# 语言代码映射（Default.json 中的代码 -> Google Translator 支持的目标代码）
LANG_CODE_MAP = {
    "af-ZA": "af",       # Afrikaans
    "ar-SA": "ar",       # Arabic
    "ca-ES": "ca",       # Catalan
    "cs-CZ": "cs",       # Czech
    "da-DK": "da",       # Danish
    "de": "de",          # German
    "de-DE": "de",       # German (Germany)
    "el-GR": "el",       # Greek
    "en-CN": "en",       # English (China)
    "en-GB": "en",       # English (UK)
    "en-US": "en",       # English (US)
    "es-ES": "es",       # Spanish
    "fi-FI": "fi",       # Finnish
    "fr": "fr",          # French
    "fr-FR": "fr",       # French (France)
    "gt-ZH": "zh-CN",    # 梗体中文（使用中文翻译）
    "he-IL": "he",       # Hebrew
    "hu-HU": "hu",       # Hungarian
    "it-IT": "it",       # Italian
    "ja": "ja",          # Japanese
    "ja-JP": "ja",       # Japanese (Japan)
    "ko": "ko",          # Korean
    "ko-KR": "ko",       # Korean (South Korea)
    "nl-NL": "nl",       # Dutch
    "no-NO": "no",       # Norwegian
    "pl-PL": "pl",       # Polish
    "pt-BR": "pt",       # Portuguese (Brazil)
    "pt-PT": "pt",       # Portuguese (Portugal)
    "ro-RO": "ro",       # Romanian
    "ru-RU": "ru",       # Russian
    "sr-SP": "sr",       # Serbian
    "sv-SE": "sv",       # Swedish
    "tr-TR": "tr",       # Turkish
    "uk-UA": "uk",       # Ukrainian
    "vi-VN": "vi",       # Vietnamese
    "zh-cn": "zh-CN",    # 简体中文（源语言，跳过）
    "zh-TW": "zh-TW",    # 繁体中文
    "zh-wy": "zh-CN",    # 文言文（使用中文翻译）
}

# 要跳过的语言（源语言）
SKIP_LANGS = {"zh-cn"}

def get_translator(target_lang_code):
    """获取翻译器实例"""
    return GoogleTranslator(source='auto', target=target_lang_code, proxies=proxies)

def safe_translate(translator, text, retries=3, delay=2):
    """带重试机制的翻译函数"""
    if not isinstance(text, str) or not text.strip():
        return text

    for i in range(retries):
        try:
            # 加上一小段随机延迟，避免请求过快
            result = translator.translate(text)
            time.sleep(0.5)
            return result
        except Exception as e:
            if i < retries - 1:
                print(f"请求失败，正在尝试第 {i+2} 次重试... 错误: {e}")
                time.sleep(delay * (i + 1)) # 递增等待时间
            else:
                print(f"跳过翻译: '{text}' (重试耗尽)")
                return text

def translate_recursive(translator, data):
    """递归处理 JSON 结构"""
    if isinstance(data, dict):
        return {k: translate_recursive(translator, v) for k, v in data.items()}
    elif isinstance(data, list):
        return [translate_recursive(translator, i) for i in data]
    else:
        return safe_translate(translator, data)

def process_translation():
    # 读取 Default.json
    try:
        with open(os.path.join(BASE_PATH, "Default.json"), 'r', encoding='utf-8') as f:
            default_config = json.load(f)

        # 读取源文件
        with open(os.path.join(BASE_PATH, SOURCE_FILE), 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    # 遍历所有配置的语言
    langs = default_config.get("lang", {})
    total = len(langs)
    current = 0
    
    for lang_code, info in langs.items():
        current += 1
        
        # 跳过源语言
        if lang_code in SKIP_LANGS:
            print(f"\n[{current}/{total}] 跳过: {info['name']} ({lang_code}) - 源语言")
            continue
        
        # 获取对应的 Google Translator 目标代码
        target_code = LANG_CODE_MAP.get(lang_code)
        if not target_code:
            print(f"\n[{current}/{total}] 跳过: {info['name']} ({lang_code}) - 无对应的翻译代码")
            continue
            
        target_filename = info['file']
        print(f"\n[{current}/{total}] 正在处理: {info['name']} ({target_filename}) -> 目标代码: {target_code}")

        try:
            # 创建翻译器
            translator = get_translator(target_code)
            
            # 开始翻译
            translated_content = translate_recursive(translator, source_data)

            # 写入文件
            output_path = os.path.join(BASE_PATH, target_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(translated_content, f, ensure_ascii=False, indent=4)

            print(f"OK: 已生成 {target_filename}")
            
            # 每个语言之间多加一点延迟，避免请求过快
            time.sleep(1)
            
        except Exception as e:
            print(f"错误: 处理 {info['name']} 时出错: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("开始翻译所有语言...")
    print(f"源文件: {SOURCE_FILE}")
    print(f"代理设置: {proxies}")
    print("=" * 50)
    process_translation()
    print("\n" + "=" * 50)
    print("翻译完成！")
    print("=" * 50)