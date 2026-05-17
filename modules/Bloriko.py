import requests
import json
import os
from modules.log import log
import threading
from PySide6.QtCore import QTimer, QObject, Signal as pyqtSignal, Slot as pyqtSlot, Qt
from PySide6.QtWidgets import QMessageBox
import logging
import hashlib
import time
import modules.config as cfg
import modules.globals as BLglobals

timeout = 600 # second

OAUTH_APP_ID = "BloretLauncher"
OAUTH_APP_SECRET = "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
AI_API_URL = f"{BLglobals.server_ip}:20000/v1/chat/completions"

class BlorikoSignals(QObject):
    """Bloriko 信号类"""
    responseReceived = pyqtSignal(str)  # 当接收到 AI 响应时发出
    errorOccurred = pyqtSignal(str)     # 当发生错误时发出
    
    def __init__(self):
        super().__init__()
        log("BlorikoSignals 信号类初始化完成", logging.DEBUG)

class UIUpdater(QObject):
    """用于跨线程更新UI的辅助类"""
    def __init__(self, answer_label, thinking_widget):
        super().__init__()
        self.answer_label = answer_label
        self.thinking_widget = thinking_widget

    @pyqtSlot(str)
    def update_ui(self, content):
        """在主线程中接收信号并更新UI"""
        log(f"UIUpdater: 收到信号，准备更新UI，内容长度: {len(content)}字符", logging.DEBUG)
        try:
            # 设置 Markdown 格式
            self.answer_label.setTextFormat(Qt.MarkdownText)
            # 设置文本内容
            self.answer_label.setText(content.replace('\n', '\n').replace('```', '```'))
            # 隐藏思考中动画
            self.thinking_widget.hide()
            log("UIUpdater: 已将 Bloriko 响应设置到界面控件", logging.INFO)
        except Exception as e:
            log(f"UIUpdater: 更新UI时发生错误: {str(e)}", logging.ERROR)


def _build_auth_header(user_token):
    """构建 OpenAI 兼容的 Bearer Token 认证头"""
    return f"Bearer {OAUTH_APP_ID};{OAUTH_APP_SECRET};{user_token}"


def _parse_ai_response(result):
    """解析 OpenAI 兼容格式的非流式 AI 响应
    
    Args:
        result (dict): 解析后的 JSON 响应
        
    Returns:
        str: AI 回复内容
    """
    try:
        choices = result.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if content:
                return content
        return "未能获取到 AI 回复内容"
    except Exception as e:
        log(f"解析AI响应时出错: {str(e)}", logging.ERROR)
        return "解析 AI 响应失败"


def _parse_stream_response(response, on_chunk=None):
    """解析 OpenAI 兼容格式的流式 SSE 响应
    
    Args:
        response: requests 响应对象 (stream=True)
        on_chunk: 可选回调，每次收到新内容时调用，参数为当前累计内容
        
    Returns:
        str: AI 完整回复内容
    """
    collected = []
    buffer = ""
    
    # 使用 iter_content 代替 iter_lines，手动按行分割
    for chunk_bytes in response.iter_content(chunk_size=None):
        if not chunk_bytes:
            continue
        text = chunk_bytes.decode("utf-8", errors="replace")
        buffer += text
        
        # 按换行符分割，逐行处理
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            
            log(f"SSE行: {repr(line[:300])}", logging.DEBUG)
            
            if line.startswith("data: "):
                data_str = line[len("data: "):]
                if data_str.strip() == "[DONE]":
                    log("流式响应收到 [DONE] 标记", logging.DEBUG)
                    return "".join(collected) if collected else "未能获取到 AI 回复内容"
                try:
                    chunk_obj = json.loads(data_str)
                    choices = chunk_obj.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if not content:
                            message = choices[0].get("message", {})
                            content = message.get("content", "")
                        if content:
                            collected.append(content)
                            full = "".join(collected)
                            if on_chunk:
                                on_chunk(full)
                except json.JSONDecodeError:
                    log(f"流式响应JSON解析失败: {data_str[:200]}", logging.WARNING)
            else:
                # 可能是整个 JSON 响应（非SSE格式）
                try:
                    chunk_obj = json.loads(line)
                    choices = chunk_obj.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        content = msg.get("content", "")
                        if content:
                            log("检测到非流式JSON响应，直接提取content", logging.INFO)
                            return content
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            collected.append(content)
                            full = "".join(collected)
                            if on_chunk:
                                on_chunk(full)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
    
    # 处理 buffer 中剩余的数据
    if buffer.strip():
        line = buffer.strip()
        log(f"SSE行(尾): {repr(line[:300])}", logging.DEBUG)
        if line.startswith("data: "):
            data_str = line[len("data: "):]
            if data_str.strip() != "[DONE]":
                try:
                    chunk_obj = json.loads(data_str)
                    choices = chunk_obj.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            collected.append(content)
                except json.JSONDecodeError:
                    pass
    
    result = "".join(collected)
    if not result:
        return "未能获取到 AI 回复内容"
    return result


