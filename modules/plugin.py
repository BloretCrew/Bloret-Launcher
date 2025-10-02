from qfluentwidgets import MessageBox, Dialog
from modules.log import log
import os
import json
import requests
import zipfile
import shutil
import tempfile
import threading
import urllib.parse
from PyQt5.QtWidgets import QApplication
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from modules.customize import CustomizeAppAdd

def install_plugin_from_zip(zip_url, plugin_name):
    '''
    直接从ZIP文件URL安装插件
    参数:
        zip_url: ZIP文件的下载URL
    '''
    try:
        log(f"正在直接从ZIP文件安装插件: {zip_url}")
            
        log(f"插件名称为: {plugin_name}")
        
        # 创建一个带有重试策略的会话用于下载
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 下载ZIP文件
        log(f"正在下载ZIP文件: {zip_url}")
        response = session.get(zip_url, timeout=60)
        response.raise_for_status()
        
        # 创建临时文件保存下载的 zip
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            # 写入文件
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_zip.write(chunk)
            temp_zip_path = temp_zip.name
            
        # 将 zip 解压缩到 %appdata%/Bloret-Launcher/Plugin/{plugin_name} 中
        plugin_dir = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'Plugin', plugin_name)
        
        # 如果目录已存在，先删除
        if os.path.exists(plugin_dir):
            shutil.rmtree(plugin_dir)
            
        # 创建插件目录
        os.makedirs(plugin_dir, exist_ok=True)
        
        # 解压缩 zip 文件
        log(f"正在解压缩插件: {plugin_name} 到 {plugin_dir}")
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(plugin_dir)
            
        # 删除临时文件
        os.unlink(temp_zip_path)
        
        # 构造插件主程序路径（固定为main.exe）
        plugin_exe_path = os.path.join(plugin_dir, "main.exe")
        
        # 检查main.exe是否存在
        if os.path.exists(plugin_exe_path):
            log(f"找到插件主程序: {plugin_exe_path}")
            # 尝试将插件主程序添加到自定义程序列表
            try:
                result = CustomizeAppAdd(plugin_exe_path, plugin_name)
                if result:
                    log(f"成功将插件主程序添加到自定义程序列表: {plugin_exe_path}")
                else:
                    log(f"未能将插件主程序添加到自定义程序列表: {plugin_exe_path}")
            except Exception as e:
                log(f"调用CustomizeAppAdd时发生错误: {str(e)}")
        else:
            log(f"插件主程序不存在: {plugin_exe_path}")
        
        log(f"插件安装成功: {plugin_name}")
        return True
        
    except Exception as e:
        log(f"从ZIP文件安装插件时发生错误: {str(e)}")
        return False


