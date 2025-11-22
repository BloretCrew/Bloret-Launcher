import requests
import json
import os
from qfluentwidgets import MessageBox
from modules.log import log
import threading
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtCore import Qt
import logging
import hashlib
import time

class BlorikoSignals(QObject):
    """Bloriko 信号类"""
    responseReceived = pyqtSignal(str)  # 当接收到 AI 响应时发出
    errorOccurred = pyqtSignal(str)     # 当发生错误时发出
    
    def __init__(self):
        super().__init__()
        log("BlorikoSignals 信号类初始化完成", logging.DEBUG)


def continue_ai_response(connection_id):
    """
    当AI响应需要继续获取结果时调用此函数
    
    Args:
        connection_id (str): 连接ID
        
    Returns:
        str: AI的完整回复内容
    """
    url = f"http://pcfs.eno.ink:20000/api/aicontinue?connectionId={connection_id}"
    
    log(f"开始继续获取AI响应，连接ID: {connection_id}", logging.INFO)
    
    while True:  # 持续重试直到成功
        try:
            log(f"发送继续请求到: {url}", logging.DEBUG)
            log(f"请求 json: {{'connectionId': '{connection_id}'}}", logging.DEBUG)
            
            response = requests.get(url)
            log(f"继续获取响应状态码: {response.status_code}", logging.DEBUG)
            log(f"响应内容： {response.text}", logging.DEBUG)
            
            response.raise_for_status()
            result = response.json()
            
            log(f"继续获取响应结果: {result}", logging.DEBUG)
            
            if result.get("status"):
                if "content" in result:
                    content = result["content"]
                    log(f"成功获取到完整回复内容，长度: {len(content)}字符", logging.INFO)
                    return content
                elif "message" in result:
                    message = result["message"]
                    log(f"AI还在处理中: {message}，等待5秒后重试", logging.INFO)
                    # 还在处理中，等待5秒后重试
                    time.sleep(5)
                    continue  # 继续循环重试
                else:
                    log("继续获取响应成功但无内容", logging.WARNING)
                    return "未能获取到 AI 回复内容"
            else:
                # status == false，等待5秒后重试
                error_msg = result.get("error", "未知错误")
                log(f"继续获取失败(status=false): {error_msg}，等待5秒后重试", logging.WARNING)
                time.sleep(5)
                continue  # 继续循环重试
                
        except requests.exceptions.RequestException as e:
            log(f"继续获取请求失败: {str(e)}，等待5秒后重试", logging.ERROR)
            time.sleep(5)
            continue  # 继续循环重试
        except json.JSONDecodeError as e:
            log(f"继续获取响应JSON解析失败: {str(e)}，等待5秒后重试", logging.ERROR)
            time.sleep(5)
            continue  # 继续循环重试
        except Exception as e:
            log(f"继续获取发生未知错误: {str(e)}，等待5秒后重试", logging.ERROR)
            time.sleep(5)
            continue  # 继续循环重试


