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

def search_mods(search_term, facets=None, limit=10):
    """搜索 Modrinth 项目。

    Returns:
        dict: API JSON（含 hits），失败时返回空 list（兼容旧调用方）。
    """
    try:
        limit = max(1, min(int(limit or 10), 20))
    except (TypeError, ValueError):
        limit = 10
    url = f"https://api.modrinth.com/v2/search?query={requests.utils.quote(str(search_term or ''))}&limit={limit}"

    if facets:
        url += f"&facets={requests.utils.quote(json.dumps(facets))}"

    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", []) if isinstance(data, dict) else []
            log(f"搜索 Modrinth 模组: {search_term} 成功, hits={len(hits)}", logging.INFO)
            return data
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


def search_mods_structured(search_term, game_version=None, loader="fabric", limit=8):
    """结构化搜索，供 AI 工具使用。返回精简 hit 列表（list[dict]）。"""
    facets = [["project_type:mod"]]
    if loader:
        facets.append([f"categories:{loader}"])
    if game_version:
        facets.append([f"versions:{game_version}"])

    data = search_mods(search_term, facets=facets, limit=limit)
    if not isinstance(data, dict):
        return []

    results = []
    for hit in data.get("hits", []) or []:
        desc = (hit.get("description") or "").replace("\n", " ").strip()
        if len(desc) > 120:
            desc = desc[:117] + "..."
        results.append({
            "slug": hit.get("slug") or "",
            "title": hit.get("title") or hit.get("slug") or "Unknown",
            "description": desc,
            "downloads": hit.get("downloads", 0),
            "project_id": hit.get("project_id") or hit.get("id") or "",
            "categories": hit.get("display_categories") or hit.get("categories") or [],
        })
    log(
        f"search_mods_structured: query={search_term!r}, version={game_version}, "
        f"loader={loader}, count={len(results)}",
        logging.INFO,
    )
    return results


def get_project(slug_or_id):
    """获取 Modrinth 项目详情。成功返回 dict，失败返回 None。"""
    if not slug_or_id:
        return None
    url = f"https://api.modrinth.com/v2/project/{requests.utils.quote(str(slug_or_id), safe='')}"
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            log(f"获取 Modrinth 项目成功: {slug_or_id}", logging.INFO)
            return data
        log(f"获取项目失败: {slug_or_id} status={response.status_code}", logging.WARNING)
        return None
    except Exception as e:
        log(f"获取项目异常: {slug_or_id}: {e}", logging.ERROR)
        return None


def get_project_summary(slug_or_id):
    """精简项目摘要，供 AI 校验工具使用。"""
    data = get_project(slug_or_id)
    if not data:
        return {"ok": False, "error": f"project not found: {slug_or_id}"}
    versions = data.get("game_versions") or []
    # 版本列表可能很长，只保留尾部常见版本
    if len(versions) > 24:
        versions = versions[-24:]
    return {
        "ok": True,
        "slug": data.get("slug") or "",
        "title": data.get("title") or "",
        "project_type": data.get("project_type") or "",
        "loaders": data.get("loaders") or [],
        "game_versions": versions,
        "downloads": data.get("downloads", 0),
        "description": ((data.get("description") or "").replace("\n", " ").strip())[:160],
    }

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
