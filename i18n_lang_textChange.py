import re
import logging
import json


def contains_chinese(text):
    """检查字符串是否包含中文字符"""
    if not text:
        print("检查空字符串是否包含中文")
        return False
    
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    result = bool(chinese_pattern.search(text))
    print(f"检查字符串 '{text}' 是否包含中文: {result}")
    return result


def is_already_i18n_wrapped(match_text):
    """检查字符串是否已经被i18nText包装"""
    # 检查是否以i18nText(开头和)结尾
    stripped = match_text.strip()
    if stripped.startswith('i18nText(') and stripped.endswith(')'):
        # 进一步检查是否是完整的包装
        inner_content = stripped[9:-1]  # 去掉 'i18nText(' 和 ')'
        # 检查是否是有效的字符串格式
        if (inner_content.startswith('"') and inner_content.endswith('"')) or \
           (inner_content.startswith("'") and inner_content.endswith("'")):
            print(f"字符串 '{match_text}' 已经被i18nText包装")
            return True
    return False


def is_f_string(match_text, line_content):
    """检查字符串是否是f-string的一部分"""
    # 检查字符串前是否有'f'字符
    match_start = line_content.find(match_text)
    if match_start >= 1 and line_content[match_start-1].lower() == 'f':
        print(f"字符串 '{match_text}' 是f-string的一部分，跳过处理")
        return True
    return False


def is_comment(line_content):
    """检查是否是注释行"""
    stripped = line_content.strip()
    # 检查是否以#开头的注释
    if stripped.startswith('#'):
        print(f"检测到注释行: {line_content}")
        return True
    # 检查是否是多行注释的一部分
    if stripped.startswith('"""') or stripped.startswith("'''"):
        print(f"检测到多行注释: {line_content}")
        return True
    return False


def load_lang_file(lang_file_path):
    """加载语言文件"""
    try:
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载语言文件失败: {e}", logging.ERROR)
        return None


def save_lang_file(lang_data, lang_file_path):
    """保存语言文件"""
    try:
        with open(lang_file_path, 'w', encoding='utf-8') as f:
            json.dump(lang_data, f, ensure_ascii=False, indent=4)
        print(f"语言文件保存成功: {lang_file_path}", logging.INFO)
        return True
    except Exception as e:
        print(f"保存语言文件失败: {e}", logging.ERROR)
        return False


def add_chinese_to_lang_file(chinese_strings, lang_file_path):
    """将提取的中文字符串添加到语言文件中"""
    if not chinese_strings:
        print("没有中文字符串需要添加到语言文件", logging.INFO)
        return True
    
    # 加载现有的语言文件
    lang_data = load_lang_file(lang_file_path)
    if lang_data is None:
        return False
    
    # 确保texts部分存在
    if "texts" not in lang_data:
        lang_data["texts"] = {}
    
    added_count = 0
    for chinese_str in chinese_strings:
        # 如果字符串不在语言文件中，则添加
        if chinese_str not in lang_data["texts"]:
            # 使用字符串本身作为键
            lang_data["texts"][chinese_str] = chinese_str
            added_count += 1
            print(f"添加中文字符串到语言文件: {chinese_str}", logging.INFO)
    
    # 保存更新后的语言文件
    if added_count > 0:
        if save_lang_file(lang_data, lang_file_path):
            print(f"成功将 {added_count} 个新的中文字符串添加到语言文件", logging.INFO)
            return True
        else:
            return False
    else:
        print("没有新的中文字符串需要添加到语言文件", logging.INFO)
        return True


