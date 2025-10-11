import requests
import json
from qfluentwidgets import StrongBodyLabel


def AskBloriko(text):
    """
    发送文本到 AI 服务并返回响应
    
    Args:
        text (str): 要发送给 AI 的文本
        
    Returns:
        str: 服务端返回的响应数据中的 content 字段值
    """
    url = "http://pcfs.eno.ink:2/api/ai/post"
    
    # 构造请求体
    payload = {
        "name": "player",
        "text": text,
        "messages": []
    }
    
    # 发送 POST 请求
    try:
        response = requests.post(url, json=payload)
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


def AskBlorikoAndSet(text, AskBloriko_Answer):
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
    
    # 将回复内容设置到 StrongBodyLabel 上
    AskBloriko_Answer.setText(response_content)
