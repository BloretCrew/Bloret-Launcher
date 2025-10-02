from PyQt5.QtWidgets import QDialog, QApplication, QProgressBar
from qfluentwidgets import Dialog
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from modules.win11toast import notify, update_progress
import logging,os,requests,zipfile,time
import threading
from concurrent.futures import ThreadPoolExecutor
# 以下导入的部分是 Bloret Launcher 所有 © 2025 Bloret Launcher All rights reserved. © 2025 Bloret All rights reserved.的模块，位于 modules 中
from modules.safe import handle_exception
from modules.log import log
from modules.i18n import i18nText

def BL_download(self, version, LM_download_way_choose, LM_Download_Way_minecraft, LM_Download_Way_version, parent):
    class BLDownloadDialog(QDialog):
        def __init__(self, version, parent=None):
            super().__init__(parent)
            self.version = version
            self.setWindowTitle("Bloret Launcher")

            # 检查 .minecraft 文件夹是否存在
            minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
            if not os.path.exists(minecraft_dir):
                log(i18nText(".minecraft 文件夹不存在"))
                uic.loadUi("ui/BL_download.ui", self)
                # 初始化进度条控件
                self.progress_bars = {
                    "version": self.findChild(QProgressBar, "version"),
                    "libraries": self.findChild(QProgressBar, "libraries"),
                    "objects1": self.findChild(QProgressBar, "objects1"),
                    "objects2": self.findChild(QProgressBar, "objects2"),
                    "objects3": self.findChild(QProgressBar, "objects3"),
                    "objects4": self.findChild(QProgressBar, "objects4"),
                    "indexes": self.findChild(QProgressBar, "indexes")
                }
            else:
                log(i18nText(".minecraft 文件夹已存在"))
                uic.loadUi("ui/BL_download_version.ui", self)
                self.progress_bars = {
                    "version": self.findChild(QProgressBar, "version")
                }

            

            # 初始化 threads 属性
            self.threads = []

        def update_progress(self, key, value, message):
            if key in self.progress_bars and self.progress_bars[key]:
                self.progress_bars[key].setValue(value)
            QApplication.processEvents()

        def closeEvent(self, event):
            for thread in self.threads:
                if thread.isRunning():
                    thread.quit()  # 请求线程退出
                    thread.wait()  # 等待线程完全退出
            event.accept()

    class VersionDownloadThread(QThread):
        progress_signal = pyqtSignal(str, int, str)
        error_signal = pyqtSignal(str)
        finished_signal = pyqtSignal()

        def __init__(self, version, minecraft_dir):
            super().__init__()
            self.version = version
            self.minecraft_dir = minecraft_dir
            # self.base_url = f"https://gitee.com/detrital/minecraft/releases/download/minecraft/"
            self.base_url = LM_Download_Way_minecraft.get(LM_download_way_choose)
            log(f"下载链接:{self.base_url}")

        def run(self):
            try:
                log(f"开始下载版本 {self.version}，目标目录: {self.minecraft_dir}")

                # 检查 .minecraft 文件夹是否存在
                minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
                if not os.path.exists(minecraft_dir):
                    log(i18nText(".minecraft 文件夹不存在，开始下载 Minecraft 核心"))
                    success = self.BL_download_minecraft()
                    if not success:
                        self.error_signal.emit(i18nText("下载 Minecraft 核心失败，请检查日志。"))
                        return
                else:
                    log(i18nText(".minecraft 文件夹已存在"))

                # 确保 .minecraft/versions 文件夹存在
                versions_dir = os.path.join(minecraft_dir, "versions")
                if not os.path.exists(versions_dir):
                    os.makedirs(versions_dir)
                    log(f"创建 .minecraft/versions 文件夹: {versions_dir}")
                else:
                    log(i18nText(".minecraft/versions 文件夹已存在"))

                # 确保 .minecraft/versions/{version} 文件夹存在
                version_dir = os.path.join(versions_dir, self.version)
                if not os.path.exists(version_dir):
                    os.makedirs(version_dir)
                    log(f"创建 .minecraft/versions/{self.version} 文件夹: {version_dir}")
                else:
                    log(f".minecraft/versions/{self.version} 文件夹已存在")

                file_name = f"{self.version}.zip"
                file_path = os.path.join(version_dir, file_name)
                log(f"准备下载文件: {file_name} 到路径: {file_path}")

                # 显示通知
                notify(progress={
                    'title': f'下载版本 {self.version}',
                    'status': i18nText('正在下载... ↓'),
                    'value': '0',
                    'valueStringOverride': '0%',
                    'icon': os.path.join(os.getcwd(), 'bloret.ico')
                })
                
                log(f"LM_download_way_choose:{LM_download_way_choose}")
                version_download_url = LM_Download_Way_version.get(LM_download_way_choose)
                log(f"下载链接:{version_download_url}")

                response = requests.get(version_download_url + file_name, stream=True, timeout=10)
                response.raise_for_status()
                log(f"成功获取文件: {file_name}，开始下载")

                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int(downloaded_size / total_size * 100)
                        self.progress_signal.emit("version", progress, f"下载进度: {progress}%")
                        update_progress({'value': progress / 100, 'valueStringOverride': f'{progress}%'})

                log(f"文件 {file_name} 下载完成，开始解压缩")

                # 解压缩文件
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(version_dir)
                log(f"文件 {file_name} 解压缩完成")

                # 删除 .zip 文件
                os.remove(file_path)
                log(f"删除文件: {file_path}")

                self.finished_signal.emit()
                log(f"版本 {self.version} 下载和解压缩完成")

                # 更新通知状态
                update_progress({
                    'status': i18nText('下载完成！✅'),
                    'value': 100,
                    'valueStringOverride': f'100%'
                })
            except Exception as e:
                handle_exception(e)
                log(f"下载版本 {self.version} 时发生错误: {str(e)}", logging.ERROR)
                self.error_signal.emit(str(e))
            finally:
                # 确保资源释放
                if hasattr(self, "response"):
                    self.response.close()
                self.quit()


        def ensure_minecraft_dir(self):
            """确保 .minecraft 文件夹存在"""
            if not os.path.exists(self.MINECRAFT_DIR):
                os.makedirs(self.MINECRAFT_DIR)
                log(f"创建 .minecraft 文件夹: {self.MINECRAFT_DIR}")
            else:
                log(i18nText(".minecraft 文件夹已存在"))

        def BL_download_minecraft(self):
            """下载 Minecraft 资源文件"""
        
            # 确保 .minecraft 文件夹存在
            self.ensure_minecraft_dir()
        
            # 创建必要的子文件夹
            assets_dir = os.path.join(self.MINECRAFT_DIR, "assets")  # 定义 assets 文件夹路径
            objects_dir = os.path.join(assets_dir, "objects")  # 定义 objects 文件夹路径
            indexes_dir = os.path.join(assets_dir, "indexes")  # 定义 indexes 文件夹路径
            libraries_dir = os.path.join(self.MINECRAFT_DIR, "libraries")  # 定义 libraries 文件夹路径
        
            # 确保上述文件夹存在，如果不存在则创建
            os.makedirs(objects_dir, exist_ok=True)  # 创建 objects 文件夹
            os.makedirs(indexes_dir, exist_ok=True)  # 创建 indexes 文件夹
            os.makedirs(libraries_dir, exist_ok=True)  # 创建 libraries 文件夹
        
            # 定义需要下载的文件及其目标路径
            files_to_download = [
                ("indexes.zip", indexes_dir, "indexes"),  # indexes.zip 文件下载到 indexes 文件夹
                ("libraries.zip", libraries_dir, "libraries"),  # libraries.zip 文件下载到 libraries 文件夹
                ("objects-01.zip", objects_dir, "objects1"),  # objects-01.zip 文件下载到 objects 文件夹
                ("objects-02.zip", objects_dir, "objects2"),  # objects-02.zip 文件下载到 objects 文件夹
                ("objects-03.zip", objects_dir, "objects3"),  # objects-03.zip 文件下载到 objects 文件夹
                ("objects-04.zip", objects_dir, "objects4")  # objects-04.zip 文件下载到 objects 文件夹
            ]
        
            # 使用线程锁保护日志输出，避免多线程日志混乱
            log_lock = threading.Lock()
        
            def download_file(file_name, target_dir, progress_key):
                """下载文件并支持重试"""
                url = f"{LM_Download_Way_minecraft.get(LM_download_way_choose)}{file_name}"
                log(f"下载链接:{url}")
                file_path = os.path.join(target_dir, file_name)
                max_retries = 5
                retry_delay = 3
            
                log(f"开始处理文件: {file_name}, 目标路径: {file_path}")
            
                for attempt in range(max_retries):
                    try:
                        log(f"准备下载 {file_name} 到 {file_path} (尝试 {attempt + 1}/{max_retries})")
                        response = requests.get(url, stream=True, timeout=10)
                        response.raise_for_status()
            
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        log(f"下载链接:{url}")
            
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    progress = int(downloaded_size / total_size * 100)
                                    self.progress_signal.emit(progress_key, progress, f"下载进度: {progress}%")
                                    # log(f"文件{file_name},下载进度: {progress}%")
            
                        log(f"文件 {file_name} 下载完成")
                        return True
                    except requests.RequestException as e:
                        log(f"下载 {file_name} 失败 (尝试 {attempt + 1}/{max_retries}): {e}", logging.ERROR)
                        time.sleep(retry_delay)
                    except Exception as e:
                        handle_exception(e)
                        log(f"下载 {file_name} 时发生未知错误: {e}", logging.ERROR)
                        time.sleep(retry_delay)
                    finally:
                        if 'response' in locals():
                            response.close()
            
                log(f"下载 {file_name} 失败，已达到最大重试次数", logging.ERROR)
                return False
            # 使用线程池并发下载文件
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 提交下载任务到线程池
                futures = [executor.submit(download_file, file_name, target_dir, progress_key) for file_name, target_dir, progress_key in files_to_download]
                for future in futures:
                    try:
                        future.result()  # 等待任务完成
                    except Exception as e:
                        handle_exception(e)
                        log(f"下载文件时发生错误: {e}", logging.ERROR)  # 记录任务执行错误日志
        
            # 解压下载的文件
            try:
                for file_name, target_dir, _ in files_to_download:
                    file_path = os.path.join(target_dir, file_name)  # 获取文件路径
                    if os.path.exists(file_path):  # 检查文件是否存在
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:  # 打开 ZIP 文件
                            zip_ref.extractall(target_dir)  # 解压文件到目标目录
                        log(f"文件 {file_name} 解压缩完成")  # 记录解压完成日志
                        os.remove(file_path)  # 删除 ZIP 文件
                        log(f"删除文件: {file_path}")  # 记录删除文件日志
                    else:
                        log(f"文件 {file_name} 不存在，无法解压缩", logging.ERROR)  # 记录文件不存在日志
            except Exception as e:  # 捕获解压异常
                handle_exception(e)
                log(f"解压文件失败: {e}", logging.ERROR)  # 记录解压失败日志
                return False  # 返回 False 表示解压失败
        
            log(i18nText("所有文件下载和解压完成"))  # 记录所有文件下载和解压完成日志
            return True  # 返回 True 表示成功
        def download_file_with_retry(self, file_name, target_dir, progress_key):
            """下载文件并支持重试"""
            # 构造下载 URL
            url = f"{self.LM_Download_Way_version.get(LM_download_way_choose)}{file_name}"
            log(f"下载链接:{url}")
            # 构造文件保存路径
            file_path = os.path.join(target_dir, file_name)
            # 设置最大重试次数
            max_retries = 5
            # 设置每次重试之间的延迟时间（秒）
            retry_delay = 3
        
            # 循环尝试下载文件，最多重试 max_retries 次
            for attempt in range(max_retries):
                try:
                    # 记录日志，显示当前尝试次数
                    log(f"开始下载 {file_name} (尝试 {attempt + 1}/{max_retries})")
                    # 发起 HTTP GET 请求，启用流式下载，设置超时时间为 10 秒
                    response = requests.get(url, stream=True, timeout=10)
                    # 检查 HTTP 响应状态码，如果不是 200 则抛出异常
                    response.raise_for_status()
        
                    # 获取文件总大小（字节）
                    total_size = int(response.headers.get('content-length', 0))
                    # 初始化已下载大小为 0
                    downloaded_size = 0
        
                    # 显示通知，初始化进度条
                    notify(progress={
                        'title': f'下载资源文件 {file_name}',
                        'status': i18nText('正在下载... ↓'),
                        'value': '0',
                        'valueStringOverride': '0%',
                        'icon': os.path.join(os.getcwd(), 'bloret.ico')  # 确保路径有效
                    })
        
                    # 打开文件并写入下载内容
                    with open(file_path, 'wb') as f:
                        # 分块下载文件，每次读取 8192 字节
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # 确保 chunk 不为空
                                f.write(chunk)  # 写入文件
                                downloaded_size += len(chunk)  # 更新已下载大小
                                # 计算下载进度百分比
                                progress = int(downloaded_size / total_size * 100)
                                # 发送进度信号，更新 UI
                                self.progress_signal.emit(progress_key, progress, f"下载进度: {progress}%")
                                # 更新通知的进度条
                                update_progress({'value': progress / 100, 'valueStringOverride': f'{progress}%'})
        
                    # 记录日志，显示文件下载完成
                    log(f"文件 {file_name} 下载完成")
        
                    # 更新通知状态为下载完成
                    update_progress({
                        'status': i18nText('下载完成！✅'),
                        'value': 100,
                        'valueStringOverride': f'100%'
                    })
        
                    # 每个文件下载完成后间隔 3 秒
                    time.sleep(3)
                    return True  # 下载成功，返回 True
                except requests.RequestException as e:
                    # 捕获请求异常，记录日志并等待一段时间后重试
                    log(f"下载 {file_name} 失败 (尝试 {attempt + 1}/{max_retries}): {e}", logging.ERROR)
                    time.sleep(retry_delay)
                except Exception as e:
                    handle_exception(e)
                    # 捕获其他异常，记录日志并等待一段时间后重试
                    log(f"下载 {file_name} 时发生未知错误: {e}", logging.ERROR)
                    time.sleep(retry_delay)
                finally:
                    # 确保 response 被正确关闭
                    if 'response' in locals():
                        response.close()
        
            # 如果达到最大重试次数仍未成功，记录日志并返回 False
            log(f"下载 {file_name} 失败，已达到最大重试次数", logging.ERROR)
            return False
    
    # 创建对话框
    download_dialog = BLDownloadDialog(version, parent)

    # 创建下载线程
    minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
    thread = VersionDownloadThread(version, minecraft_dir)
    thread.finished.connect(lambda t=thread: self.threads.remove(t) if t in self.threads else None)
    self.threads.append(thread)

    # 连接信号与槽
    thread.progress_signal.connect(
        lambda key, value, message: download_dialog.update_progress(key, value, message)
    )
    thread.error_signal.connect(
        lambda e: (
            log(f"下载失败: {e}", logging.ERROR),
            Dialog(i18nText("下载失败"), f"下载过程中发生错误: {e}").exec()
        )
    )

    def download_finished():
        log(f"下载完成: 版本 {version}")
        # QTimer.singleShot(0, lambda: send_system_notification("下载完成", f"版本 {version} 已成功下载"))

        # 断开信号
        thread.progress_signal.disconnect()
        thread.error_signal.disconnect()
        thread.finished_signal.disconnect()

        # 确保线程退出
        if thread.isRunning():
            thread.quit()
            thread.wait(2000)  # 等待线程完全退出

        # 关闭对话框
        QTimer.singleShot(0, download_dialog.close)
        QTimer.singleShot(0, download_dialog.deleteLater)
        QTimer.singleShot(0, thread.deleteLater)

        # 清理线程列表
        if thread in self.threads:
            self.threads.remove(thread)

        log(i18nText("下载完成处理结束"))

    thread.finished_signal.connect(download_finished)

    # 启动线程
    thread.start()

    # 显示对话框
    download_dialog.exec()

    return 0

