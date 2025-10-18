import requests
import json
import os
from qfluentwidgets import MessageBox
from modules.log import log
import threading
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtCore import Qt
import logging

class BlorikoSignals(QObject):
    """处理Bloriko响应的信号类"""
    finished = pyqtSignal(str)  # 当请求完成时发出信号


def AskBloriko(text, AskBloriko_Answer):
    """
    发送文本到 AI 服务并返回响应
    
    Args:
        text (str): 要发送给 AI 的文本
        callback (function): 可选的回调函数，接收响应内容作为参数
        
    Returns:
        str: 当同步调用时返回响应内容，异步调用时返回提示信息
    """
    
    log(f"开始调用 AskBloriko 函数，请求文本: {text[:50]}{'...' if len(text) > 50 else ''}", logging.INFO)
    
    # 读取配置文件
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        log("成功读取配置文件 config.json", logging.DEBUG)
    except FileNotFoundError:
        log("配置文件 config.json 未找到", logging.ERROR)
        return ""
    except json.JSONDecodeError:
        log("配置文件 config.json 格式错误", logging.ERROR)
        return ""

    # 检查登录状态
    is_logged_in = config.get("Bloret_PassPort_Login", False)
    log(f"用户登录状态: {is_logged_in}", logging.DEBUG)
    
    if not is_logged_in:
        log("用户未登录，无法使用 Bloriko 功能", logging.WARNING)
        return "Bloret_PassPort_Not_Login"

    # 设置 name 字段
    user_name = config.get("Bloret_PassPort_UserName", "")
    log(f"当前用户: {user_name}", logging.DEBUG)
    
    # 定义在单独线程中执行的请求函数
    def make_request():
        url = "http://pcfs.eno.ink:2/api/ai/post"
        log(f"准备发送请求到 Bloriko AI 服务，URL: {url}", logging.INFO)
        
        # 构造请求体
        payload = {
            "name": user_name,
            "text": text,
            "messages": []
        }
        log(f"请求体数据: {payload}", logging.DEBUG)
        
        # 设置请求头
        headers = {
            "key": "RHEDARANDDETRITALSERVERPCFSpiecesandcloudflashserver87654321",
            "model": "Bloriko"
        }
        log("已设置请求头信息", logging.DEBUG)
        
        result_content = ""
        
        # 发送 POST 请求
        try:
            log("正在发送 POST 请求到 Bloriko AI 服务", logging.INFO)
            response = requests.post(url, json=payload, headers=headers)
            log(f"收到响应，状态码: {response.status_code}", logging.INFO)
            
            response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
            result = response.json()
            log(f"成功解析响应 JSON，响应内容大小: {len(str(result))} 字符", logging.DEBUG)
            
            # 返回 content 字段值
            if "content" in result:
                result_content = result["content"]
                log(f"Bloriko 回复内容: {result_content[:100]}{'...' if len(result_content) > 100 else ''}", logging.INFO)
            else:
                result_content = "未能获取到 AI 回复内容"
                log("响应中未找到 content 字段", logging.WARNING)
        except requests.exceptions.RequestException as e:
            # 处理请求异常
            result_content = f"请求失败: {str(e)}"
            log(f"请求 Bloriko AI 服务失败: {str(e)}", logging.ERROR)
        except json.JSONDecodeError:
            # 处理响应不是有效 JSON 的情况
            result_content = "服务器响应不是有效的 JSON 格式"
            log("服务器响应不是有效的 JSON 格式", logging.ERROR)
        except Exception as e:
            result_content = f"未知错误: {str(e)}"
            log(f"处理 Bloriko 响应时发生未知错误: {str(e)}", logging.ERROR)
        
        # 如果提供了回调函数，则调用它
        # if callback:
        #     log("准备调度回调函数处理响应结果", logging.DEBUG)
        #     # 使用QTimer确保回调在主线程中执行
        #     def execute_callback():
        #         log("Lambda 函数（execute_callback）被执行，准备调用回调", logging.DEBUG)
        #         try:
        #             callback(result_content)
        #             log("回调函数调用成功", logging.DEBUG)
        #         except Exception as e:
        #             log(f"执行回调函数时发生错误: {e}", logging.ERROR)
        #     QTimer.singleShot(0, execute_callback)
        #     log("回调函数已调度", logging.DEBUG)
        # else:
        #     log("同步调用，直接返回结果", logging.DEBUG)
        AskBloriko_Answer.setText(result_content)
        
        log("已将 Bloriko 响应设置到界面控件", logging.INFO)
        return result_content
        
    
    # 在单独线程中执行网络请求
    # if callback:
    log("创建线程以异步执行请求", logging.INFO)
    thread = threading.Thread(target=make_request)
    thread.daemon = True  # 设置为守护线程
    thread.start()
    log(f"线程已启动，线程ID: {thread.ident}", logging.INFO)
    return "请求已在后台执行"
    # else:
    #     # 同步执行（会阻塞调用线程）
    #     log("同步执行请求", logging.INFO)
    #     result = make_request()
    #     log("同步请求完成", logging.INFO)
    #     return result


def AskBlorikoAndSet(self, widget, text, AskBloriko_Answer):
    """
    调用 Bloriko 函数获取 AI 回复，并将结果设置到 StrongBodyLabel 上
    
    Args:
        text (str): 要发送给 AI 的文本
        AskBloriko_Answer (StrongBodyLabel): 用于显示 AI 回复的 StrongBodyLabel 控件
    """
    log(f"开始调用 AskBlorikoAndSet 函数，请求文本: {text[:50]}{'...' if len(text) > 50 else ''}", logging.INFO)
    
    # 读取配置文件
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        log("成功读取配置文件 config.json", logging.DEBUG)
    except FileNotFoundError:
        log("配置文件 config.json 未找到", logging.ERROR)
        return ""
    except json.JSONDecodeError:
        log("配置文件 config.json 格式错误", logging.ERROR)
        return ""

    # 检查登录状态
    is_logged_in = config.get("Bloret_PassPort_Login", False)
    log(f"用户登录状态: {is_logged_in}", logging.DEBUG)
    
    # 定义登录提示消息框函数
    def show_login_message():
        log("显示登录提示消息框", logging.INFO)
        w = MessageBox("Bloriko 还不知道您是谁", "Bloriko AI 需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。\n请先登录，确认以转到通行证页面。", widget)
        if w.exec():
            self.switchTo(self.passportInterface)
            log("用户点击确认，切换到通行证界面", logging.INFO)

    if not is_logged_in:
        # 在主线程中显示消息框
        QTimer.singleShot(0, show_login_message)
        return
    
    # 设置文本格式为Markdown
    AskBloriko_Answer.setTextFormat(Qt.MarkdownText)
    log("已设置 StrongBodyLabel 文本格式为 Markdown", logging.DEBUG)
    
    # 先设置加载中状态
    AskBloriko_Answer.setText("让络可好好想想...")
    log("已在界面显示'加载中'状态", logging.DEBUG)

    # 定义回调函数处理响应
    # def handle_response(response_content):
    #     log("进入 handle_response 函数", logging.DEBUG)
    #     log(f"处理 Bloriko 响应，内容: {response_content[:50]}{'...' if len(response_content) > 50 else ''}", logging.INFO)
    #     # 将回复内容设置到 StrongBodyLabel 上
    #     AskBloriko_Answer.setText(response_content)
    #     log("已将 Bloriko 响应设置到界面控件", logging.INFO)

    # 调用 Bloriko 函数获取 AI 回复（异步方式）
    result = AskBloriko(text, AskBloriko_Answer)
    log(f"AskBloriko 调用完成，返回结果: {result}", logging.INFO)