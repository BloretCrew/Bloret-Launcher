import json
import os
import requests
import subprocess
from modules.win11toast import toast
from threading import Thread

def InstallJava(Java_Version):
    # 创建新线程执行Java安装
    thread = Thread(target=_install_java_thread, args=(Java_Version,))
    thread.start()

def _install_java_thread(Java_Version):
    # 修复配置文件路径，使用相对路径而不是绝对路径
    config_path = "config.json"
    temp_dir = os.path.join(os.environ.get('TEMP'), "Bloret-Launcher")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        java_versions = config.get("Java_Versions", {})
        
        # 修复Java版本处理逻辑，确保正确获取版本数据
        # 确保Java_Version是字符串类型，避免float类型导致的问题
        version_key = str(Java_Version) if Java_Version is not None else ""
        version_data = java_versions.get(version_key)
        if not version_data:
            toast('错误', f'未找到 Java {Java_Version} 的下载信息。')
            return

        # 获取Windows x64下载链接
        download_url = version_data.get("Windows", {}).get("x64")
        if not download_url:
            toast('错误', f'未找到 Java {Java_Version} 的 Windows x64 下载地址。')
            return

        file_name = os.path.basename(download_url)
        download_path = os.path.join(temp_dir, file_name)

        # 初始化进度通知
        toast('下载中', f'正在下载 Java {Java_Version}...', progress={
            'value': 0,
            'valueStringOverride': '0%'
        })
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress = (downloaded_size / total_size) if total_size > 0 else 0
                    progress_percent = progress * 100
                    toast('下载中', f'正在下载 Java {Java_Version}: {progress_percent:.2f}%', progress={
                        'value': progress,
                        'valueStringOverride': f'{progress_percent:.2f}%'
                    })
        
        toast('安装中', f'正在安装 Java {Java_Version}...', progress={
            'value': 100,
            'valueStringOverride': '100%'
        })
        
        if download_path.endswith('.msi'):
            # /qb for basic UI with progress bar, /qn for no UI
            # /L*v for verbose logging
            log_file = os.path.join(temp_dir, f"java_install_{Java_Version}.log")
            subprocess.run(['msiexec', '/i', download_path, '/qb', f'/L*v {log_file}'], check=True)
            toast('安装完成', f'Java {Java_Version} 安装成功！', progress={
                'value': 100,
                'valueStringOverride': '完成'
            })
        elif download_path.endswith('.zip'):
            # Handle zip extraction for Java 24
            # This part needs more robust implementation for zip files,
            # as it's not a direct silent install like MSI.
            # For now, I'll just notify that it's downloaded.
            toast('下载完成', f'Java {Java_Version} (ZIP) 下载完成，请手动解压安装。', progress={
                'value': 100,
                'valueStringOverride': '完成'
            })
            return
        else:
            toast('错误', f'不支持的文件类型: {file_name}')
            return

        os.remove(download_path)
        toast('清理完成', '安装文件已删除。', progress={
            'value': 100,
            'valueStringOverride': '完成'
        })

    except requests.exceptions.RequestException as e:
        toast('网络错误', f'下载 Java {Java_Version} 失败: {e}')
    except subprocess.CalledProcessError as e:
        toast('安装失败', f'Java {Java_Version} 安装失败: {e}')
    except Exception as e:
        toast('错误', f'发生未知错误: {e}')