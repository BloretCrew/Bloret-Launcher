import requests
import json
import os
from qfluentwidgets import MessageBox
from modules.log import log
import threading
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtCore import Qt


class BlorikoSignals(QObject):
    """处理Bloriko响应的信号类"""
    finished = pyqtSignal(str)  # 当请求完成时发出信号


def AskBloriko(text, callback=None):
    """
    发送文本到 AI 服务并返回响应
    
    Args:
        text (str): 要发送给 AI 的文本
        callback (function): 可选的回调函数，接收响应内容作为参数
        
    Returns:
        str: 当同步调用时返回响应内容，异步调用时返回提示信息
    """
    
    # 读取配置文件
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        log("配置文件未找到")
        return ""
    except json.JSONDecodeError:
        log("配置文件格式错误")
        return ""

    # 检查登录状态
    if not config.get("Bloret_PassPort_Login", False):
        return "Bloret_PassPort_Not_Login"

    # 设置 name 字段
    user_name = config.get("Bloret_PassPort_UserName", "")
    
    # 定义在单独线程中执行的请求函数
    def make_request():
        url = "http://pcfs.eno.ink:2/api/ai/post"
        
        # 构造请求体
        payload = {
            "name": user_name,
            "text": text,
            "messages": []
        }
        
        # 设置请求头
        headers = {
            "key": "RHEDARANDDETRITALSERVERPCFSpiecesandcloudflashserver87654321",
            "model": "Bloriko"
        }
        
        result_content = ""
        
        # 发送 POST 请求
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
            result = response.json()
            
            # 返回 content 字段值
            if "content" in result:
                result_content = result["content"]
                log(f"Bloriko 回复: {result_content}")
            else:
                result_content = "未能获取到 AI 回复内容"
        except requests.exceptions.RequestException as e:
            # 处理请求异常
            result_content = f"请求失败: {str(e)}"
        except json.JSONDecodeError:
            # 处理响应不是有效 JSON 的情况
            result_content = "服务器响应不是有效的 JSON 格式"
        
        # 如果提供了回调函数，则调用它
        if callback:
            # 使用QTimer确保回调在主线程中执行
            QTimer.singleShot(0, lambda: callback(result_content))
        return result_content
    
    # 在单独线程中执行网络请求
    if callback:
        thread = threading.Thread(target=make_request)
        thread.daemon = True  # 设置为守护线程
        thread.start()
        return "请求已在后台执行"
    else:
        # 同步执行（会阻塞调用线程）
        return make_request()


def AskBlorikoAndSet(self, widget, text, AskBloriko_Answer):
    """
    调用 Bloriko 函数获取 AI 回复，并将结果设置到 StrongBodyLabel 上
    
    Args:
        text (str): 要发送给 AI 的文本
        AskBloriko_Answer (StrongBodyLabel): 用于显示 AI 回复的 StrongBodyLabel 控件
    """
    # 设置文本格式为Markdown
    AskBloriko_Answer.setTextFormat(Qt.MarkdownText)
    
    # 先设置加载中状态
    AskBloriko_Answer.setText("让络可好好想想...")

    # 定义回调函数处理响应
    def handle_response(response_content):
        if response_content == "Bloret_PassPort_Not_Login":
            log("用户未登录，无法使用 Bloriko 功能")
            AskBloriko_Answer.setText("")
            # 在主线程中显示消息框
            QTimer.singleShot(0, lambda: show_login_message())
        else:
            # 将回复内容设置到 StrongBodyLabel 上
            AskBloriko_Answer.setText(response_content)

    def show_login_message():
        w = MessageBox("Bloriko 还不知道您是谁", "Bloriko AI 需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。\n请先登录，确认以转到通行证页面。", widget)
        if w.exec():
            self.switchTo(self.passportInterface)

    # 调用 Bloriko 函数获取 AI 回复（异步方式）
    AskBloriko(text, handle_response)