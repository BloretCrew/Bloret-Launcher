import threading
import requests
import json
from typing import Callable, Any, Dict

def getServerData(ServerName: str, callback: Callable[[Dict[str, Any]], None] = None):
    """
    在单独的线程中向服务器发送请求并获取服务器数据
    
    Args:
        ServerName (str): 服务器名称
        callback (Callable[[Dict[str, Any]], None], optional): 回调函数，当数据获取完成后调用
        
    Returns:
        threading.Thread: 执行请求的线程对象
    """
    def _fetch_data():
        url = f"http://pcfs.eno.ink:20901/api/getserver?name={ServerName}"
        try:
            response = requests.get(url)
            response.raise_for_status()  # 如果响应状态码不是200会抛出异常
            data = response.json()
            if callback:
                callback(data)
            return data
        except Exception as e:
            error_result = {"error": str(e)}
            if callback:
                callback(error_result)
            return error_result
    
    # 创建并启动线程
    thread = threading.Thread(target=_fetch_data)
    thread.daemon = True  # 设置为守护线程，主线程结束时会自动退出
    thread.start()
    
    return thread