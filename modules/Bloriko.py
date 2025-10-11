import requests
import json
import os
from qfluentwidgets import MessageBox
from modules.log import log


def AskBloriko(text):
    """
    发送文本到 AI 服务并返回响应
    
    Args:
        text (str): 要发送给 AI 的文本
        
    Returns:
        str: 服务端返回的响应数据中的 content 字段值
    """
    # 获取配置文件路径
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        return "配置文件未找到"
    except json.JSONDecodeError:
        return "配置文件格式错误"

    # 检查登录状态
    if not config.get("Bloret_PassPort_Login", False):
        return "Bloret_PassPort_Not_Login"

    # 设置 name 字段
    user_name = config.get("Bloret_PassPort_UserName", "")
    
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
    
    # 发送 POST 请求
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
        result = response.json()
        
        # 返回 content 字段值
        if "content" in result:
            return result["content"]
        else:
            return "未能获取到 AI 回复内容"
    except requests.exceptions.RequestException as e:
        # 处理请求异常
        return f"请求失败: {str(e)}"
    except json.JSONDecodeError:
        # 处理响应不是有效 JSON 的情况
        return "服务器响应不是有效的 JSON 格式"


def AskBlorikoAndSet(self, widget, text, AskBloriko_Answer):
    """
    调用 Bloriko 函数获取 AI 回复，并将结果设置到 StrongBodyLabel 上
    
    Args:
        text (str): 要发送给 AI 的文本
        AskBloriko_Answer (StrongBodyLabel): 用于显示 AI 回复的 StrongBodyLabel 控件
    """
    # 先设置加载中状态
    AskBloriko_Answer.setText("让络可好好想想...")

    # 调用 Bloriko 函数获取 AI 回复
    response_content = AskBloriko(text)
    if response_content == "Bloret_PassPort_Not_Login":
        log("用户未登录，无法使用 Bloriko 功能")
        w = MessageBox("Bloriko 还不知道您是谁", "Bloriko AI 需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。请先登录，确认以转到通行证页面。", widget)
        if w.exec():
            self.switchTo(self.passportInterface)
    else :
        # 将回复内容设置到 StrongBodyLabel 上
        AskBloriko_Answer.setText(response_content)