def _parse_stream_response_text(text, on_chunk=None):
    """从完整的 SSE 文本中解析响应
    
    Args:
        text (str): 完整的 SSE 响应文本
        on_chunk: 可选回调
        
    Returns:
        str: AI 回复内容
    """
    collected = []
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        log(f"SSE行(text): {repr(line[:300])}", logging.DEBUG)
        if line.startswith("data: "):
            data_str = line[len("data: "):]
            if data_str.strip() == "[DONE]":
                log("流式响应收到 [DONE] 标记", logging.DEBUG)
                break
            try:
                chunk_obj = json.loads(data_str)
                choices = chunk_obj.get("choices", [])
                if choices:
                    # 先尝试 delta 格式（标准 OpenAI 流式）
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    # 再尝试 message 格式（Bloret 服务端）
                    if not content:
                        message = choices[0].get("message", {})
                        content = message.get("content", "")
                    if content:
                        collected.append(content)
                        full = "".join(collected)
                        if on_chunk:
                            on_chunk(full)
            except json.JSONDecodeError:
                log(f"SSE文本JSON解析失败: {data_str[:200]}", logging.WARNING)
        else:
            try:
                chunk_obj = json.loads(line)
                choices = chunk_obj.get("choices", [])
                if choices:
                    # 先尝试 message 格式
                    msg = choices[0].get("message", {})
                    content = msg.get("content", "")
                    if content:
                        log("检测到非流式JSON响应，直接提取content", logging.INFO)
                        return content
                    # 再尝试 delta 格式
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        collected.append(content)
                        full = "".join(collected)
                        if on_chunk:
                            on_chunk(full)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
    result = "".join(collected)
    if not result:
        return "未能获取到 AI 回复内容"
    return result