def AskBloriko(question, config):
    """
    向Bloriko发送问题并获取回答
    
    Args:
        question (str): 用户的问题
        config (dict): 配置信息
        
    Returns:
        str: AI的回复内容
    """
    log(f"开始处理AI请求，问题长度: {len(question)}字符", logging.INFO)
    
    # 获取用户信息
    user_name = config.get("Bloret_PassPort_UserName", "")
    user_token = config.get("Bloret_PassPort_PassWord", "")
    
    log(f"获取用户信息 - 用户名: {user_name}, token长度: {len(user_token) if user_token else 0}", logging.DEBUG)
    
    if not user_name:
        log("用户名为空", logging.ERROR)
        return "用户名为空"
    
    def make_request():
        url = "http://pcfs.eno.ink:20000/api/ai"
        
        payload = {
            "pause": True,
            "model": "Bloriko",
            "OauthApp": {
                "app_id": "BloretLauncher",
                "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
            },
            "user": {
                "name": user_name,
                "token": user_token
            },
            "context": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        log(f"准备发送AI请求到: {url}", logging.INFO)
        log(f"请求payload: {payload}", logging.DEBUG)
        
        try:
            log("开始发送POST请求...", logging.DEBUG)
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            log(f"收到响应，状态码: {response.status_code}", logging.INFO)
            log(f"响应头: {dict(response.headers)}", logging.DEBUG)
            
            response.raise_for_status()
            result = response.json()
            
            log(f"响应JSON解析成功: {result}", logging.DEBUG)
            
            if result.get("status"):
                log("AI响应状态为成功", logging.INFO)
                if result.get("pause"):
                    connection_id = result.get("connectionId")
                    log(f"检测到pause=true，需要继续获取结果，连接ID: {connection_id}", logging.INFO)
                    if connection_id:
                        return continue_ai_response(connection_id)
                    else:
                        log("警告: pause=true但没有connectionId", logging.WARNING)
                        return "未能获取到 AI 回复内容"
                else:
                    content = result.get("content", "未能获取到 AI 回复内容")
                    log(f"直接获取到AI回复内容，长度: {len(content)}字符", logging.INFO)
                    return content
            else:
                error_msg = result.get("error", "未知错误")
                log(f"AI响应状态为失败，错误信息: {error_msg}", logging.ERROR)
                # 特殊处理认证失败情况
                if "认证失败" in error_msg or "权限" in error_msg:
                    log(f"Bloret PassPort 认证失败: {error_msg}", logging.ERROR)
                    return "Bloret PassPort 认证失败，请重新登录"
                return f"请求失败: {error_msg}"
                
        except requests.exceptions.HTTPError as e:
            log(f"HTTP错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            log(f"HTTP状态码: {e.response.status_code if e.response else '未知'}", logging.ERROR)
            log(f"HTTP响应头: {dict(e.response.headers) if e.response else '无响应'}", logging.ERROR)
            log(f"HTTP响应内容: {e.response.text if e.response else '无响应内容'}", logging.ERROR)
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
    thread.join(timeout=30)  # 30秒超时
    
    if thread.is_alive():
        log("AI请求超时(30秒)，线程仍在运行", logging.ERROR)
        return "请求超时，请稍后重试"
    
    final_result = result[0]
    log(f"AI请求处理完成，最终返回内容长度: {len(final_result) if final_result else 0}字符", logging.INFO)
    return final_result
    # else:
    #     # 同步执行（会阻塞调用线程）
    #     log("同步执行请求", logging.INFO)
    #     result = make_request()
    #     log("同步请求完成", logging.INFO)
    #     return result


def AskBlorikoAndSet(question, AskBloriko_Answer, BlorikoThinking, parent):
    """
    向Bloriko发送问题并获取回答，直接设置到UI控件
    
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
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        log("成功读取配置文件 config.json", logging.DEBUG)
    except FileNotFoundError:
        log("配置文件 config.json 未找到", logging.ERROR)
        return ""
    except json.JSONDecodeError as e:
        log(f"配置文件 config.json 格式错误: {str(e)}", logging.ERROR)
        return ""

    def show_login_message():
        log("显示登录提示消息框", logging.INFO)
        w = MessageBox("登录才可使用联机功能", "Easytier 联机需要您登录 Bloret PassPort 才能使用，您尚未登录 Bloret PassPort。\n请先登录，确认以转到通行证页面。", parent)
        if w.exec():
            parent.switchTo(parent.passportInterface)
            log("用户点击确认，切换到通行证界面", logging.INFO)

    if not config.get("Bloret_PassPort_Login", False):
        log("用户未登录Bloret PassPort，显示登录提示", logging.WARNING)
        # 在主线程中显示消息框
        QTimer.singleShot(0, show_login_message)
        return "未登录"

    # 获取用户信息
    user_name = config.get("Bloret_PassPort_UserName", "")
    user_token = config.get("Bloret_PassPort_PassWord", "")
    
    log(f"当前用户: {user_name}", logging.DEBUG)
    log(f"用户token: {'已设置' if user_token else '未设置'} (长度: {len(user_token) if user_token else 0})", logging.DEBUG)
    
    # 检查必要的用户信息
    if not user_name:
        log("用户名为空，无法使用 Bloriko 功能", logging.ERROR)
        return "用户名为空"

    def make_request():
        url = "http://pcfs.eno.ink:20000/api/ai"
        log(f"准备发送请求到 Bloriko AI 服务，URL: {url}", logging.INFO)
        
        # 构造请求体，适配新的API格式
        payload = {
            "pause": True,  # 允许暂停，以便处理工具调用
            "model": "Bloriko",
            "OauthApp": {
                "app_id": "BloretLauncher",
                "app_secret": "s4d56f4a68sd46g54asd46f54a5dsf654asdf546"
            },
            "user": {
                "name": user_name,
                "token": user_token
            },
            "context": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
        log(f"请求体数据: {payload}", logging.DEBUG)
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        log("已设置请求头信息", logging.DEBUG)
        
        result_content = ""
        
        # 发送 POST 请求
        try:
            log("正在发送 POST 请求到 Bloriko AI 服务", logging.INFO)
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            log(f"收到响应，状态码: {response.status_code}", logging.INFO)
            
            response.raise_for_status()  # 如果响应状态码不是 200，会抛出异常
            result = response.json()
            log(f"成功解析响应 JSON，响应内容大小: {len(str(result))} 字符", logging.DEBUG)
            
            # 根据新的API格式处理响应
            if result.get("status"):
                # 成功响应
                log("AI响应状态为成功", logging.INFO)
                if result.get("pause"):
                    # AI正在使用工具，需要继续获取结果
                    connection_id = result.get("connectionId")
                    if connection_id:
                        log(f"AI正在使用工具，连接ID: {connection_id}，开始继续获取结果", logging.INFO)
                        result_content = continue_ai_response(connection_id)
                        log(f"最终回复内容长度: {len(result_content)}字符", logging.INFO)
                        log(f"最终回复内容预览: {result_content[:100]}{'...' if len(result_content) > 100 else ''}", logging.DEBUG)
                    else:
                        result_content = "未能获取到连接ID"
                        log("响应中未找到 connectionId 字段", logging.WARNING)
                else:
                    # 直接获取到完整响应
                    if "content" in result:
                        result_content = result["content"]
                        log(f"直接获取到完整回复内容，长度: {len(result_content)}字符", logging.INFO)
                        log(f"回复内容预览: {result_content[:100]}{'...' if len(result_content) > 100 else ''}", logging.DEBUG)
                    else:
                        result_content = "未能获取到 AI 回复内容"
                        log("响应中未找到 content 字段", logging.WARNING)
            else:
                # 错误响应
                error_msg = result.get("error", "未知错误")
                log(f"AI响应状态为失败，错误信息: {error_msg}", logging.ERROR)
                if "认证失败" in error_msg or "权限" in error_msg:
                    result_content = "Bloret PassPort 认证失败，请重新登录"
                    log(f"认证失败: {error_msg}", logging.ERROR)
                else:
                    result_content = f"AI服务错误: {error_msg}"
                    log(f"AI服务返回错误: {error_msg}", logging.ERROR)
                    
        except requests.exceptions.HTTPError as e:
            # 处理HTTP错误（包括400错误）
            result_content = f"请求失败: {str(e)}"
            log(f"HTTP错误: {type(e).__name__}: {str(e)}", logging.ERROR)
            log(f"HTTP状态码: {e.response.status_code if e.response else '未知'}", logging.ERROR)
            log(f"HTTP响应头: {dict(e.response.headers) if e.response else '无响应'}", logging.ERROR)
            log(f"HTTP响应内容: {e.response.text if e.response else '无响应内容'}", logging.ERROR)
            log(f"请求URL: {url}", logging.ERROR)
            log(f"请求Payload: {payload}", logging.ERROR)
        except requests.exceptions.RequestException as e:
            # 处理其他请求异常
            result_content = f"请求失败: {str(e)}"
            log(f"请求 Bloriko AI 服务失败: {type(e).__name__}: {str(e)}", logging.ERROR)
        except json.JSONDecodeError as e:
            # 处理响应不是有效 JSON 的情况
            result_content = "服务器响应不是有效的 JSON 格式"
            log(f"JSON解析失败: {str(e)}", logging.ERROR)
        except Exception as e:
            result_content = f"未知错误: {str(e)}"
            log(f"处理 Bloriko 响应时发生未知错误: {type(e).__name__}: {str(e)}", logging.ERROR)
        
        # 设置结果到UI控件
        log(f"准备将结果设置到UI控件，内容长度: {len(result_content)}字符", logging.DEBUG)
        AskBloriko_Answer.setText(result_content)
        BlorikoThinking.hide()
        log("已将 Bloriko 响应设置到界面控件", logging.INFO)
        return result_content
    
    # 在单独线程中执行网络请求
    log("创建线程以异步执行请求", logging.INFO)
    thread = threading.Thread(target=make_request)
    thread.daemon = True  # 设置为守护线程
    thread.start()
    log(f"线程已启动，线程ID: {thread.ident}", logging.INFO)
    return "请求已在后台执行"