def addPlugin(list_url, plugin_name):
    '''
    添加插件到 Bloret Launcher
    参数:
        list_url: 包含插件信息的列表或字典或URL字符串
        window: 父窗口，用于显示对话框
    '''
    try:
        # 1. list_url 是一个 url，获取 JSON 数据，存入变量 plugin
        
        if not list_url:
            log("无效的URL")
            return False
            
        log(f"正在从以下位置获取插件信息: {list_url}")
        
        # 检查是否是直接的ZIP文件URL（通过文件扩展名判断）
        if list_url.endswith('.zip'):
            # 直接处理ZIP文件下载
            return install_plugin_from_zip(list_url, plugin_name)
        
        # 创建一个带有重试策略的会话
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 尝试请求，处理SSL错误
        try:
            response = session.get(list_url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.SSLError as ssl_error:
            log(f"SSL错误: {str(ssl_error)}")
            # 尝试禁用SSL验证再次请求（仅作为备选方案）
            try:
                response = session.get(list_url, verify=False, timeout=30)
                response.raise_for_status()
                log("警告: SSL验证已禁用，仅作为备选方案")
            except Exception as fallback_error:
                raise Exception(f"SSL连接失败，备选方案也失败: {str(fallback_error)}")
        except Exception as e:
            raise Exception(f"网络请求失败: {str(e)}")
        
        # 检查响应内容是否为空
        if not response.text or not response.text.strip():
            raise Exception("服务器返回空响应")
            
        # 检查响应内容是否为JSON格式
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            # 如果不是JSON类型，记录响应内容的前200个字符用于调试
            preview_content = response.text[:200] if response.text else "空响应"
            raise Exception(f"服务器返回非JSON内容 (Content-Type: {content_type}): {preview_content}")
        
        try:
            plugin = response.json()
        except json.JSONDecodeError as json_error:
            # 如果JSON解析失败，记录响应内容用于调试
            preview_content = response.text[:200] if response.text else "空响应"
            raise Exception(f"JSON解析失败: {str(json_error)}. 响应内容预览: {preview_content}")
            
        # 验证插件数据格式
        log(f"获取到的数据：{plugin}")
        if not isinstance(plugin, dict) or 'name' not in plugin or 'download' not in plugin:
            log("插件数据格式不正确")
            return False

        # 2. 通过网页界面询问用户是否安装插件，而不是使用桌面对话框
        # 构造插件确认页面的URL
        plugin_data = {
            'name': plugin['name'],
            'download': plugin['download'],
            'master': plugin.get('master', 'Unknown'),
            'version': plugin.get('version', 'Unknown')
        }
        
        # 将插件数据编码为URL参数
        plugin_params = urllib.parse.urlencode(plugin_data)
        confirmation_url = f"http://localhost:25252/plugin/confirm?{plugin_params}"
        
        log(f"请在浏览器中打开以下链接确认插件安装: {confirmation_url}")
        # 这里应该触发浏览器打开confirmation_url页面
        # 在实际应用中，可能需要调用系统默认浏览器打开这个链接

        # 3. 用户确认后，下载和解压缩过程放到新线程中进行
        def install_plugin_task():
            try:
                log(f"开始安装插件: {plugin['name']}")

                # 3. 根据 plugin 的 download 值下载 zip 文件
                download_url = plugin['download']
                log(f"正在下载插件: {plugin['name']} 从 {download_url}")

                # 创建一个带有重试策略的会话用于下载
                download_session = requests.Session()
                download_retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
                download_adapter = HTTPAdapter(max_retries=download_retry_strategy)
                download_session.mount("http://", download_adapter)
                download_session.mount("https://", download_adapter)

                # 创建临时文件保存下载的 zip
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                    try:
                        response = download_session.get(download_url, stream=True, timeout=60)
                        response.raise_for_status()
                    except requests.exceptions.SSLError as ssl_error:
                        log(f"下载时SSL错误: {str(ssl_error)}")
                        # 尝试禁用SSL验证再次请求（仅作为备选方案）
                        try:
                            response = download_session.get(download_url, stream=True, verify=False, timeout=60)
                            response.raise_for_status()
                            log("警告: 下载时SSL验证已禁用，仅作为备选方案")
                        except Exception as fallback_error:
                            raise Exception(f"下载时SSL连接失败，备选方案也失败: {str(fallback_error)}")
                    except Exception as e:
                        raise Exception(f"下载失败: {str(e)}")

                    # 写入文件
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_zip.write(chunk)

                    temp_zip_path = temp_zip.name

                # 4. 将 zip 解压缩到 %appdata%/Bloret-Launcher/Plugin/{plugin[name]} 中
                plugin_dir = os.path.join(os.getenv('APPDATA'), 'Bloret-Launcher', 'Plugin', plugin['name'])

                # 如果目录已存在，先删除
                if os.path.exists(plugin_dir):
                    shutil.rmtree(plugin_dir)

                # 创建插件目录
                os.makedirs(plugin_dir, exist_ok=True)

                # 解压缩 zip 文件
                log(f"正在解压缩插件: {plugin['name']} 到 {plugin_dir}")
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(plugin_dir)

                # 删除临时文件
                os.unlink(temp_zip_path)
                
                # 构造插件主程序路径（固定为main.exe）
                plugin_exe_path = os.path.join(plugin_dir, "main.exe")
                
                # 检查main.exe是否存在
                if os.path.exists(plugin_exe_path):
                    log(f"找到插件主程序: {plugin_exe_path}")
                    # 尝试将插件主程序添加到自定义程序列表
                    try:
                        result = CustomizeAppAdd(plugin_exe_path, plugin['name'])
                        if result:
                            log(f"成功将插件主程序添加到自定义程序列表: {plugin_exe_path}")
                        else:
                            log(f"未能将插件主程序添加到自定义程序列表: {plugin_exe_path}")
                    except Exception as e:
                        log(f"调用CustomizeAppAdd时发生错误: {str(e)}")
                else:
                    log(f"插件主程序不存在: {plugin_exe_path}")

                log(f"插件安装成功: {plugin['name']}")

            except Exception as e:
                log(f"安装插件失败: {plugin['name']}, 错误: {str(e)}")
                # 可以在这里添加错误处理，比如显示错误消息

        # 启动新线程执行安装任务
        install_thread = threading.Thread(target=install_plugin_task)
        install_thread.daemon = True
        install_thread.start()

        return True

    except Exception as e:
        log(f"添加插件时发生错误: {str(e)}")
        return False