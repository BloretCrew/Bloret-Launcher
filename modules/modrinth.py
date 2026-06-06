import requests, logging, json
import sys
from modules.log import log
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import subprocess
import threading
from PySide6.QtWidgets import QWidget, QFileDialog
from modules.i18n import i18nText
from modules.process_utils import hidden_process_kwargs

def search_mods(search_term, facets=None):
    url = f"https://api.modrinth.com/v2/search?query={search_term}&limit=10"
    
    if facets:
        url += f"&facets={requests.utils.quote(json.dumps(facets))}"
    
    # 创建一个包含重试策略的会话
    session = requests.Session()
    
    # 定义重试策略
    retry_strategy = Retry(
        total=3,  # 总重试次数
        backoff_factor=1,  # 重试间隔
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
    )
    
    # 创建适配器并将其挂载到会话
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            log(f"搜索 Modrinth 模组: {search_term} 成功", logging.INFO)
            return data
        else:
            log(f"搜索失败: {response.status_code}", logging.ERROR)
            return []
    except requests.exceptions.SSLError as e:
        log(f"SSL错误: {str(e)}", logging.ERROR)
        return []
    except requests.exceptions.ConnectionError as e:
        log(f"连接错误: {str(e)}", logging.ERROR)
        return []
    except requests.exceptions.Timeout as e:
        log(f"请求超时: {str(e)}", logging.ERROR)
        return []
    except requests.exceptions.RequestException as e:
        log(f"请求异常: {str(e)}", logging.ERROR)
        return []
    except Exception as e:
        log(f"搜索异常: {str(e)}", logging.ERROR)
        return []

def Get_Mod_File_Download_Url(slug, loaders=None, game_versions=None):
    """
    获取指定项目的文件下载URL
    
    Args:
        slug (str): 项目ID或slug
        loaders (str): 加载器类型，如"fabric"
        game_versions (str): 游戏版本，如"1.18.1"
        
    Returns:
        str: 文件下载URL
    """
    # 构建URL
    url = f"https://api.modrinth.com/v2/project/{slug}/version"
    
    # 创建一个包含重试策略的会话
    session = requests.Session()
    
    # 定义重试策略
    retry_strategy = Retry(
        total=3,  # 总重试次数
        backoff_factor=1,  # 重试间隔
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
    )
    
    # 创建适配器并将其挂载到会话
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 构建查询参数
    query_parts = []
    if loaders:
        if isinstance(loaders, str):
            loaders = [loaders]
        query_parts.append(f'loaders={requests.utils.quote(json.dumps(loaders))}')
    if game_versions:
        if isinstance(game_versions, str):
            game_versions = [game_versions]
        query_parts.append(f'game_versions={requests.utils.quote(json.dumps(game_versions))}')
    
    if query_parts:
        url = url + "?" + "&".join(query_parts)

    try:
        # 发送GET请求
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and "files" in data[0] and len(data[0]["files"]) > 0:
                for f in data[0]["files"]:
                    if f.get("filename", "").endswith(".jar"):
                        log(f"找到项目 {slug} 的文件: {f['filename']}", logging.INFO)
                        return f["url"]
                first_url = data[0]["files"][0]["url"]
                log(f"未找到项目 {slug} 的JAR文件，返回第一个文件的URL {first_url}", logging.WARNING)
                return first_url
            else:
                log(f"未找到项目 {slug} 的文件", logging.ERROR)
                return None
        else:
            log(f"请求失败，状态码: {response.status_code}", logging.ERROR)
            return None
    except requests.exceptions.SSLError as e:
        log(f"SSL错误: {str(e)}", logging.ERROR)
        return None
    except requests.exceptions.ConnectionError as e:
        log(f"连接错误: {str(e)}", logging.ERROR)
        return None
    except requests.exceptions.Timeout as e:
        log(f"请求超时: {str(e)}", logging.ERROR)
        return None
    except requests.exceptions.RequestException as e:
        log(f"请求异常: {str(e)}", logging.ERROR)
        return None
    except Exception as e:
        log(f"获取下载URL异常: {str(e)}", logging.ERROR)
        return None


def add_mrpack(parent_widget: QWidget = None):
    log(i18nText("添加 Modrinth Modpack"), logging.INFO)

    # 弹出文件选择对话框
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        i18nText("选择 .mrpack 文件"),
        "",
        "Modrinth Modpack Files (*.mrpack)"
    )

    # 如果用户选择了文件
    if file_path:
        # 创建信息栏
        if parent_widget:
            info_bar = InfoBar(parent=parent_widget)
            info_bar.show()
        
        def run_install():
            try:
                # 运行 mrpack-install 命令
                executable = "mrpack-install.exe" if sys.platform == "win32" else "mrpack-install"
                process = subprocess.Popen(
                    [executable, file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    **hidden_process_kwargs(),
                )
                
                # 实时输出日志
                last_line = ""
                for line in process.stdout:
                    print(line, end='')
                    last_line = line
                    # 更新信息栏
                    if parent_widget:
                        # 这里可以根据需要更新信息栏的状态
                        # 例如，可以根据输出内容更新信息栏的文本
                        info_bar.setMessage(last_line.strip()[:50])  # 限制文本长度
                
                # 等待进程结束
                process.wait()
                
                # 检查最后一条日志
                if "Done :) Have a nice day" in last_line.strip():
                        log(i18nText("Modpack 安装成功!"))
                        if parent_widget:
                            info_bar.setMessage(i18nText("安装成功!"))
                            info_bar.setSuccess()
                else:
                        log(i18nText("Modpack 安装失败!"))
                        if parent_widget:
                            info_bar.setMessage(i18nText("安装失败!"))
                            info_bar.setError()
                    
            except Exception as e:
                    log(f"安装过程中发生错误: {str(e)}", logging.ERROR)
                    if parent_widget:
                        info_bar.setMessage(f"错误: {str(e)}")
                        info_bar.setError()
            finally:
                    # 关闭信息栏
                    if parent_widget:
                        info_bar.close()
        
        # 在单独线程中运行安装过程
        thread = threading.Thread(target=run_install)
        thread.daemon = True
        thread.start()
    else:
        log(i18nText("未选择文件"))
