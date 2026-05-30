import os
from pathlib import Path

try:
    from dulwich import porcelain
    from dulwich.repo import Repo
    HAS_DULWICH = True
except ImportError:
    HAS_DULWICH = False


class ResourcePackGit:
    def __init__(self, repo_path):
        if not HAS_DULWICH:
            raise ImportError("dulwich is required for git operations. Install it with: pip install dulwich")
        self.repo_path = Path(repo_path)
        self._repo = None

    def init_if_needed(self):
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self._repo = Repo.init(str(self.repo_path))
            gitignore_path = self.repo_path / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text(
                    ".DS_Store\nThumbs.db\n*.log\ntemp/\n__pycache__/\n"
                )
            porcelain.add(self._repo, paths=[".gitignore"])
            porcelain.commit(
                self._repo,
                message="Initial commit: Bloret Resource Pack Editor",
            )
            return True
        self._repo = Repo(str(self.repo_path))
        return False

    def get_status(self):
        if self._repo is None:
            self.init_if_needed()
        status = porcelain.status(self._repo)
        result = {}
        for f in status.staged.get("add", []):
            result[f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f] = "A"
        for f in status.staged.get("modify", []):
            result[f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f] = "M"
        for f in status.staged.get("delete", []):
            result[f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f] = "D"
        for f in status.unstaged:
            path = f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f
            existing = result.get(path, "")
            if existing == "A":
                result[path] = "M"
            else:
                result[path] = "M"
        for f in status.untracked:
            result[f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f] = "U"
        return result

    def get_file_status(self, file_path):
        statuses = self.get_status()
        return statuses.get(file_path, "")

    def stage_file(self, file_path):
        if self._repo is None:
            self.init_if_needed()
        porcelain.add(self._repo, paths=[file_path])
        return True

    def unstage_file(self, file_path):
        if self._repo is None:
            self.init_if_needed()
        try:
            porcelain.unstage_file(self._repo, file_path)
        except Exception:
            pass
        return True

    def commit(self, message):
        if self._repo is None:
            self.init_if_needed()
        porcelain.commit(self._repo, message=message)
        return True

    def get_commit_count(self):
        if self._repo is None:
            return 0
        try:
            count = 0
            for _ in self._repo.get_walker(self._repo.head()):
                count += 1
            return count
        except Exception:
            return 0

    def get_log(self, max_count=50):
        if self._repo is None:
            return []
        try:
            commits = []
            for i, entry in enumerate(self._repo.get_walker(self._repo.head())):
                if i >= max_count:
                    break
                commit = entry.commit
                commits.append({
                    "id": commit.id.decode("ascii"),
                    "author": commit.author.decode("utf-8", errors="replace"),
                    "message": commit.message.decode("utf-8", errors="replace").strip(),
                    "timestamp": commit.commit_time,
                })
            return commits
        except Exception:
            return []

    def stage_all(self):
        if self._repo is None:
            self.init_if_needed()
        try:
            status = porcelain.status(self._repo)
            all_files = []
            for f in status.unstaged:
                all_files.append(f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f)
            for f in status.untracked:
                all_files.append(f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f)
            if all_files:
                porcelain.add(self._repo, paths=all_files)
            return True
        except Exception:
            return False

    def unstage_all(self):
        if self._repo is None:
            self.init_if_needed()
        try:
            porcelain.reset(self._repo, mode="soft", treeish=None)
            return True
        except Exception:
            return False

    def get_diff(self, file_path=None):
        if self._repo is None:
            return ""
        try:
            if file_path:
                full_path = self.repo_path / file_path
                if full_path.exists():
                    with open(str(full_path), "rb") as f:
                        current = f.read()
                    try:
                        blob = self._repo.object_store[porcelain.index_entry_blob(self._repo, file_path)]
                        original = blob.data
                    except Exception:
                        original = b""
                    diff_lines = []
                    import difflib
                    a = original.decode("utf-8", errors="replace").splitlines(keepends=True)
                    b = current.decode("utf-8", errors="replace").splitlines(keepends=True)
                    for line in difflib.unified_diff(a, b, fromfile=f"a/{file_path}", tofile=f"b/{file_path}"):
                        diff_lines.append(line.rstrip("\n"))
                    return "\n".join(diff_lines)
            else:
                return ""
        except Exception:
            return ""

    def get_staged_files(self):
        if self._repo is None:
            return []
        try:
            status = porcelain.status(self._repo)
            files = []
            for op, paths in status.staged.items():
                for f in paths:
                    files.append({
                        "path": f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f,
                        "operation": op,
                    })
            return files
        except Exception:
            return []

    def get_unstaged_files(self):
        if self._repo is None:
            return []
        try:
            status = porcelain.status(self._repo)
            files = []
            for f in status.unstaged:
                files.append(f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f)
            for f in status.untracked:
                files.append(f.decode("utf-8", errors="replace") if isinstance(f, bytes) else f)
            return files
        except Exception:
            return []
