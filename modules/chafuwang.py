import threading
import requests
import json
from typing import Callable, Any, Dict
from modules.log import log
import logging

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
        log(f"开始获取服务器数据: {ServerName}", logging.INFO)
        log(f"请求URL: {url}", logging.DEBUG)
        
        try:
            log(f"正在发送HTTP GET请求到服务器: {ServerName}", logging.INFO)
            response = requests.get(url)
            log(f"收到服务器 {ServerName} 的响应，状态码: {response.status_code}", logging.INFO)
            
            response.raise_for_status()  # 如果响应状态码不是200会抛出异常
            data = response.json()
            
            log(f"成功解析服务器 {ServerName} 的JSON数据，数据大小: {len(str(data))} 字符", logging.INFO)
            log(f"服务器 {ServerName} 返回的数据: {data}", logging.DEBUG)
            
            if callback:
                log(f"调用回调函数处理服务器 {ServerName} 的数据", logging.DEBUG)
                callback(data)
            return data
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求错误 - 服务器: {ServerName}, 错误: {str(e)}"
            log(error_msg, logging.ERROR)
            error_result = {"error": str(e)}
            if callback:
                log(f"调用回调函数处理服务器 {ServerName} 的错误", logging.DEBUG)
                callback(error_result)
            return error_result
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析错误 - 服务器: {ServerName}, 错误: {str(e)}"
            log(error_msg, logging.ERROR)
            error_result = {"error": "Invalid JSON response"}
            if callback:
                log(f"调用回调函数处理服务器 {ServerName} 的JSON解析错误", logging.DEBUG)
                callback(error_result)
            return error_result
        except Exception as e:
            error_msg = f"获取服务器数据时发生未知错误 - 服务器: {ServerName}, 错误: {str(e)}"
            log(error_msg, logging.ERROR)
            error_result = {"error": str(e)}
            if callback:
                log(f"调用回调函数处理服务器 {ServerName} 的未知错误", logging.DEBUG)
                callback(error_result)
            return error_result
    
    log(f"创建线程以获取服务器数据: {ServerName}", logging.INFO)
    # 创建并启动线程
    thread = threading.Thread(target=_fetch_data)
    thread.daemon = True  # 设置为守护线程，主线程结束时会自动退出
    thread.start()
    
    log(f"线程已启动，用于获取服务器数据: {ServerName} (线程ID: {thread.ident})", logging.INFO)
    return thread