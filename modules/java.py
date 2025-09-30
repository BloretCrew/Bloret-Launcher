import json
import os
import requests
import subprocess
import time
from modules.win11toast import toast, update_progress, notify
from threading import Thread
from modules.log import log
from modules.i18n import i18nText

def InstallJava(Java_Version):
    # 创建新线程执行Java安装
    thread = Thread(target=_install_java_thread, args=(Java_Version,))
    thread.start()

def _install_java_thread(Java_Version):
    log(f"开始安装 Java {Java_Version}")
    # 修复配置文件路径，使用相对路径而不是绝对路径
    config_path = "config.json"
    temp_dir = os.path.join(os.environ.get('TEMP'), "Bloret-Launcher")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        log(f"正在加载配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        log(i18nText("配置文件加载成功。"))
        
        java_versions = config.get("Java_Versions", {})
        
        # 修复Java版本处理逻辑，确保正确获取版本数据
        # 确保Java_Version是字符串类型，避免float类型导致的问题
        version_key = str(Java_Version) if Java_Version is not None else ""
        version_data = java_versions.get(version_key)
        if not version_data:
            log(f"错误: 未找到 Java {Java_Version} 的下载信息。")
            toast(i18nText('错误'), f'未找到 Java {Java_Version} 的下载信息。')
            return
        log(f"已找到 Java {Java_Version} 的下载信息。")

        # 获取Windows x64下载链接
        download_url = version_data.get("Windows", {}).get("x64")
        if not download_url:
            log(f"错误: 未找到 Java {Java_Version} 的 Windows x64 下载地址。")
            toast(i18nText('错误'), f'未找到 Java {Java_Version} 的 Windows x64 下载地址。')
            return
        log(f"已获取 Java {Java_Version} 的下载地址: {download_url}")

        file_name = os.path.basename(download_url)
        download_path = os.path.join(temp_dir, file_name)
        log(f"Java 安装包将下载到: {download_path}")

        # 初始化进度通知
        notify(progress={
            'title': f'正在下载 Java {Java_Version}...',
            'status': i18nText('正在下载...'),
            'value': '0',
            'valueStringOverride': '0%'
        })
        log(f"开始下载 Java {Java_Version}...")
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        log(f"文件总大小: {total_size} 字节")

        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress = (downloaded_size / total_size) if total_size > 0 else 0
                    progress_percent = progress * 100
                    
                    # 更新通知中的进度信息
                    update_progress({
                        'value': progress,
                        'valueStringOverride': f'{progress_percent:.1f}%'
                    })
                    
                    # 每下载5%更新一次日志
                    # if total_size > 0 and downloaded_size % (total_size // 20) == 0:
                    #     log(f"下载进度: {progress_percent:.1f}% ({downloaded_size}/{total_size} bytes)")
            
            log(f"文件下载完成: {downloaded_size} 字节已下载到 {download_path}")
        
        # 下载完成通知
        update_progress({
            'value': 1,
            'valueStringOverride': '100%',
            'status': f'Java {Java_Version} 下载完成'
        })
        log(f"Java {Java_Version} 下载成功。")
        
        notify(progress={
            'title': f'正在安装 Java {Java_Version}...',
            'status': i18nText('正在安装...'),
            'value': '0',
            'valueStringOverride': '0%'
        })
        log(f"开始安装 Java {Java_Version}...")
        
        if download_path.endswith('.msi'):
            log(f"检测到 MSI 安装包: {download_path}")
            # 修复MSI安装命令参数格式
            log_file = os.path.join(temp_dir, f"java_install_{Java_Version}.log")
            log(f"MSI 安装日志将保存到: {log_file}")
            
            # 使用正确的MSI安装命令格式
            cmd = [
                'msiexec', '/i', download_path,
                '/quiet',  # 安静模式安装
                '/norestart',  # 不重启
                '/passive'
            ]
            
            log(f"执行安装命令: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待进程完成
            stdout, stderr = process.communicate()
            log(f"安装进程退出码: {process.returncode}")
            if stdout:
                log(f"MSI 安装标准输出: {stdout}")
            if stderr:
                log(f"MSI 安装标准错误: {stderr}")
                
            if process.returncode == 0:
                log(f"Java {Java_Version} MSI 安装成功。")
                update_progress({
                    'value': 1,
                    'valueStringOverride': i18nText('安装完成'),
                    'status': f'Java {Java_Version} 安装成功'
                })
                # time.sleep(1)  # 等待通知显示
                toast(i18nText('安装成功'), f'Java {Java_Version} 安装成功。')
            else:
                log(f"错误: Java {Java_Version} MSI 安装失败，返回码: {process.returncode}")
                update_progress({
                    'value': 1,
                    'valueStringOverride': i18nText('安装失败'),
                    'status': f'Java {Java_Version} 安装失败，错误码: {process.returncode}'
                })
                # time.sleep(1)  # 等待通知显示
                toast(i18nText('安装失败'), f'Java {Java_Version} 安装失败，错误码: {process.returncode}。')
            
        elif download_path.endswith('.zip') or download_path.endswith('.tar.gz'):
            log(f"检测到压缩包: {download_path}")
            extract_dir = os.path.join(os.environ.get('APPDATA'), '.minecraft', 'runtime', f'java-{Java_Version}')
            os.makedirs(extract_dir, exist_ok=True)
            log(f"将解压到: {extract_dir}")

            try:
                if download_path.endswith('.zip'):
                    import zipfile
                    with zipfile.ZipFile(download_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                elif download_path.endswith('.tar.gz'):
                    import tarfile
                    with tarfile.open(download_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(extract_dir)
                log(f"Java {Java_Version} 压缩包解压成功到 {extract_dir}。")
                update_progress({
                    'value': 1,
                    'valueStringOverride': i18nText('解压完成'),
                    'status': f'Java {Java_Version} 解压完成'
                })
                time.sleep(1)  # 等待通知显示
                toast(i18nText('安装成功'), f'Java {Java_Version} 安装成功。')
            except Exception as e:
                log(f"错误: Java {Java_Version} 压缩包解压失败: {e}")
                update_progress({
                    'value': 1,
                    'valueStringOverride': i18nText('解压失败'),
                    'status': f'Java {Java_Version} 解压失败'
                })
                time.sleep(1)  # 等待通知显示
                toast(i18nText('安装失败'), f'Java {Java_Version} 解压失败。')
        else:
            log(f"错误: 不支持的 Java 安装包格式: {file_name}")
            update_progress({
                'value': 1,
                'valueStringOverride': i18nText('格式错误'),
                'status': f'不支持的格式: {file_name}'
            })
            time.sleep(1)  # 等待通知显示
            toast(i18nText('错误'), f'不支持的 Java 安装包格式: {file_name}')
            return

        # 更新配置文件中的Java路径
        java_path = ""
        if download_path.endswith('.msi'):
            # 对于MSI安装，通常Java会安装到Program Files，需要查找实际路径
            # 简化处理，假设安装成功后Java在系统PATH中或通过其他方式找到
            # 实际应用中需要更复杂的逻辑来查找Java安装路径
            log(i18nText("MSI 安装，尝试查找 Java 路径..."))
            # 这是一个简化的示例，实际需要根据Java版本和系统环境查找
            # 例如，可以通过注册表或特定目录查找java.exe
            java_home = os.environ.get('JAVA_HOME')
            if java_home:
                java_path = os.path.join(java_home, 'bin', 'java.exe')
                log(f"从 JAVA_HOME 获取到 Java 路径: {java_path}")
            else:
                log(i18nText("未找到 JAVA_HOME 环境变量，尝试在常见路径查找。"))
                # 尝试在Program Files中查找
                program_files = os.environ.get('ProgramFiles')
                if program_files:
                    potential_path = os.path.join(program_files, 'Java', f'jdk-{Java_Version}', 'bin', 'java.exe')
                    if os.path.exists(potential_path):
                        java_path = potential_path
                        log(f"在 Program Files 中找到 Java 路径: {java_path}")
            if not java_path:
                log(i18nText("警告: 无法自动确定 MSI 安装的 Java 路径，可能需要手动配置。"))

        elif download_path.endswith('.zip') or download_path.endswith('.tar.gz'):
            # 对于压缩包安装，Java路径就是解压目录下的bin/java.exe
            java_path = os.path.join(extract_dir, 'bin', 'java.exe')
            log(f"压缩包安装，Java 路径设置为: {java_path}")

        if java_path:
            config["Java_Path"] = java_path
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            log(f"配置文件中 Java_Path 已更新为: {java_path}")
        else:
            log(i18nText("警告: 未能确定 Java 路径，配置文件未更新 Java_Path。"))

        # 清理下载的文件
        try:
            os.remove(download_path)
            log(f"已删除下载的安装文件: {download_path}")
            toast(i18nText('清理完成'), i18nText('安装文件已删除。'), duration='short')
        except Exception as e:
            log(f"清理提醒: 无法删除安装文件 {download_path}: {e}")
            toast(i18nText('清理提醒'), f'无法删除安装文件: {e}', duration='short')

    except requests.exceptions.RequestException as e:
        log(f"错误: 下载 Java {Java_Version} 失败: {e}")
        toast(i18nText('下载失败'), f'下载 Java {Java_Version} 失败: {e}')
    except json.JSONDecodeError as e:
        log(f"错误: config.json 解析失败: {e}")
        toast(i18nText('错误'), f'配置文件读取失败: {e}')
    except FileNotFoundError as e:
        log(f"错误: 文件未找到: {e}")
        toast(i18nText('错误'), f'文件操作失败: {e}')
    except subprocess.CalledProcessError as e:
        log(f"错误: Java {Java_Version} 安装失败: {e}")
        toast(i18nText('安装失败'), f'Java {Java_Version} 安装失败: {e}')
    except Exception as e:
        log(f"发生未知错误: {e}")
        toast(i18nText('错误'), f'发生未知错误: {e}')