import os
import sys
import json
import logging
import subprocess
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot, Property

from .git_handler import ResourcePackGit
from .pack_analyzer import PackAnalyzer

log = logging.getLogger(__name__)

# 数据存储路径
try:
    from modules.globals import datapath as _datapath
except ImportError:
    _datapath = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Bloret-Launcher')


class ResourcePackEditorBackend(QObject):
    packLoaded = Signal(dict)
    fileTreeChanged = Signal(list)
    gitStatusChanged = Signal(str)
    statusMessage = Signal(str, str)
    errorOccurred = Signal(str)
    packMissingStructure = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pack_path = None
        self._git = None
        self._analyzer = None
        self._recent_packs_path = os.path.join(_datapath, 'recent_resource_packs.json')

    # ========== 最近打开的资源包 ==========

    def _record_recent_pack(self, path):
        """记录最近打开的资源包路径"""
        try:
            recent = self._load_recent_packs()
            path_str = str(path)
            # 移除同路径旧记录
            recent = [r for r in recent if r.get("path") != path_str]
            # 插入到最前面
            recent.insert(0, {
                "path": path_str,
                "name": Path(path_str).name,
                "lastOpen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            # 最多保留 15 条
            recent = recent[:15]
            os.makedirs(os.path.dirname(self._recent_packs_path), exist_ok=True)
            with open(self._recent_packs_path, 'w', encoding='utf-8') as f:
                json.dump(recent, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录最近资源包失败: {e}")

    def _load_recent_packs(self):
        """加载最近打开的资源包列表"""
        try:
            if os.path.exists(self._recent_packs_path):
                with open(self._recent_packs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"读取最近资源包失败: {e}")
        return []

    @Slot(result=list)
    def getRecentPacks(self):
        """获取最近打开的资源包列表，返回有效路径的列表"""
        recent = self._load_recent_packs()
        # 只返回仍然存在的路径
        valid = []
        for item in recent:
            p = Path(item["path"])
            if p.exists():
                valid.append({
                    "path": item["path"],
                    "name": item.get("name", p.name),
                    "lastOpen": item.get("lastOpen", "")
                })
        return valid

    @Slot(str, result=str)
    def extractZipToSameDir(self, zipPath):
        """将压缩包解压到同目录下的同名文件夹，返回解压后的路径"""
        zip_path = Path(zipPath)
        if not zip_path.exists():
            self.errorOccurred.emit(f"压缩包不存在: {zipPath}")
            return ""
        if zip_path.suffix.lower() != ".zip":
            self.errorOccurred.emit("请选择 .zip 格式的压缩包")
            return ""
        extract_dir = zip_path.parent / zip_path.stem
        try:
            with zipfile.ZipFile(str(zip_path), "r") as zf:
                zf.extractall(str(extract_dir))
            return str(extract_dir)
        except Exception as e:
            self.errorOccurred.emit(f"解压失败: {e}")
            return ""

    # ========== 基本属性 ==========

    @Slot(result=str)
    def getPackPath(self):
        return self._pack_path if self._pack_path else ""

    @Slot(result=bool)
    def isPackOpen(self):
        return self._pack_path is not None

    def open_pack(self, path):
        path = Path(path)
        if not path.exists():
            self.errorOccurred.emit(f"路径不存在: {path}")
            return False

        if path.suffix.lower() == ".zip":
            extract_dir = path.parent / path.stem
            try:
                with zipfile.ZipFile(str(path), "r") as zf:
                    zf.extractall(str(extract_dir))
                self._pack_path = extract_dir
            except Exception as e:
                self.errorOccurred.emit(f"解压失败: {e}")
                return False
        elif path.is_dir():
            self._pack_path = path
        else:
            self.errorOccurred.emit("请选择 zip 文件或文件夹")
            return False

        if not (self._pack_path / "pack.mcmeta").exists():
            self.packMissingStructure.emit(str(self._pack_path))
            self._pack_path = None
            return False

        try:
            self._git = ResourcePackGit(str(self._pack_path))
            self._git.init_if_needed()
        except ImportError:
            self._git = None
        self._analyzer = PackAnalyzer(self._pack_path)
        if not self._analyzer.is_valid_pack():
            self.errorOccurred.emit("该目录不是有效的资源包（缺少 pack.mcmeta）")
            self._pack_path = None
            self._git = None
            self._analyzer = None
            return False
        # 创建 .BLRPE 项目配置目录
        blrpe_dir = self._pack_path / ".BLRPE"
        blrpe_dir.mkdir(exist_ok=True)

        self._record_recent_pack(self._pack_path)
        self._refresh()
        return True

    @Slot(str, result=bool)
    def openPack(self, path):
        return self.open_pack(path)

    @Slot(str, result=bool)
    def createBasicStructure(self, path):
        path = Path(path)
        try:
            assets_dir = path / "assets" / "minecraft"
            assets_dir.mkdir(parents=True, exist_ok=True)
            (assets_dir / "lang").mkdir(exist_ok=True)
            (assets_dir / "textures").mkdir(exist_ok=True)
            (assets_dir / "models").mkdir(exist_ok=True)
            mcmeta = {
                "pack": {
                    "pack_format": 42,
                    "description": "My Resource Pack"
                }
            }
            (path / "pack.mcmeta").write_text(
                json.dumps(mcmeta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            (assets_dir / "lang" / "en_us.json").write_text(
                json.dumps({"pack.name": "My Resource Pack", "pack.description": ""}, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            self.errorOccurred.emit(f"创建资源包结构失败: {e}")
            return False
        return self.open_pack(str(path))

    def _refresh(self):
        if self._analyzer is None:
            return
        try:
            git_statuses = self._git.get_status() if self._git else {}
        except Exception:
            git_statuses = {}
        file_tree = self._analyzer.get_file_tree(git_statuses)
        mcmeta = self._analyzer.read_mcmeta()
        stats = self._analyzer.get_stats()
        self.packLoaded.emit(
            {
                "path": str(self._pack_path),
                "mcmeta": json.dumps(mcmeta, ensure_ascii=False),
                "stats": json.dumps(stats),
            }
        )
        self.fileTreeChanged.emit(file_tree)
        self.statusMessage.emit("ready", f"已加载资源包: {self._pack_path.name}")

    @Slot(result=list)
    def getFileTree(self):
        if self._analyzer is None:
            return []
        try:
            git_statuses = self._git.get_status() if self._git else {}
        except Exception:
            git_statuses = {}
        return self._analyzer.get_file_tree(git_statuses)

    @Slot(str, result=str)
    def getFileContent(self, filePath):
        if self._pack_path is None:
            return ""
        full_path = self._pack_path / filePath
        if not full_path.exists():
            return ""
        try:
            return full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return full_path.read_text(encoding="utf-8-sig")
            except Exception:
                return ""
        except Exception:
            return ""

    @Slot(str, str, result=bool)
    def saveFile(self, filePath, content):
        if self._pack_path is None:
            return False
        full_path = self._pack_path / filePath
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            self.statusMessage.emit("saved", f"已保存: {filePath}")
            return True
        except Exception as e:
            self.errorOccurred.emit(f"保存失败: {e}")
            return False

    @Slot(result=str)
    def getMcmeta(self):
        if self._analyzer is None:
            return "{}"
        return json.dumps(self._analyzer.read_mcmeta(), indent=2, ensure_ascii=False)

    @Slot(str, result=bool)
    def saveMcmeta(self, jsonStr):
        if self._analyzer is None:
            return False
        try:
            data = json.loads(jsonStr)
            ok = self._analyzer.save_mcmeta(data)
            if ok:
                self.statusMessage.emit("saved", "pack.mcmeta 已保存")
                self._refresh()
            return ok
        except json.JSONDecodeError as e:
            self.errorOccurred.emit(f"JSON 格式错误: {e}")
            return False

    @Slot(result=list)
    def getLanguages(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_languages()

    @Slot(str, result=str)
    def getLanguageData(self, langPath):
        if self._analyzer is None:
            return "{}"
        data = self._analyzer.read_language_file(langPath)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @Slot(str, str, result=bool)
    def saveLanguageData(self, langPath, jsonStr):
        if self._analyzer is None:
            return False
        try:
            data = json.loads(jsonStr)
            ok = self._analyzer.save_language_file(langPath, data)
            if ok:
                self.statusMessage.emit("saved", f"语言文件已保存: {langPath}")
            return ok
        except json.JSONDecodeError as e:
            self.errorOccurred.emit(f"JSON 格式错误: {e}")
            return False

    @Slot(result=list)
    def getTextures(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_textures()

    @Slot(result=str)
    def getGitStatus(self):
        if self._git is None:
            return "{}"
        try:
            return json.dumps(self._git.get_status())
        except Exception:
            return "{}"

    @Slot(str, result=bool)
    def stageFile(self, filePath):
        if self._git is None:
            return False
        try:
            self._git.stage_file(filePath)
            self.statusMessage.emit("staged", f"已暂存: {filePath}")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"暂存失败: {e}")
            return False

    @Slot(str, result=bool)
    def unstageFile(self, filePath):
        if self._git is None:
            return False
        try:
            self._git.unstage_file(filePath)
            self.statusMessage.emit("unstage", f"已取消暂存: {filePath}")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"取消暂存失败: {e}")
            return False

    @Slot(str, result=bool)
    def commit(self, message):
        if self._git is None:
            return False
        try:
            self._git.commit(message)
            self.statusMessage.emit("committed", f"已提交: {message}")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"提交失败: {e}")
            return False

    @Slot(result=int)
    def getCommitCount(self):
        if self._git is None:
            return 0
        return self._git.get_commit_count()

    @Slot(result=str)
    def getStats(self):
        if self._analyzer is None:
            return "{}"
        return json.dumps(self._analyzer.get_stats())

    @Slot(str, result=str)
    def getDiff(self, filePath):
        if self._git is None:
            return ""
        return self._git.get_diff(filePath) or ""

    @Slot(result=str)
    def getStagedFiles(self):
        if self._git is None:
            return "[]"
        return json.dumps(self._git.get_staged_files(), ensure_ascii=False)

    @Slot(result=str)
    def getUnstagedFiles(self):
        if self._git is None:
            return "[]"
        return json.dumps(self._git.get_unstaged_files(), ensure_ascii=False)

    @Slot(int, result=str)
    def getCommitLog(self, maxCount):
        if self._git is None:
            return "[]"
        return json.dumps(self._git.get_log(int(maxCount)), ensure_ascii=False)

    @Slot(result=bool)
    def stageAll(self):
        if self._git is None:
            return False
        try:
            self._git.stage_all()
            self.statusMessage.emit("staged", "已暂存所有更改")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"暂存失败: {e}")
            return False

    @Slot(result=bool)
    def unstageAll(self):
        if self._git is None:
            return False
        try:
            self._git.unstage_all()
            self.statusMessage.emit("unstage", "已取消所有暂存")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"取消暂存失败: {e}")
            return False

    @Slot(str, str, result=bool)
    def stagePath(self, path, mode):
        if self._git is None:
            return False
        try:
            if mode == "stage":
                self._git.stage_file(path)
            elif mode == "unstage":
                self._git.unstage_file(path)
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"操作失败: {e}")
            return False

    @Slot(str, result=bool)
    def deleteFile(self, filePath):
        if self._pack_path is None:
            return False
        full_path = self._pack_path / filePath
        try:
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(str(full_path))
            self.statusMessage.emit("deleted", f"已删除: {filePath}")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"删除失败: {e}")
            return False

    @Slot(str, str, result=bool)
    def createFile(self, parentPath, fileName):
        if self._pack_path is None:
            return False
        try:
            full_dir = self._pack_path / parentPath if parentPath else self._pack_path
            full_dir.mkdir(parents=True, exist_ok=True)
            full_path = full_dir / fileName
            full_path.touch()
            self.statusMessage.emit("created", f"已创建: {fileName}")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"创建失败: {e}")
            return False

    @Slot(str, str, result=bool)
    def renameFile(self, oldPath, newName):
        if self._pack_path is None:
            return False
        try:
            old_full = self._pack_path / oldPath
            new_full = old_full.parent / newName
            old_full.rename(new_full)
            self.statusMessage.emit("renamed", f"已重命名: {oldPath} → {newName}")
            self._refresh()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"重命名失败: {e}")
            return False

    # ========== 快捷操作 ==========

    @Slot(result=str)
    def exportAsZip(self) -> str:
        """导出资源包为 ZIP 压缩包，返回保存路径"""
        if self._pack_path is None:
            return ""
        try:
            zip_name = f"{self._pack_path.name}.zip"
            zip_path = self._pack_path.parent / zip_name
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in self._pack_path.rglob("*"):
                    if file.is_file():
                        arcname = str(file.relative_to(self._pack_path))
                        zf.write(str(file), arcname)
            self.statusMessage.emit("exported", f"已导出: {zip_path}")
            return str(zip_path)
        except Exception as e:
            self.errorOccurred.emit(f"导出失败: {e}")
            return ""

    @Slot()
    def showInExplorer(self):
        """在文件资源管理器/访达中显示"""
        if self._pack_path is None:
            return
        path = str(self._pack_path)
        try:
            if sys.platform == "win32":
                # explorer /select, 需要文件路径，对目录使用 explorer 直接打开
                if self._pack_path.is_dir():
                    subprocess.Popen(["explorer", path])
                else:
                    subprocess.Popen(["explorer", "/select,", path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.errorOccurred.emit(f"打开失败: {e}")

    @Slot()
    def openInVSCode(self):
        """在 Visual Studio Code 中打开"""
        if self._pack_path is None:
            log.warning("openInVSCode: _pack_path is None")
            return
        path = str(self._pack_path)
        log.info(f"openInVSCode: 尝试打开 {path}")
        try:
            # 尝试多种方式启动 VS Code
            for cmd in [["code", path], ["code.cmd", path], ["code-insiders", path]]:
                try:
                    log.info(f"openInVSCode: 尝试命令 {cmd[0]}")
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = proc.communicate(timeout=5)
                    if proc.returncode == 0:
                        log.info(f"openInVSCode: 成功")
                        return
                    else:
                        log.warning(f"openInVSCode: {cmd[0]} 返回 {proc.returncode}, stderr={stderr.decode('utf-8', errors='replace')}")
                except FileNotFoundError:
                    log.warning(f"openInVSCode: 命令 {cmd[0]} 未找到")
                    continue
                except subprocess.TimeoutExpired:
                    # 超时说明进程已启动（VS Code 是 GUI 程序，不会立即退出）
                    log.info(f"openInVSCode: {cmd[0]} 已启动（超时正常）")
                    proc.kill()
                    return
                except Exception as e:
                    log.warning(f"openInVSCode: {cmd[0]} 异常: {e}")
                    continue
            # 所有命令都失败，尝试用 os.startfile
            log.info("openInVSCode: 尝试 os.startfile")
            if sys.platform == "win32":
                os.startfile(path)
            else:
                self.errorOccurred.emit("未找到 VS Code，请确认已安装并添加到 PATH")
        except Exception as e:
            log.error(f"openInVSCode 失败: {e}")
            self.errorOccurred.emit(f"打开 VS Code 失败: {e}")

    @Slot()
    def openInTerminal(self):
        """在终端中打开"""
        if self._pack_path is None:
            return
        path = str(self._pack_path)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", f"cd /d {path}"])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Terminal", path])
            else:
                subprocess.Popen(["xdg-terminal", "--working-directory", path])
        except Exception as e:
            self.errorOccurred.emit(f"打开终端失败: {e}")

    @Slot(result=str)
    def getExplorerLabel(self) -> str:
        """获取系统对应的文件管理器名称"""
        if sys.platform == "win32":
            return "文件资源管理器"
        elif sys.platform == "darwin":
            return "访达"
        else:
            return "文件管理器"

    @Slot(result=list)
    def getBlockstates(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_blockstates()

    @Slot(result=list)
    def getModels(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_models()

    @Slot(result=list)
    def getSoundsJson(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_sounds_json()

    @Slot(result=list)
    def getSoundFiles(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_sound_files()

    @Slot(result=list)
    def getFonts(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_fonts()

    @Slot(result=list)
    def getTexts(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_texts()

    @Slot(result=list)
    def getParticles(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_particles()

    @Slot(result=list)
    def getOptifineCem(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_optifine_cem()

    @Slot(result=list)
    def getOptifineCit(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_optifine_cit()

    @Slot(result=list)
    def getSpecialFiles(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_special_files()

    @Slot(result=list)
    def getNamespaces(self):
        if self._analyzer is None:
            return []
        return self._analyzer.get_namespaces()

    @Slot(result=str)
    def getPackPngPath(self):
        if self._pack_path is None:
            return ""
        p = self._pack_path / "pack.png"
        if p.exists():
            return p.as_uri()
        return ""

    @Slot(str, result=str)
    def readRawFile(self, relPath):
        if self._pack_path is None:
            return ""
        full = self._pack_path / relPath
        if not full.exists():
            return ""
        try:
            return full.read_text(encoding="utf-8")
        except Exception:
            return ""

    @Slot(str, str, result=bool)
    def saveRawFile(self, relPath, content):
        if self._pack_path is None:
            return False
        full = self._pack_path / relPath
        try:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
            self.statusMessage.emit("saved", f"已保存: {relPath}")
            return True
        except Exception as e:
            self.errorOccurred.emit(f"保存失败: {e}")
            return False
