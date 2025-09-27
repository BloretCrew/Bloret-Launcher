import re
import ast
import sys
import logging
import json
import os
from datetime import datetime

# 尝试导入项目中的log函数
try:
    from modules.log import log
    use_project_log = True
except ImportError:
    # 如果无法导入，则使用标准logging模块
    def log(message, level=logging.INFO):
        print(message)
    use_project_log = False


def contains_chinese(text):
    """检查字符串是否包含中文字符"""
    if not text:
        log("检查空字符串是否包含中文", logging.DEBUG)
        return False
    
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
    result = bool(chinese_pattern.search(text))
    log(f"检查字符串 '{text}' 是否包含中文: {result}", logging.DEBUG)
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
            log(f"字符串 '{match_text}' 已经被i18nText包装", logging.DEBUG)
            return True
    return False


def is_f_string(match_text, line_content):
    """检查字符串是否是f-string的一部分"""
    # 检查字符串前是否有'f'字符
    match_start = line_content.find(match_text)
    if match_start >= 1 and line_content[match_start-1].lower() == 'f':
        log(f"字符串 '{match_text}' 是f-string的一部分，跳过处理", logging.DEBUG)
        return True
    return False


def is_comment(line_content):
    """检查是否是注释行"""
    stripped = line_content.strip()
    # 检查是否以#开头的注释
    if stripped.startswith('#'):
        log(f"检测到注释行: {line_content}", logging.DEBUG)
        return True
    # 检查是否是多行注释的一部分
    if stripped.startswith('"""') or stripped.startswith("'''"):
        log(f"检测到多行注释: {line_content}", logging.DEBUG)
        return True
    return False


def load_lang_file(lang_file_path):
    """加载语言文件"""
    try:
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"加载语言文件失败: {e}", logging.ERROR)
        return None


def save_lang_file(lang_data, lang_file_path):
    """保存语言文件"""
    try:
        with open(lang_file_path, 'w', encoding='utf-8') as f:
            json.dump(lang_data, f, ensure_ascii=False, indent=4)
        log(f"语言文件保存成功: {lang_file_path}", logging.INFO)
        return True
    except Exception as e:
        log(f"保存语言文件失败: {e}", logging.ERROR)
        return False


def add_chinese_to_lang_file(chinese_strings, lang_file_path):
    """将提取的中文字符串添加到语言文件中"""
    if not chinese_strings:
        log("没有中文字符串需要添加到语言文件", logging.INFO)
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
            log(f"添加中文字符串到语言文件: {chinese_str}", logging.INFO)
    
    # 保存更新后的语言文件
    if added_count > 0:
        if save_lang_file(lang_data, lang_file_path):
            log(f"成功将 {added_count} 个新的中文字符串添加到语言文件", logging.INFO)
            return True
        else:
            return False
    else:
        log("没有新的中文字符串需要添加到语言文件", logging.INFO)
        return True


def process_python_file(file_path, lang_file_path):
    """处理单个Python文件"""
    log(f"开始处理文件: {file_path}", logging.INFO)
    
    try:
        # 读取文件内容
        log("正在读取文件内容", logging.INFO)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        log(f"文件读取完成，内容长度: {len(content)} 字符", logging.INFO)
        
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
                
                log(f"发现字符串: {full_match}", logging.DEBUG)
                
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
                    log(f"包装中文字符串: {full_match} -> {wrapped_string}", logging.INFO)
                    return wrapped_string
                else:
                    # 如果不包含中文，返回原字符串
                    log(f"跳过非中文字符串: {full_match}", logging.DEBUG)
                    return full_match
            
            # 替换行中的中文字符串
            modified_line = string_pattern.sub(replace_chinese_strings, line)
            modified_lines.append(modified_line)
        
        # 重新组合内容
        modified_content = '\n'.join(modified_lines)
        
        log(f"处理完成，共处理 {processed_count} 个中文字符串，{already_wrapped_count} 个已包装字符串，跳过 {skipped_f_string_count} 个f-string，跳过 {skipped_comment_count} 个注释中的字符串", logging.INFO)
        
        # 将提取的中文字符串添加到语言文件
        if chinese_strings:
            log(f"提取到 {len(chinese_strings)} 个中文字符串，准备添加到语言文件", logging.INFO)
            if not add_chinese_to_lang_file(chinese_strings, lang_file_path):
                log("添加中文字符串到语言文件失败", logging.ERROR)
                return False
        
        # 检查是否有变化
        if modified_content == content:
            log("文件内容无变化，无需写入", logging.INFO)
            log(f"文件 {file_path} 处理完成，未发现需要修改的中文字符串")
            return True
        
        # 将修改后的内容写回文件
        log("正在将修改后的内容写入文件", logging.INFO)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        log("文件写入完成", logging.INFO)
            
        log(f"成功处理文件: {file_path}")
        log(f"  - 处理了 {processed_count} 个中文字符串")
        log(f"  - 跳过了 {already_wrapped_count} 个已包装的字符串")
        log(f"  - 跳过了 {skipped_f_string_count} 个f-string")
        log(f"  - 跳过了 {skipped_comment_count} 个注释中的字符串")
        log(f"  - 添加了 {len(chinese_strings)} 个中文字符串到语言文件")
        
        return True
        
    except FileNotFoundError:
        error_msg = f"文件未找到: {file_path}"
        log(error_msg, logging.ERROR)
        log(error_msg)
        return False
    except PermissionError:
        error_msg = f"权限不足，无法访问文件: {file_path}"
        log(error_msg, logging.ERROR)
        log(error_msg)
        return False
    except Exception as e:
        error_msg = f"处理文件时出错: {e}"
        log(error_msg, logging.ERROR)
        log(error_msg)
        return False