def add_i18n_to_file(file_path, lang_file_path):
    """在指定的Python文件中查找中文字符串并套上i18nText()函数"""
    print(f"开始处理文件: {file_path}", logging.INFO)
    
    try:
        # 读取文件内容
        print("正在读取文件内容", logging.INFO)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"文件读取完成，内容长度: {len(content)} 字符", logging.INFO)
        
        # 按行分割内容，便于检查f-string和注释
        lines = content.split('\n')
        modified_lines = []
        
        # 存储提取的中文字符串
        chinese_strings = []
        
        # 统计处理的字符串数量
        processed_count = 0
        already_wrapped_count = 0
        skipped_f_string_count = 0
        skipped_comment_count = 0
        
        # 处理每一行
        for line_num, line in enumerate(lines):
            # 检查是否是注释行
            if is_comment(line):
                skipped_comment_count += line.count('"') + line.count("'")
                modified_lines.append(line)
                continue
            
            # 使用正则表达式匹配字符串字面量
            # 匹配单引号和双引号包围的字符串
            string_pattern = re.compile(r'(["\'])(.*?)(\1)')
            
            def replace_chinese_strings(match):
                nonlocal processed_count, already_wrapped_count, skipped_f_string_count, chinese_strings
                
                quote = match.group(1)
                string_content = match.group(2)
                full_match = match.group(0)
                
                print(f"发现字符串: {full_match}")
                
                # 检查是否是f-string
                if is_f_string(full_match, line):
                    skipped_f_string_count += 1
                    return full_match
                
                # 检查是否已经被i18nText包装
                if is_already_i18n_wrapped(full_match):
                    already_wrapped_count += 1
                    return full_match
                
                # 如果字符串包含中文且不为空
                if contains_chinese(string_content):
                    processed_count += 1
                    chinese_strings.append(string_content)
                    wrapped_string = f'i18nText({quote}{string_content}{quote})'
                    print(f"包装中文字符串: {full_match} -> {wrapped_string}", logging.INFO)
                    return wrapped_string
                else:
                    # 如果不包含中文，返回原字符串
                    print(f"跳过非中文字符串: {full_match}")
                    return full_match
            
            # 替换行中的中文字符串
            modified_line = string_pattern.sub(replace_chinese_strings, line)
            modified_lines.append(modified_line)
        
        # 重新组合内容
        modified_content = '\n'.join(modified_lines)
        
        print(f"处理完成，共处理 {processed_count} 个中文字符串，{already_wrapped_count} 个已包装字符串，跳过 {skipped_f_string_count} 个f-string，跳过 {skipped_comment_count} 个注释中的字符串", logging.INFO)
        
        # 将提取的中文字符串添加到语言文件
        if chinese_strings:
            print(f"提取到 {len(chinese_strings)} 个中文字符串，准备添加到语言文件", logging.INFO)
            if not add_chinese_to_lang_file(chinese_strings, lang_file_path):
                print("添加中文字符串到语言文件失败", logging.ERROR)
                return False
        
        # 检查是否有变化
        if modified_content == content:
            print("文件内容无变化，无需写入", logging.INFO)
            print(f"文件 {file_path} 处理完成，未发现需要修改的中文字符串")
            return True
        
        # 将修改后的内容写回文件
        print("正在将修改后的内容写入文件", logging.INFO)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print("文件写入完成", logging.INFO)
            
        print(f"成功处理文件: {file_path}")
        print(f"  - 处理了 {processed_count} 个中文字符串")
        print(f"  - 跳过了 {already_wrapped_count} 个已包装的字符串")
        print(f"  - 跳过了 {skipped_f_string_count} 个f-string")
        print(f"  - 跳过了 {skipped_comment_count} 个注释中的字符串")
        print(f"  - 添加了 {len(chinese_strings)} 个中文字符串到语言文件")
        
        return True
        
    except FileNotFoundError:
        error_msg = f"文件未找到: {file_path}"
        print(error_msg, logging.ERROR)
        print(error_msg)
        return False
    except PermissionError:
        error_msg = f"权限不足，无法访问文件: {file_path}"
        print(error_msg, logging.ERROR)
        print(error_msg)
        return False
    except Exception as e:
        error_msg = f"处理文件时出错: {e}"
        print(error_msg, logging.ERROR)
        print(error_msg)
        return False


def main():
    print("i18n文本处理工具启动", logging.INFO)
    
    # 获取用户输入的文件路径
    file_path = input("Enter the file path: ")
    print(f"用户输入文件路径: {file_path}", logging.INFO)
    
    # 语言文件路径
    lang_file_path = "lang/zh-cn.json"
    
    # 处理文件中的中文字符串
    if add_i18n_to_file(file_path, lang_file_path):
        print("i18n文本处理工具执行完成", logging.INFO)
    else:
        print("i18n文本处理工具执行失败", logging.ERROR)


if __name__ == "__main__":
    while True:
        main()
    