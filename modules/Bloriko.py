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
# 旧端点已废弃；实际请求走 resolve_global_ai_config()（Bloret PassPort / OpenCode Zen / 自定义供应商）
AI_API_URL_LEGACY = f"{BLglobals.server_ip}:20000/v1/chat/completions"

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
    """构建 OpenAI 兼容的 Bearer Token 认证头（旧路径兼容，优先使用 resolve_global_ai_config）"""
    return f"Bearer {OAUTH_APP_ID};{OAUTH_APP_SECRET};{user_token}"


def _resolve_ai_endpoint():
    """获取当前全局 AI 端点配置。

    Returns:
        tuple: (api_url, auth_header, model, error_message_or_None)
    """
    try:
        from modules.bloriko_agent import resolve_global_ai_config
        cfg_ai = resolve_global_ai_config()
        if cfg_ai.get("error"):
            return "", "", "", cfg_ai["error"]
        return (
            cfg_ai.get("api_url", ""),
            cfg_ai.get("auth_header", ""),
            cfg_ai.get("model", ""),
            None,
        )
    except Exception as e:
        log(f"解析全局 AI 配置失败: {e}", logging.ERROR)
        return "", "", "", f"解析 AI 配置失败: {e}"


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


def AskBloriko(question, config=None, deepthink=False):
    """
    向 Bloriko 发送问题并获取回答（流式）。

    使用全局 AI 供应商配置（与络可 Agent 一致）：
    Bloret PassPort / OpenCode Zen / 自定义供应商。

    Args:
        question (str): 用户的问题
        config (dict): 保留参数，兼容旧调用；认证已由全局配置解析
        deepthink (bool): 已废弃，忽略

    Returns:
        str: AI 的回复内容
    """
    log(f"开始处理 AI 请求，问题长度: {len(question)} 字符, deepthink(忽略)={deepthink}", logging.INFO)

    api_url, auth_header, model, config_error = _resolve_ai_endpoint()
    if config_error:
        log(f"AI 配置错误: {config_error}", logging.ERROR)
        return config_error

    log(
        f"AskBloriko 使用全局 AI: model={model}, api={api_url}, auth={'yes' if auth_header else 'no'}",
        logging.INFO,
    )

    def make_request():
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": question}
            ],
            "stream": True,
        }

        log(f"准备发送 AI 请求到: {api_url}", logging.INFO)
        if auth_header:
            masked = auth_header[:24] + "..." if len(auth_header) > 24 else "***"
            log(f"请求 Authorization(脱敏): {masked}", logging.DEBUG)
        log(f"请求 payload model={model}, messages_count=1", logging.DEBUG)

        try:
            log("开始发送 POST 请求(流式)...", logging.DEBUG)
            response = requests.post(api_url, json=payload, headers=headers, timeout=timeout, stream=True)
            log(f"收到响应，状态码: {response.status_code}", logging.INFO)

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            log(f"响应 Content-Type: {content_type}", logging.INFO)
            if "application/json" in content_type and "text/event-stream" not in content_type:
                result = response.json()
                log(f"JSON 响应内容: {result}", logging.DEBUG)
                if "error" in result:
                    err = result["error"]
                    if isinstance(err, dict):
                        error_msg = err.get("message", "未知错误")
                        error_type = err.get("type", "unknown")
                    else:
                        error_msg = str(err)
                        error_type = "unknown"
                    log(f"AI 响应返回错误: [{error_type}] {error_msg}", logging.ERROR)
                    if error_type == "authentication_error" or "认证" in error_msg or "认证失败" in error_msg:
                        return "Bloret PassPort 认证失败，请重新登录或检查 AI 配置"
                    return f"请求失败: {error_msg}"
                return _parse_ai_response(result)

            log("进入流式 SSE 解析...", logging.INFO)

            log(f"响应头: {dict(response.headers)}", logging.DEBUG)
            raw_bytes = response.content
            log(f"响应原始字节数: {len(raw_bytes)}", logging.INFO)
            raw_text = raw_bytes.decode("utf-8", errors="replace")
            log(f"响应原始文本(前500字符): {repr(raw_text[:500])}", logging.INFO)

            if raw_text.strip():
                return _parse_stream_response_text(raw_text, on_chunk=None)

            return _parse_stream_response(response)

        except requests.exceptions.HTTPError as e:
            log(f"HTTP 错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            log(f"HTTP 状态码: {e.response.status_code if e.response else '未知'}", logging.ERROR)
            log(f"HTTP 响应内容: {e.response.text if e.response else '无响应内容'}", logging.ERROR)
            if e.response and e.response.status_code == 401:
                return "AI 认证失败，请重新登录 Bloret PassPort 或检查 API 密钥"
            return f"请求失败: {str(e)}"
        except requests.exceptions.RequestException as e:
            log(f"请求异常: {type(e).__name__}: {str(e)}", logging.ERROR)
            return f"请求失败: {str(e)}"
        except json.JSONDecodeError as e:
            log(f"JSON 解析失败: {str(e)}", logging.ERROR)
            return "服务器响应不是有效的 JSON 格式"
        except Exception as e:
            log(f"处理响应时发生未知错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            return f"未知错误: {str(e)}"

    result = [None]

    def run_in_thread():
        try:
            log("在新线程中开始执行 AI 请求", logging.DEBUG)
            result[0] = make_request()
            log(f"线程执行完成，结果长度: {len(result[0]) if result[0] else 0} 字符", logging.DEBUG)
        except Exception as e:
            log(f"线程执行错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            result[0] = f"线程执行错误: {str(e)}"

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        log(f"AI 请求超时({timeout}秒)，线程仍在运行", logging.ERROR)
        return "请求超时，请稍后重试"

    final_result = result[0]
    log(f"AI 请求处理完成，最终返回内容长度: {len(final_result) if final_result else 0} 字符", logging.INFO)
    return final_result


def BuildModRecommendationQuestion(user_query, mc_version):
    """
    构建针对模组推荐的 AI 问题（强制返回 Modrinth slug JSON，供一键安装解析）。

    Args:
        user_query (str): 用户的需求描述
        mc_version (str): Minecraft 版本号

    Returns:
        str: 完整的推荐问题
    """
    prompt = (
        f"User is playing Minecraft version {mc_version} using the FABRIC loader.\n"
        f"User Request: {user_query}\n\n"
        f"Please recommend 3-8 suitable Modrinth mods that are compatible with FABRIC "
        f"and Minecraft {mc_version}. Briefly explain why each was chosen. "
        f"Use real Modrinth project slugs (URL path ids), not display names.\n\n"
        f"EXTREMELY IMPORTANT: At the very end of your response, you MUST provide a JSON block "
        f"containing ONLY a list of the Modrinth slugs (project IDs) for these mods.\n"
        f"Format strictly like this:\n```json\n[\"sodium\", \"lithium\", \"iris\"]\n```"
    )
    log(
        f"BuildModRecommendationQuestion: mc={mc_version}, query_len={len(user_query)}",
        logging.INFO,
    )
    return prompt


def parse_mod_slugs_from_response(response_text):
    """从 AI 回复中解析 Modrinth slug 列表，并返回去掉 JSON 块后的展示文本。

    Returns:
        tuple: (clean_text, slugs:list)
    """
    import re as _re

    if not response_text:
        return "", []

    slugs = []
    clean_text = response_text

    json_match = _re.search(r'```json\s*(\[.*?\])\s*```', response_text, _re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                slugs = [str(s).strip() for s in parsed if str(s).strip()]
                clean_text = response_text.replace(json_match.group(0), "").strip()
                log(f"从 JSON 块解析到 {len(slugs)} 个 slug: {slugs}", logging.INFO)
        except json.JSONDecodeError:
            log("Bloriko AI 返回的 JSON 格式错误", logging.ERROR)

    if not slugs:
        slug_fallback = _re.findall(r'modrinth\.com/(?:mod|project)/([a-zA-Z0-9_-]+)', response_text)
        if not slug_fallback:
            slug_fallback = _re.findall(r'`([a-zA-Z0-9_-]+)`', response_text)
        if slug_fallback:
            slugs = list(dict.fromkeys(slug_fallback))
            log(f"Fallback 提取 slugs: {slugs}", logging.INFO)
        else:
            log("未能从 AI 回复中解析到任何 slug", logging.WARNING)

    return clean_text, slugs


def AskBlorikoAndSet(self, question, AskBloriko_Answer, BlorikoThinking, parent, deepthink=False):
    """
    向 Bloriko 发送问题并获取回答，直接设置到 UI 控件。
    底层复用 AskBloriko（全局 AI 供应商配置）。
    deepthink 已废弃，忽略。
    """
    AskBloriko_Answer.setText("让络可好好想想...")
    BlorikoThinking.show()
    log(f"开始 AskBlorikoAndSet，问题长度: {len(question)} 字符, deepthink(忽略)={deepthink}", logging.INFO)

    # 预检全局 AI 配置，给出可读错误（含免密钥供应商）
    api_url, auth_header, model, config_error = _resolve_ai_endpoint()
    if config_error:
        log(f"AskBlorikoAndSet AI 配置错误: {config_error}", logging.ERROR)
        AskBloriko_Answer.setText(config_error)
        BlorikoThinking.hide()
        return config_error

    signals = BlorikoSignals()
    ui_updater = UIUpdater(AskBloriko_Answer, BlorikoThinking)
    signals.responseReceived.connect(ui_updater.update_ui)

    # 临时存储引用，防止被回收
    AskBloriko_Answer._bloriko_signals = signals
    AskBloriko_Answer._bloriko_updater = ui_updater

    def make_request():
        log(
            f"AskBlorikoAndSet 后台请求: model={model}, api={api_url}, auth={'yes' if auth_header else 'no'}",
            logging.INFO,
        )
        try:
            result_content = AskBloriko(question, config=None, deepthink=False)
        except Exception as e:
            result_content = f"未知错误: {str(e)}"
            log(f"AskBlorikoAndSet 异常: {e}", logging.ERROR)
        log(f"发送信号通知 UI 更新，内容长度: {len(result_content) if result_content else 0}", logging.DEBUG)
        signals.responseReceived.emit(result_content or "")
        return result_content

    log("创建线程以异步执行 AskBlorikoAndSet 请求", logging.INFO)
    thread = threading.Thread(target=make_request, daemon=True)
    thread.start()
    log(f"线程已启动，线程ID: {thread.ident}", logging.INFO)
    return "请求已在后台执行"