def process_directory(dir_path, lang_file_path):
    """递归处理目录中的所有Python文件"""
    log(f"开始处理目录: {dir_path}", logging.INFO)
    
    processed_files = 0
    total_processed_count = 0
    total_already_wrapped_count = 0
    total_skipped_f_string_count = 0
    total_skipped_comment_count = 0
    total_chinese_strings_count = 0
    
    # 收集所有需要处理的Python文件
    python_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    log(f"找到 {len(python_files)} 个Python文件", logging.INFO)
    
    # 处理每个Python文件
    all_chinese_strings = []
    for file_path in python_files:
        log(f"正在处理文件: {file_path}", logging.INFO)
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按行分割内容
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
                string_pattern = re.compile(r'(["\'])(.*?)(\1)')
                
                def replace_chinese_strings(match):
                    nonlocal processed_count, already_wrapped_count, skipped_f_string_count, chinese_strings
                    
                    quote = match.group(1)
                    string_content = match.group(2)
                    full_match = match.group(0)
                    
                    log(f"发现字符串: {full_match}", logging.DEBUG)
                    
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
                        log(f"包装中文字符串: {full_match} -> {wrapped_string}", logging.INFO)
                        return wrapped_string
                    else:
                        # 如果不包含中文，返回原字符串
                        log(f"跳过非中文字符串: {full_match}", logging.DEBUG)
                        return full_match
                
                # 替换行中的中文字符串
                modified_line = string_pattern.sub(replace_chinese_strings, line)
                modified_lines.append(modified_line)
            
            # 更新总计数
            total_processed_count += processed_count
            total_already_wrapped_count += already_wrapped_count
            total_skipped_f_string_count += skipped_f_string_count
            total_skipped_comment_count += skipped_comment_count
            total_chinese_strings_count += len(chinese_strings)
            all_chinese_strings.extend(chinese_strings)
            
            # 重新组合内容
            modified_content = '\n'.join(modified_lines)
            
            # 检查是否有变化
            if modified_content != content:
                # 将修改后的内容写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                log(f"文件 {file_path} 处理完成", logging.INFO)
            else:
                log(f"文件 {file_path} 无变化，跳过写入", logging.INFO)
            
            processed_files += 1
            
        except Exception as e:
            log(f"处理文件 {file_path} 时出错: {e}", logging.ERROR)
    
    # 将所有提取的中文字符串添加到语言文件
    if all_chinese_strings:
        log(f"总共提取到 {len(all_chinese_strings)} 个中文字符串，准备添加到语言文件", logging.INFO)
        if not add_chinese_to_lang_file(all_chinese_strings, lang_file_path):
            log("添加中文字符串到语言文件失败", logging.ERROR)
            return False
    
    log(f"目录处理完成: {dir_path}", logging.INFO)
    log(f"  - 处理了 {processed_files} 个文件")
    log(f"  - 总共处理了 {total_processed_count} 个中文字符串")
    log(f"  - 跳过了 {total_already_wrapped_count} 个已包装的字符串")
    log(f"  - 跳过了 {total_skipped_f_string_count} 个f-string")
    log(f"  - 跳过了 {total_skipped_comment_count} 个注释中的字符串")
    log(f"  - 添加了 {len(all_chinese_strings)} 个中文字符串到语言文件")
    
    return True


def main():
    log("i18n文本处理工具启动", logging.INFO)
    
    # 询问用户要处理文件还是文件夹
    while True:
        process_type = input("请选择要处理的类型 (file/folder): ").strip().lower()
        if process_type in ['file', 'folder']:
            break
        log("输入无效，请输入 'file' 或 'folder'", logging.WARNING)
    
    # 获取用户输入的路径
    path = input("请输入路径: ").strip()
    log(f"用户选择处理类型: {process_type}, 路径: {path}", logging.INFO)
    
    # 语言文件路径
    lang_file_path = "lang/zh-cn.json"
    
    # 根据用户选择处理文件或文件夹
    if process_type == 'file':
        if os.path.isfile(path):
            if path.endswith('.py'):
                if process_python_file(path, lang_file_path):
                    log("i18n文本处理工具执行完成", logging.INFO)
                else:
                    log("i18n文本处理工具执行失败", logging.ERROR)
            else:
                log("指定的文件不是Python文件(.py)", logging.ERROR)
        else:
            log("指定的文件不存在", logging.ERROR)
    else:  # folder
        if os.path.isdir(path):
            if process_directory(path, lang_file_path):
                log("i18n文本处理工具执行完成", logging.INFO)
            else:
                log("i18n文本处理工具执行失败", logging.ERROR)
        else:
            log("指定的目录不存在", logging.ERROR)


if __name__ == "__main__":
    main()