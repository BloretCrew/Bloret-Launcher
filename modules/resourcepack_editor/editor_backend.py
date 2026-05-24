import os
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, Property

from .git_handler import ResourcePackGit
from .pack_analyzer import PackAnalyzer


class ResourcePackEditorBackend(QObject):
    packLoaded = Signal(dict)
    fileTreeChanged = Signal(list)
    gitStatusChanged = Signal(str)
    statusMessage = Signal(str, str)
    errorOccurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pack_path = None
        self._git = None
        self._analyzer = None

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
        self._git = ResourcePackGit(str(self._pack_path))
        self._git.init_if_needed()
        self._analyzer = PackAnalyzer(self._pack_path)
        if not self._analyzer.is_valid_pack():
            self.errorOccurred.emit("该目录不是有效的资源包（缺少 pack.mcmeta）")
            return False
        self._refresh()
        return True

    @Slot(str, result=bool)
    def openPack(self, path):
        return self.open_pack(path)

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