def AskBloriko(question, config, deepthink=False):
    """
    向Bloriko发送问题并获取回答（流式）
    
    Args:
        question (str): 用户的问题
        config (dict): 配置信息
        deepthink (bool): 保留参数，当前未使用
        
    Returns:
        str: AI的回复内容
    """
    log(f"开始处理AI请求，问题长度: {len(question)}字符", logging.INFO)
    
    user_token = config.get("Bloret_PassPort_PassWord", "")
    
    log(f"token状态: {'已设置' if user_token else '未设置'} (长度: {len(user_token) if user_token else 0})", logging.DEBUG)
    
    if not user_token:
        log("用户token为空", logging.ERROR)
        return "用户token为空"
    
    def make_request():
        headers = {
            "Content-Type": "application/json",
            "Authorization": _build_auth_header(user_token)
        }
        
        payload = {
            "model": "Bloriko",
            "messages": [
                {"role": "user", "content": question}
            ],
            "stream": True
        }
        
        log(f"准备发送AI请求到: {AI_API_URL}", logging.INFO)
        log(f"请求headers: Authorization=Bearer ****;{user_token[:8]}...", logging.DEBUG)
        log(f"请求payload: {payload}", logging.DEBUG)
        
        try:
            log("开始发送POST请求(流式)...", logging.DEBUG)
            response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=timeout, stream=True)
            log(f"收到响应，状态码: {response.status_code}", logging.INFO)
            
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            log(f"响应Content-Type: {content_type}", logging.INFO)
            if "application/json" in content_type:
                result = response.json()
                log(f"JSON响应内容: {result}", logging.DEBUG)
                if "error" in result:
                    error_msg = result["error"].get("message", "未知错误")
                    error_type = result["error"].get("type", "unknown")
                    log(f"AI响应返回错误: [{error_type}] {error_msg}", logging.ERROR)
                    if error_type == "authentication_error" or "认证" in error_msg or "认证失败" in error_msg:
                        return "Bloret PassPort 认证失败，请重新登录"
                    return f"请求失败: {error_msg}"
                return _parse_ai_response(result)
            
            log("进入流式SSE解析...", logging.INFO)
            
            # 诊断：打印响应头和原始内容
            log(f"响应头: {dict(response.headers)}", logging.DEBUG)
            raw_bytes = response.content
            log(f"响应原始字节数: {len(raw_bytes)}", logging.INFO)
            raw_text = raw_bytes.decode("utf-8", errors="replace")
            log(f"响应原始文本(前500字符): {repr(raw_text[:500])}", logging.INFO)
            
            # 如果有内容，直接解析
            if raw_text.strip():
                return _parse_stream_response_text(raw_text, on_chunk=None)
            
            return _parse_stream_response(response)
                
        except requests.exceptions.HTTPError as e:
            log(f"HTTP错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            log(f"HTTP状态码: {e.response.status_code if e.response else '未知'}", logging.ERROR)
            log(f"HTTP响应内容: {e.response.text if e.response else '无响应内容'}", logging.ERROR)
            if e.response and e.response.status_code == 401:
                return "Bloret PassPort 认证失败，请重新登录"
            return f"请求失败: {str(e)}"
        except requests.exceptions.RequestException as e:
            log(f"请求异常: {type(e).__name__}: {str(e)}", logging.ERROR)
            return f"请求失败: {str(e)}"
        except json.JSONDecodeError as e:
            log(f"JSON解析失败: {str(e)}", logging.ERROR)
            return "服务器响应不是有效的 JSON 格式"
        except Exception as e:
            log(f"处理响应时发生未知错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            return f"未知错误: {str(e)}"
    
    # 在新线程中执行请求
    result = [None]
    
    def run_in_thread():
        try:
            log("在新线程中开始执行AI请求", logging.DEBUG)
            result[0] = make_request()
            log(f"线程执行完成，结果长度: {len(result[0]) if result[0] else 0}字符", logging.DEBUG)
        except Exception as e:
            log(f"线程执行错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            result[0] = f"线程执行错误: {str(e)}"
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        log(f"AI请求超时({timeout}秒)，线程仍在运行", logging.ERROR)
        return "请求超时，请稍后重试"
    
    final_result = result[0]
    log(f"AI请求处理完成，最终返回内容长度: {len(final_result) if final_result else 0}字符", logging.INFO)
    return final_result


def BuildModRecommendationQuestion(user_query, mc_version):
    """
    构建针对模组推荐的 AI 问题
    
    Args:
        user_query (str): 用户的需求描述
        mc_version (str): Minecraft 版本号
        
    Returns:
        str: 完整的推荐问题
    """
    prompt = f"""我需要为 Minecraft {mc_version} 推荐一些模组。

用户的需求是：{user_query}

请根据以下要求给出推荐：
1. 所有推荐的模组必须支持 Minecraft {mc_version} 和 Fabric 加载器
2. 提供模组的 Modrinth 项目名称（英文名，用于搜索）
3. 简短说明每个模组的功能
4. 按照重要性或依赖关系排序推荐

格式示例：
- **模组名称** (Modrinth ID: xxx)：功能说明

请确保推荐的模组在 Modrinth 上都能找到，并且支持指定的版本和加载器。"""
    return prompt


def AskBlorikoAndSet(self, question, AskBloriko_Answer, BlorikoThinking, parent, deepthink=False):
    """
    向Bloriko发送问题并获取回答（流式），直接设置到UI控件
    
    Args:
        question (str): 用户的问题
        AskBloriko_Answer: 用于显示答案的UI控件
        parent: 父窗口对象
        
    Returns:
        str: AI的回复内容
    """
    AskBloriko_Answer.setText("让络可好好想想...")
    BlorikoThinking.show()
    log(f"开始AskBlorikoAndSet函数，问题长度: {len(question)}字符", logging.INFO)
    
    # 读取配置文件
    try:
        log("开始读取配置文件 config.json", logging.DEBUG)
        config = cfg.read()
        log("成功读取配置文件 config.json", logging.DEBUG)
    except FileNotFoundError:
        log("配置文件 config.json 未找到", logging.ERROR)
        return ""
    except json.JSONDecodeError as e:
        log(f"配置文件 config.json 格式错误: {str(e)}", logging.ERROR)
        return ""

    def show_login_message():
        log("显示登录提示消息框", logging.INFO)
        msg = QMessageBox()
        msg.setWindowTitle("Bloriko 还不知道您是谁")
        msg.setText("Bloriko AI 需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。\n请先登录，确认以转到通行证页面。")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msg.exec() == QMessageBox.Ok:
            log("用户点击确认，应切换到通行证界面", logging.INFO)

    if not config.get("Bloret_PassPort_Login", False):
        log("用户未登录Bloret PassPort，显示登录提示", logging.WARNING)
        QTimer.singleShot(0, show_login_message)
        return "未登录"

    user_token = config.get("Bloret_PassPort_PassWord", "")
    
    log(f"用户token: {'已设置' if user_token else '未设置'} (长度: {len(user_token) if user_token else 0})", logging.DEBUG)
    
    if not user_token:
        log("用户token为空，无法使用 Bloriko 功能", logging.ERROR)
        return "用户名为空"

    # 初始化信号和UI更新器，并绑定到控件上防止被垃圾回收
    signals = BlorikoSignals()
    ui_updater = UIUpdater(AskBloriko_Answer, BlorikoThinking)
    signals.responseReceived.connect(ui_updater.update_ui)
    
    # 临时存储引用，防止被回收
    AskBloriko_Answer._bloriko_signals = signals
    AskBloriko_Answer._bloriko_updater = ui_updater

    def make_request():
        log(f"准备发送请求到 Bloriko AI 服务，URL: {AI_API_URL}", logging.INFO)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": _build_auth_header(user_token)
        }
        
        payload = {
            "model": "Bloriko",
            "messages": [
                {"role": "user", "content": question}
            ],
            "stream": True
        }
        log(f"请求体数据: {payload}", logging.DEBUG)
        
        result_content = ""
        
        try:
            log("正在发送 POST 请求到 Bloriko AI 服务(流式)", logging.INFO)
            response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=timeout, stream=True)
            log(f"收到响应，状态码: {response.status_code}", logging.INFO)
            
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "")
            log(f"响应Content-Type: {content_type}", logging.INFO)
            if "application/json" in content_type:
                result = response.json()
                log(f"JSON响应内容: {result}", logging.DEBUG)
                if "error" in result:
                    error_msg = result["error"].get("message", "未知错误")
                    error_type = result["error"].get("type", "unknown")
                    log(f"AI响应返回错误: [{error_type}] {error_msg}", logging.ERROR)
                    if error_type == "authentication_error" or "认证" in error_msg:
                        result_content = "Bloret PassPort 认证失败，请重新登录"
                    else:
                        result_content = f"AI服务错误: {error_msg}"
                else:
                    result_content = _parse_ai_response(result)
                    log(f"获取到AI回复内容，长度: {len(result_content)}字符", logging.INFO)
            else:
                def on_stream_chunk(partial_content):
                    signals.responseReceived.emit(partial_content)
                
                log("进入流式SSE解析...", logging.INFO)
                # 诊断：打印响应头和原始内容
                log(f"响应头: {dict(response.headers)}", logging.DEBUG)
                raw_bytes = response.content
                log(f"响应原始字节数: {len(raw_bytes)}", logging.INFO)
                raw_text = raw_bytes.decode("utf-8", errors="replace")
                log(f"响应原始文本(前500字符): {repr(raw_text[:500])}", logging.INFO)
                
                if raw_text.strip():
                    result_content = _parse_stream_response_text(raw_text, on_chunk=on_stream_chunk)
                else:
                    result_content = _parse_stream_response(response, on_chunk=on_stream_chunk)
                log(f"流式响应完成，内容长度: {len(result_content)}字符", logging.INFO)
                    
        except requests.exceptions.HTTPError as e:
            result_content = f"请求失败: {str(e)}"
            log(f"HTTP错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            if e.response:
                log(f"HTTP状态码: {e.response.status_code}", logging.ERROR)
                log(f"HTTP响应内容: {e.response.text}", logging.ERROR)
                if e.response.status_code == 401:
                    result_content = "Bloret PassPort 认证失败，请重新登录"
        except requests.exceptions.RequestException as e:
            result_content = f"请求失败: {str(e)}"
            log(f"请求 Bloriko AI 服务失败: {type(e).__name__}: {str(e)}", logging.ERROR)
        except json.JSONDecodeError as e:
            result_content = "服务器响应不是有效的 JSON 格式"
            log(f"JSON解析失败: {str(e)}", logging.ERROR)
        except Exception as e:
            result_content = f"未知错误: {str(e)}"
            log(f"处理 Bloriko 响应时发生未知错误: {type(e).__name__}: {str(e)}", logging.ERROR)
        
        # 最终发送完整结果到主线程更新UI
        log(f"发送信号通知UI更新，内容长度: {len(result_content)}", logging.DEBUG)
        signals.responseReceived.emit(result_content)
        return result_content
    
    # 在单独线程中执行网络请求
    log("创建线程以异步执行请求", logging.INFO)
    thread = threading.Thread(target=make_request)
    thread.daemon = True  # 设置为守护线程
    thread.start()
    log(f"线程已启动，线程ID: {thread.ident}", logging.INFO)
    return "请求已在后台执行"
